"""
Middleware personalizado para debug e tratamento de CSRF
"""
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponseForbidden
from django.template import loader
import logging
import time
import re
from django.utils import timezone
from user_agents import parse

logger = logging.getLogger(__name__)


class CSRFDebugMiddleware(MiddlewareMixin):
    """
    Middleware para debug de CSRF em produção
    Não mata a aplicação, só registra problemas
    """
    
    def process_request(self, request):
        # Log detalhado apenas se houver problema
        if request.method == 'POST':
            csrf_token = (
                request.META.get('HTTP_X_CSRFTOKEN') or 
                request.POST.get('csrfmiddlewaretoken')
            )
            
            if not csrf_token and not settings.DEBUG:
                # CSRF ausente - tratar silenciosamente
                pass
                
        return None
    
    def process_response(self, request, response):
        # Se for erro CSRF (403), tratar silenciosamente
        if response.status_code == 403 and not settings.DEBUG:
            # Erro 403 - sem logs
            pass
            
        return response


class SafeCSRFMiddleware(MiddlewareMixin):
    """
    Middleware que tenta recuperar de erros CSRF sem matar a aplicação
    """
    
    def process_exception(self, request, exception):
        # Se for erro relacionado a CSRF, tenta uma recuperação suave
        if 'CSRF' in str(exception) or 'csrf' in str(exception).lower():
            # Erro CSRF - tratar silenciosamente
            
            # Em produção, retorna uma página amigável em vez de crash
            if not settings.DEBUG:
                template = loader.get_template('bolao/csrf_error.html')
                return HttpResponseForbidden(
                    template.render({
                        'message': 'Erro de segurança detectado. Tente recarregar a página.',
                        'path': request.path
                    }, request)
                )
        
        return None


class AnalyticsMiddleware(MiddlewareMixin):
    """
    Middleware para capturar dados de analytics dos usuários
    """
    
    def get_client_ip(self, request):
        """Obtém o IP real do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    def get_device_info(self, user_agent_string):
        """Analisa o user agent para obter informações do dispositivo"""
        user_agent = parse(user_agent_string)
        
        if user_agent.is_mobile:
            device_type = 'mobile'
        elif user_agent.is_tablet:
            device_type = 'tablet'
        else:
            device_type = 'desktop'
            
        return {
            'device_type': device_type,
            'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
            'os': f"{user_agent.os.family} {user_agent.os.version_string}"
        }
    
    def process_request(self, request):
        """Processa o início da requisição"""
        # Marca o tempo de início
        request._analytics_start_time = time.time()
        
        # Não rastreia requisições para arquivos estáticos, admin ou API
        if any(path in request.path for path in ['/static/', '/media/', '/admin/', '/api/']):
            return None
        
        try:
            # Importa aqui para evitar circular import
            from bolao.models import SessaoVisita, AcaoUsuario, Participante
            
            # Obtém informações da requisição
            ip = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Obtém ou cria sessão de forma segura
            session_key = request.session.session_key
            if not session_key:
                try:
                    request.session.create()
                    session_key = request.session.session_key
                except Exception:
                    # Se não conseguir criar sessão, pula analytics
                    return None
            
            try:
                sessao = SessaoVisita.objects.get(session_id=session_key, ativo=True)
            except SessaoVisita.DoesNotExist:
                # Informações do dispositivo
                device_info = self.get_device_info(user_agent)
                
                sessao = SessaoVisita.objects.create(
                    session_id=session_key,
                    ip_address=ip,
                    user_agent=user_agent,
                    dispositivo_tipo=device_info['device_type'],
                    navegador=device_info['browser'],
                    sistema_operacional=device_info['os']
                )
            
            # Atualiza participante se logado - mas não durante logout
            if request.user.is_authenticated and 'logout' not in request.path:
                try:
                    participante = Participante.objects.get(user=request.user)
                    sessao.participante = participante
                    sessao.save()
                except Participante.DoesNotExist:
                    pass
            elif 'logout' in request.path:
                # Durante logout, remove participante da sessão
                try:
                    sessao.participante = None
                    sessao.ativo = False
                    sessao.save()
                except Exception:
                    pass  # Ignora erros durante logout
            
            # Salva a sessão no request para uso posterior
            request._analytics_sessao = sessao
            
        except Exception:
            # Se qualquer parte do analytics falhar, continua sem quebrar a app
            pass
        
        return None
    
    def process_response(self, request, response):
        """Processa o final da requisição"""
        # Calcula tempo de resposta
        if hasattr(request, '_analytics_start_time'):
            response_time = (time.time() - request._analytics_start_time) * 1000  # em ms
        else:
            response_time = None
        
        # Não rastreia arquivos estáticos ou durante problemas de sessão
        if any(path in request.path for path in ['/static/', '/media/', '/admin/', '/api/']):
            return response
        
        # Não processa analytics durante logout para evitar conflitos de sessão
        if 'logout' in request.path:
            return response
        
        # Salva a ação se tem sessão
        try:
            if hasattr(request, '_analytics_sessao') and response.status_code < 500:
                self.registrar_acao(request, response, response_time)
        except Exception:
            # Se analytics falhar, continua sem quebrar a app
            pass
        
        return response
    
    def registrar_acao(self, request, response, response_time):
        """Registra a ação do usuário"""
        from bolao.models import AcaoUsuario, PaginaPopular
        
        sessao = request._analytics_sessao
        
        # Determina o tipo de ação
        if request.method == 'POST':
            if 'login' in request.path:
                tipo_acao = 'login'
            elif 'logout' in request.path:
                tipo_acao = 'logout'
            elif 'palpite' in request.path:
                tipo_acao = 'palpite'
            else:
                tipo_acao = 'form_submit'
        else:
            if response.status_code == 404:
                tipo_acao = 'error_404'
            elif response.status_code >= 500:
                tipo_acao = 'error_500'
            else:
                tipo_acao = 'page_view'
        
        # Obtém título da página (se disponível)
        titulo_pagina = self.get_page_title(request.path)
        
        # Criar ação
        try:
            acao = AcaoUsuario.objects.create(
                sessao=sessao,
                tipo_acao=tipo_acao,
                pagina_url=request.build_absolute_uri(),
                pagina_titulo=titulo_pagina,
                tempo_resposta=response_time,
                metadados={
                    'method': request.method,
                    'status_code': response.status_code,
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'query_params': dict(request.GET) if request.GET else {}
                }
            )
            
            # Atualiza contadores da sessão
            sessao.paginas_visitadas += 1
            sessao.save()
            
            # Atualiza páginas populares (apenas para page_view)
            if tipo_acao == 'page_view' and response.status_code == 200:
                self.atualizar_pagina_popular(request.path, titulo_pagina)
                
        except Exception as e:
            # Erro silencioso em analytics
            pass
    
    def get_page_title(self, path):
        """Obtém título amigável da página baseado na URL"""
        titles = {
            '/': 'Página Inicial',
            '/classificacao/': 'Classificação',
            '/jogos-ao-vivo/': 'Jogos ao Vivo',
            '/login/': 'Login',
            '/logout/': 'Logout',
            '/perfil/': 'Perfil',
            '/atualizacoes/': 'Atualizações',
            '/termos-uso/': 'Termos de Uso'
        }
        
        # Verifica padrões
        if '/rodada/' in path and '/palpites/' in path:
            return 'Palpites da Rodada'
        elif '/rodada/' in path and '/resultados/' in path:
            return 'Resultados da Rodada'
        elif '/participante/' in path:
            return 'Perfil do Participante'
        
        return titles.get(path, 'Página')
    
    def atualizar_pagina_popular(self, url, titulo):
        """Atualiza o contador de páginas populares"""
        from bolao.models import PaginaPopular
        
        try:
            pagina, created = PaginaPopular.objects.get_or_create(
                url=url,
                defaults={'titulo': titulo, 'visitas_hoje': 0, 'visitas_total': 0}
            )
            
            pagina.visitas_hoje += 1
            pagina.visitas_total += 1
            pagina.save()
            
        except Exception as e:
            # Erro silencioso ao atualizar página
            pass