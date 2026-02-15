from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, F
from django.conf import settings
import os
import json
from .models import Rodada, Jogo, Palpite, Participante, Classificacao, Time, NotificationSettings, Notification
from .forms import PerfilParticipanteForm


def home(request):
    """Página inicial mostrando rodadas e status"""
    
    # Busca rodadas ativas com consulta otimizada
    rodadas_ativas = Rodada.objects.filter(ativa=True).select_related().order_by('numero')
    
    # Rodada atual: otimizada
    agora = timezone.now()
    rodada_atual = None
    
    # Busca mais eficiente
    rodadas_list = list(rodadas_ativas)
    
    # Primeiro tenta pegar uma rodada ativa no período correto
    for rodada in rodadas_list:
        if rodada.data_inicio <= agora <= rodada.data_fim:
            rodada_atual = rodada
            break
    
    # Se não achou, pega a próxima ou a última
    if not rodada_atual:
        futuras = [r for r in rodadas_list if r.data_inicio > agora]
        rodada_atual = futuras[0] if futuras else (rodadas_list[-1] if rodadas_list else None)
    
    # Filtra rodadas usando listas já carregadas
    rodadas_futuras = [r for r in rodadas_list if r.data_inicio > agora and r != rodada_atual][:3]
    rodadas_passadas = sorted([r for r in rodadas_list if r.data_fim < agora], key=lambda x: x.numero, reverse=True)[:3]
    
    # Participante e atualizações
    participante = None
    atualizacao_nao_vista = None
    
    # Verificação simples e direta
    if request.user.is_authenticated:
        try:
            # Busca explícita do participante
            from .models import Participante
            participante = Participante.objects.get(user=request.user)
            
            # Busca atualizações simples
            from .models import AtualizacaoSite, AtualizacaoVista
            atualizacoes_vistas_ids = list(AtualizacaoVista.objects.filter(participante=participante).values_list('atualizacao_id', flat=True))
            atualizacao_nao_vista = AtualizacaoSite.objects.filter(ativa=True).exclude(id__in=atualizacoes_vistas_ids).first()
                
        except Participante.DoesNotExist:
            # Usuário autenticado mas sem participante (ex: admin)
            participante = None
        except Exception as e:
            participante = None
            import logging
            logging.warning(f'Erro ao buscar participante para user {request.user.username}: {e}')
    
    # Preparar dados para resposta
    context = {
        'rodada_atual': rodada_atual,
        'rodadas_futuras': rodadas_futuras,
        'rodadas_passadas': rodadas_passadas,
        'participante': participante,
        'atualizacao_nao_vista': atualizacao_nao_vista
    }
    
    # Renderiza o template
    response = render(request, 'bolao/home.html', context)
    
    # Headers agressivos para evitar qualquer tipo de cache
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Accel-Expires'] = '0'
    response['Vary'] = 'Cookie'
    response['Last-Modified'] = timezone.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    return response


@login_required
def rodada_palpites(request, rodada_id):
    """Página para fazer palpites ou visualizar palpites da rodada"""
    
    rodada = get_object_or_404(Rodada.objects.select_related(), id=rodada_id)
    
    # Verifica se o usuário tem um participante associado
    try:
        participante = getattr(request.user, 'participante', None)
        if not participante:
            messages.error(request, "Você não está cadastrado como participante do bolão. Entre em contato com o administrador.")
            return redirect('home')
    except Exception:
        messages.error(request, "Erro ao verificar participante. Entre em contato com o administrador.")
        return redirect('home')
    
    # Se não pode mais palpitar, muda para modo visualização
    pode_palpitar = rodada.pode_palpitar
    
    # Consulta otimizada de jogos com times relacionados
    jogos = rodada.jogo_set.select_related('time_casa', 'time_visitante').all().order_by('data_hora')
    
    # Palpites existentes do usuário
    palpites_existentes = {}
    for palpite in Palpite.objects.select_related('jogo').filter(participante=participante, jogo__rodada=rodada):
        palpites_existentes[palpite.jogo.id] = palpite
    
    # Se não pode palpitar, buscar todos os palpites para a planilha
    todos_palpites = {}
    participantes_ativos = []
    if not pode_palpitar:
        participantes_ativos = list(Participante.objects.filter(ativo=True).order_by('nome_exibicao'))
        for jogo in jogos:
            todos_palpites[jogo.id] = {}
            for palpite in Palpite.objects.select_related('participante').filter(jogo=jogo):
                todos_palpites[jogo.id][palpite.participante.id] = palpite
    
    if request.method == 'POST' and pode_palpitar:
        todos_palpites_validos = True
        palpites_salvos = []
        
        for jogo in jogos:
            gols_casa_key = f'gols_casa_{jogo.id}'
            gols_visitante_key = f'gols_visitante_{jogo.id}'
            
            if gols_casa_key in request.POST and gols_visitante_key in request.POST:
                try:
                    gols_casa = int(request.POST[gols_casa_key])
                    gols_visitante = int(request.POST[gols_visitante_key])
                    
                    if gols_casa >= 0 and gols_visitante >= 0 and gols_casa <= 20 and gols_visitante <= 20:
                        palpite, created = Palpite.objects.get_or_create(
                            participante=participante,
                            jogo=jogo,
                            defaults={
                                'gols_casa_palpite': gols_casa,
                                'gols_visitante_palpite': gols_visitante
                            }
                        )
                        
                        if not created:
                            palpite.gols_casa_palpite = gols_casa
                            palpite.gols_visitante_palpite = gols_visitante
                            palpite.save()
                        
                        palpites_salvos.append(palpite)
                except (ValueError, TypeError):
                    continue
        
        if palpites_salvos:
            messages.success(request, f"Palpites salvos com sucesso! {len(palpites_salvos)} jogos.")
            return redirect('home')
        else:
            messages.error(request, "Nenhum palpite foi salvo. Verifique os dados.")
    
    
    context = {
        'rodada': rodada,
        'jogos': list(jogos),
        'participante': participante,
        'palpites_existentes': palpites_existentes,
        'pode_palpitar': pode_palpitar,
        'todos_palpites': todos_palpites,
        'participantes_ativos': participantes_ativos
    }
    
    return render(request, 'bolao/palpites.html', context)


def resultados_rodada(request, rodada_id):
    """Página para ver resultados de uma rodada específica"""
    rodada = get_object_or_404(Rodada, id=rodada_id)
    jogos = rodada.jogo_set.all().order_by('data_hora')
    
    # Se o usuário estiver logado, mostrar seus palpites
    palpites_usuario = {}
    if request.user.is_authenticated:
        try:
            participante = request.user.participante
            for palpite in Palpite.objects.filter(participante=participante, jogo__rodada=rodada):
                palpites_usuario[palpite.jogo.id] = palpite
        except:
            pass
    
    context = {
        'rodada': rodada,
        'jogos': jogos,
        'palpites_usuario': palpites_usuario,
    }
    
    return render(request, 'bolao/resultados.html', context)


def classificacao(request):
    """Página da classificação geral"""
    
    # Consultas otimizadas com select_related
    classificacoes = Classificacao.objects.select_related('participante').all().order_by('posicao')
    
    # Estatísticas gerais
    total_participantes = Participante.objects.filter(ativo=True).count()
    total_jogos_finalizados = Jogo.objects.filter(resultado_finalizado=True).count()
    total_palpites = Palpite.objects.count()
    
    context = {
        'classificacoes': list(classificacoes),
        'total_participantes': total_participantes,
        'total_jogos_finalizados': total_jogos_finalizados,
        'total_palpites': total_palpites
    }
    
    return render(request, 'bolao/classificacao.html', context)


def login_participante(request):
    """Página de login para participantes"""
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Verifica se o usuário tem um participante associado
            try:
                participante = getattr(user, 'participante', None)
                if participante and participante.ativo:
                    auth_login(request, user)
                    
                    messages.success(request, f"Bem-vindo(a), {participante.nome_exibicao}!")
                    # Sempre redireciona para home, ignorando next se for logout
                    next_url = request.GET.get('next', 'home')
                    if 'logout' in str(next_url):
                        next_url = 'home'
                    
                    return redirect(next_url)
                elif participante:
                    messages.error(request, "Sua conta está inativa. Entre em contato com o administrador.")
                else:
                    messages.error(request, "Usuário não é um participante do bolão.")
            except Exception as e:
                import logging
                logging.error(f'Erro no login: {e}')
                messages.error(request, "Erro interno. Tente novamente.")
        else:
            messages.error(request, "Usuário ou senha incorretos.")
    
    return render(request, 'bolao/login.html')


def logout_participante(request):
    """Logout do participante"""
    # Limpa cache específico do usuário se existir
    from django.core.cache import cache
    user_cache_key = f"user_data_{request.user.id}"
    cache.delete(user_cache_key)
    
    # Método mais seguro para logout sem conflitos de sessão
    # Salva dados antes de limpar
    user_to_logout = request.user
    
    # Executa o logout antes de manipular a sessão
    auth_logout(request)
    
    # Agora limpa a sessão de forma segura
    try:
        request.session.clear()
        request.session.cycle_key()  # Gera nova chave de sessão
    except Exception:
        pass  # Ignora erros de sessão durante logout
    
    messages.success(request, "Você foi desconectado com sucesso.")
    
    # Resposta com headers para evitar cache do navegador - sempre redireciona para home
    response = redirect('home')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Accel-Expires'] = '0'
    return response


def perfil_participante(request, participante_id):
    """Página do perfil detalhado de um participante"""
    participante = get_object_or_404(Participante, id=participante_id, ativo=True)
    
    # Buscar estatísticas do participante
    palpites = Palpite.objects.filter(participante=participante, jogo__resultado_finalizado=True)
    
    total_palpites = palpites.count()
    acertos = palpites.filter(
        # Placar exato
        Q(gols_casa_palpite=F('jogo__gols_casa'), gols_visitante_palpite=F('jogo__gols_visitante')) |
        # Acertou o resultado (vitória casa)
        Q(gols_casa_palpite__gt=F('gols_visitante_palpite'), jogo__gols_casa__gt=F('jogo__gols_visitante')) |
        # Acertou o resultado (empate)
        Q(gols_casa_palpite=F('gols_visitante_palpite'), jogo__gols_casa=F('jogo__gols_visitante')) |
        # Acertou o resultado (vitória visitante)
        Q(gols_casa_palpite__lt=F('gols_visitante_palpite'), jogo__gols_casa__lt=F('jogo__gols_visitante'))
    ).count()
    
    # Calcular pontos totais
    pontos_totais = sum(palpite.pontos_obtidos for palpite in palpites)
    
    # Calcular último saldo (pontos da última rodada)
    from .models import Rodada
    ultima_rodada = Rodada.objects.filter(
        jogo__resultado_finalizado=True
    ).order_by('-numero').first()
    
    ultimo_saldo = 0
    if ultima_rodada:
        palpites_ultima_rodada = palpites.filter(jogo__rodada=ultima_rodada)
        ultimo_saldo = sum(palpite.pontos_obtidos for palpite in palpites_ultima_rodada)
    
    # Palpites recentes
    palpites_recentes = palpites.order_by('-data_palpite')[:10]
    
    # Classificação atual
    try:
        classificacao_atual = Classificacao.objects.get(participante=participante)
    except:
        classificacao_atual = None
    
    context = {
        'participante': participante,
        'total_palpites': total_palpites,
        'acertos': acertos,
        'pontos_totais': pontos_totais,
        'ultimo_saldo': ultimo_saldo,
        'palpites_recentes': palpites_recentes,
        'classificacao_atual': classificacao_atual,
        'porcentagem_acerto': round((acertos / total_palpites * 100), 1) if total_palpites > 0 else 0,
    }
    
    return render(request, 'bolao/perfil.html', context)


@login_required
def editar_perfil(request):
    """Página para editar o próprio perfil"""
    try:
        participante = request.user.participante
    except Participante.DoesNotExist:
        messages.error(request, "Você não está cadastrado como participante do bolão.")
        return redirect('home')
    
    if request.method == 'POST':
        form = PerfilParticipanteForm(request.POST, request.FILES, instance=participante)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil_participante', participante_id=participante.id)
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = PerfilParticipanteForm(instance=participante)
    
    context = {
        'form': form,
        'participante': participante
    }
    
    return render(request, 'bolao/editar_perfil.html', context)


def csrf_failure(request, reason=""):
    """
    View personalizada para falhas de CSRF
    Não mata a produção, oferece uma experiência amigável
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log do erro para debug
    logger.warning(f"CSRF Failure: {reason}")
    logger.warning(f"Path: {request.path}")
    logger.warning(f"Method: {request.method}")
    logger.warning(f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    # Contexto para o template
    context = {
        'message': 'Verificação de segurança necessária. Recarregue a página.',
        'reason': reason,
        'path': request.path,
        'can_retry': True,
    }
    
    # Em desenvolvimento, mostra detalhes
    if settings.DEBUG:
        context.update({
            'debug_info': {
                'reason': reason,
                'path': request.path,
                'method': request.method,
                'headers': dict(request.headers),
            }
        })
    
    # Renderiza página amigável em vez de erro brutal
    return render(request, 'bolao/csrf_error.html', context, status=403)


def termos_uso(request):
    """Página com os termos de uso do site"""
    return render(request, 'bolao/termos_uso.html')


def atualizacoes(request):
    """Página com todas as atualizações do site"""
    from .models import AtualizacaoSite
    atualizacoes_list = AtualizacaoSite.objects.filter(ativa=True).order_by('-data_lancamento')
    
    context = {
        'atualizacoes': atualizacoes_list,
    }
    
    return render(request, 'bolao/atualizacoes.html', context)


@login_required
@require_POST
def marcar_atualizacao_vista(request, versao):
    """Marca uma atualização como vista pelo usuário"""
    from django.http import JsonResponse
    from .models import AtualizacaoSite, AtualizacaoVista
    
    try:
        participante = request.user.participante
        atualizacao = get_object_or_404(AtualizacaoSite, versao=versao)
        
        # Cria ou atualiza o registro de visualização
        vista, created = AtualizacaoVista.objects.get_or_create(
            participante=participante,
            atualizacao=atualizacao
        )
        
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'success': False}, status=400)


import requests
import json
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http import JsonResponse


def jogos_ao_vivo(request):
    """Página de jogos ao vivo com placares em tempo real"""
    return render(request, 'bolao/jogos_ao_vivo.html')


def atualizar_placares_api(request):
    """API para atualizar placares do Brasileirão - APENAS BRASILEIRÃO SÉRIE A"""
    from django.core.cache import cache
    import requests
    from datetime import datetime, timedelta
    
    # Cache INTELIGENTE - Só usa cache se não há jogos ao vivo
    CACHE_KEY = 'brasileirao_placares'
    CACHE_BACKUP_KEY = 'brasileirao_placares_backup'
    CACHE_TIMEOUT = 30  # Reduzido para 30 segundos
    CACHE_BACKUP_TIMEOUT = 600  # 10 minutos backup
    
    # Tenta pegar do cache primeiro
    placares_cache = cache.get(CACHE_KEY)
    
    if placares_cache:
        return JsonResponse({
            'success': True,
            'jogos': placares_cache['jogos'],
            'ultima_atualizacao': placares_cache['ultima_atualizacao'],
            'fonte': 'cache',
            'proxima_atualizacao': placares_cache.get('proxima_atualizacao')
        })
    
    try:
        # Configuração da API-Football
        API_URL = "https://v3.football.api-sports.io/fixtures"
        
        headers = {
            'X-RapidAPI-Key': 'b20093f89e13ee92bd30872fba5da1fe',
            'X-RapidAPI-Host': 'v3.football.api-sports.io'
        }
        
        jogos_api = []
        fonte = 'sem_dados'
        
        # 1. BUSCAR JOGOS AO VIVO - APENAS BRASILEIRÃO SÉRIE A (timeout reduzido)
        try:
            params_live = {
                'live': 'all'  # Buscar todos os jogos ao vivo
            }
            response_live = requests.get(API_URL, headers=headers, params=params_live, timeout=3)
            
            if response_live.status_code == 200:
                data_live = response_live.json()
                jogos_live_todos = data_live.get('response', [])
                
                # Filtrar APENAS Brasileirão Série A (Liga ID = 71)
                jogos_live_brasileirao = []
                for jogo in jogos_live_todos:
                    if jogo['league']['id'] == 71:  # APENAS Liga 71
                        jogos_live_brasileirao.append(jogo)
                
                if jogos_live_brasileirao:
                    jogos_api.extend(jogos_live_brasileirao)
                    fonte = 'ao_vivo_brasileirao'
                    
        except Exception as e:
            # Erro silencioso
            pass
        
        # 2. SE NÃO HÁ JOGOS AO VIVO, BUSCAR PRÓXIMOS JOGOS - APENAS BRASILEIRÃO
        if not jogos_api:
            try:
                hoje = datetime.now()
                
                # Buscar próximos 7 dias
                for i in range(8):
                    data = (hoje + timedelta(days=i)).strftime('%Y-%m-%d')
                    
                    # Testar temporadas: 2025, 2026, 2024
                    for temporada in ['2025', '2026', '2024']:
                        try:
                            params = {
                                'league': '71',  # APENAS Brasileirão Série A
                                'season': temporada,
                                'date': data,
                                'timezone': 'America/Sao_Paulo'
                            }
                            
                            response = requests.get(API_URL, headers=headers, params=params, timeout=2)
                            
                            if response.status_code == 200:
                                data_resp = response.json()
                                jogos_data = data_resp.get('response', [])
                                
                                if jogos_data:
                                    jogos_api.extend(jogos_data)
                                    fonte = f'brasileirao_{temporada}_{data}'
                                    break
                                    
                        except Exception as e:
                            continue
                    
                    if jogos_api:  # Se encontrou jogos, para de buscar
                        break
                            
            except Exception as e:
                # Erro silencioso
                pass
        
        # 3. FALLBACK: ÚLTIMOS JOGOS DO BRASILEIRÃO 2024 PARA DEMONSTRAÇÃO
        if not jogos_api:
            try:
                params_recentes = {
                    'league': '71',  # APENAS Brasileirão Série A
                    'season': '2024',
                    'last': 10,
                    'timezone': 'America/Sao_Paulo'
                }
                
                response_recentes = requests.get(API_URL, headers=headers, params=params_recentes, timeout=3)
                
                if response_recentes.status_code == 200:
                    data_recentes = response_recentes.json()
                    jogos_recentes = data_recentes.get('response', [])
                    
                    if jogos_recentes:
                        jogos_api = jogos_recentes[:8]  # Máximo 8 jogos
                        fonte = 'recentes_brasileirao_2024'
                        
            except Exception as e:
                # Erro silencioso
                pass
        
        # 4. SE AINDA NÃO TEM NADA, DADOS SIMULADOS DO BRASILEIRÃO
        if not jogos_api:
            agora = datetime.now()
            jogos_api = [
                {
                    'fixture': {
                        'id': 999991,
                        'date': agora.isoformat(),
                        'status': {'short': '2H', 'long': 'Second Half', 'elapsed': 67},
                        'venue': {'name': 'Maracanã', 'city': 'Rio de Janeiro'}
                    },
                    'teams': {
                        'home': {'name': 'Flamengo', 'logo': 'https://media.api-sports.io/football/teams/18.png'},
                        'away': {'name': 'Palmeiras', 'logo': 'https://media.api-sports.io/football/teams/130.png'}
                    },
                    'goals': {'home': 2, 'away': 1},
                    'league': {'name': 'Brasileirão Série A', 'round': 'Regular Season - 5', 'country': 'Brazil'}
                },
                {
                    'fixture': {
                        'id': 999992,
                        'date': (agora + timedelta(hours=2)).isoformat(),
                        'status': {'short': 'NS', 'long': 'Not Started', 'elapsed': None},
                        'venue': {'name': 'Neo Química Arena', 'city': 'São Paulo'}
                    },
                    'teams': {
                        'home': {'name': 'Corinthians', 'logo': 'https://media.api-sports.io/football/teams/131.png'},
                        'away': {'name': 'São Paulo', 'logo': 'https://media.api-sports.io/football/teams/126.png'}
                    },
                    'goals': {'home': None, 'away': None},
                    'league': {'name': 'Brasileirão Série A', 'round': 'Regular Season - 5', 'country': 'Brazil'}
                }
            ]
            fonte = 'simulados_brasileirao'
        
        # Processa os jogos encontrados - APENAS BRASILEIRÃO SÉRIE A
        jogos_processados = []
        for jogo in jogos_api:
            try:
                # Filtro adicional: apenas Liga 71 (Brasileirão Série A)
                if jogo['league']['id'] != 71:
                    continue  # Pula jogos que não são do Brasileirão
                
                # Converte horário para fuso do Brasil
                data_jogo = jogo['fixture']['date']
                if isinstance(data_jogo, str):
                    try:
                        dt = datetime.fromisoformat(data_jogo.replace('Z', '+00:00'))
                        data_formatada = dt.strftime('%d/%m %H:%M')
                    except:
                        data_formatada = data_jogo
                else:
                    data_formatada = str(data_jogo)
                
                # Status do jogo
                status = jogo['fixture']['status']['short']
                status_longo = jogo['fixture']['status']['long']
                minuto = jogo['fixture']['status'].get('elapsed')
                
                # Classificar status
                ao_vivo = status in ['1H', '2H', 'HT', 'ET', 'P', 'LIVE']
                finalizado = status in ['FT', 'AET', 'PEN']
                agendado = status in ['TBD', 'NS', 'PST']
                
                # Extrai estatísticas se disponível
                estatisticas = extrair_estatisticas(jogo)
                
                jogo_info = {
                    'id': jogo['fixture']['id'],
                    'time_casa': jogo['teams']['home']['name'],
                    'time_visitante': jogo['teams']['away']['name'],
                    'escudo_casa': jogo['teams']['home'].get('logo', ''),
                    'escudo_visitante': jogo['teams']['away'].get('logo', ''),
                    'gols_casa': jogo['goals']['home'] if jogo['goals']['home'] is not None else 0,
                    'gols_visitante': jogo['goals']['away'] if jogo['goals']['away'] is not None else 0,
                    'status': status,
                    'status_longo': status_longo,
                    'minuto': minuto,
                    'competicao': 'Brasileirão Série A',
                    'rodada': jogo['league'].get('round', 'Rodada'),
                    'horario_formatado': data_formatada,
                    'horario': jogo['fixture']['date'],
                    'estadio': jogo['fixture']['venue']['name'] if jogo['fixture'].get('venue') else None,
                    'cidade': jogo['fixture']['venue']['city'] if jogo['fixture'].get('venue') else None,
                    'ao_vivo': ao_vivo,
                    'finalizado': finalizado,
                    'agendado': agendado,
                    'estatisticas': estatisticas
                }
                jogos_processados.append(jogo_info)
                
            except Exception as e:
                # Erro silencioso - continua processamento
                continue
                continue
        
        # Ordena: ao vivo primeiro, depois agendados, depois finalizados
        jogos_processados.sort(key=lambda x: (
            0 if x['ao_vivo'] else 1 if x['agendado'] else 2,
            x['horario']
        ))
        
        # Limita a 15 jogos máximo
        jogos_processados = jogos_processados[:15]
        
        # Dados para cache
        proxima_atualizacao = datetime.now() + timedelta(seconds=CACHE_TIMEOUT)
        cache_data = {
            'jogos': jogos_processados,
            'ultima_atualizacao': datetime.now().strftime('%H:%M:%S'),
            'proxima_atualizacao': proxima_atualizacao.strftime('%H:%M:%S'),
            'total_jogos': len(jogos_processados),
            'ao_vivo': len([j for j in jogos_processados if j['ao_vivo']]),
            'agendados': len([j for j in jogos_processados if j['agendado']]),
            'finalizados': len([j for j in jogos_processados if j['finalizado']])
        }
        
        # Salva no cache
        cache.set(CACHE_KEY, cache_data, CACHE_TIMEOUT)
        cache.set(CACHE_BACKUP_KEY, cache_data, CACHE_BACKUP_TIMEOUT)
        
        return JsonResponse({
            'success': True,
            'jogos': jogos_processados,
            'ultima_atualizacao': cache_data['ultima_atualizacao'],
            'proxima_atualizacao': cache_data['proxima_atualizacao'],
            'estatisticas': {
                'total_jogos': cache_data['total_jogos'],
                'ao_vivo': cache_data['ao_vivo'],
                'agendados': cache_data['agendados'],
                'finalizados': cache_data['finalizados']
            },
            'fonte': fonte,
            'debug': f'Buscou {len(jogos_api)} jogos do Brasileirão - fonte: {fonte}'
        })
        
    except Exception as e:
        # Tenta cache backup
        backup_cache = cache.get(CACHE_BACKUP_KEY)
        if backup_cache:
            return JsonResponse({
                'success': True,
                'jogos': backup_cache['jogos'],
                'ultima_atualizacao': backup_cache['ultima_atualizacao'],
                'fonte': 'cache_backup',
                'erro': f'API indisponível: {str(e)}'
            })
        
        # Último recurso: dados simulados do Brasileirão
        return JsonResponse({
            'success': True,
            'jogos': [
                {
                    'id': 999999,
                    'time_casa': 'Flamengo',
                    'time_visitante': 'Palmeiras',
                    'gols_casa': 2,
                    'gols_visitante': 1,
                    'status': '2H',
                    'status_longo': 'Segundo Tempo',
                    'minuto': 67,
                    'ao_vivo': True,
                    'finalizado': False,
                    'agendado': False,
                    'competicao': 'Brasileirão Série A',
                    'rodada': 'Rodada 5',
                    'horario_formatado': datetime.now().strftime('%d/%m %H:%M'),
                    'estadio': 'Maracanã',
                    'cidade': 'Rio de Janeiro',
                    'escudo_casa': '',
                    'escudo_visitante': '',
                    'estatisticas': None
                }
            ],
            'ultima_atualizacao': datetime.now().strftime('%H:%M:%S'),
            'fonte': 'erro_fallback',
            'erro': f'API falhou: {str(e)}',
            'estatisticas': {'total_jogos': 1, 'ao_vivo': 1, 'agendados': 0, 'finalizados': 0}
        })


def extrair_estatisticas(jogo):
    """Extrai estatísticas detalhadas do jogo se disponível"""
    try:
        stats = jogo.get('statistics', [])
        if not stats:
            return None
            
        estatisticas = {
            'casa': {},
            'visitante': {}
        }
        
        # Mapeamento de estatísticas importantes
        stats_map = {
            'Shots on Goal': 'chutes_no_gol',
            'Shots off Goal': 'chutes_para_fora', 
            'Total Shots': 'total_chutes',
            'Ball Possession': 'posse_de_bola',
            'Fouls': 'faltas',
            'Yellow Cards': 'cartoes_amarelos',
            'Red Cards': 'cartoes_vermelhos',
            'Offsides': 'impedimentos',
            'Corner Kicks': 'escanteios',
            'Passes %': 'precisao_passes',
            'expected_goals': 'gols_esperados'
        }
        
        for team_stats in stats:
            team = 'casa' if team_stats['team']['id'] == jogo['teams']['home']['id'] else 'visitante'
            
            for stat in team_stats['statistics']:
                stat_name = stat['type']
                stat_value = stat['value']
                
                if stat_name in stats_map:
                    key = stats_map[stat_name]
                    estatisticas[team][key] = stat_value
        
        return estatisticas
        
    except Exception:
        return None


def manifest(request):
    """Serve o manifest.json com Content-Type correto"""
    try:
        manifest_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR / 'static', 'manifest.json')
        
        # Se não encontrar no STATIC_ROOT, tenta no diretório static do projeto
        if not os.path.exists(manifest_path):
            manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        return JsonResponse(manifest_data, content_type='application/manifest+json')
    
    except FileNotFoundError:
        # Se não encontrar o arquivo, retorna um manifest básico
        manifest_data = {
            "name": "FutAmigo - Bolão de Futebol",
            "short_name": "FutAmigo",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#000000"
        }
        return JsonResponse(manifest_data, content_type='application/manifest+json')


def service_worker(request):
    """Serve um service worker minimalista para PWA"""
    smart_sw = """
// Service Worker minimalista - FutAmigo v3
// Apenas intercepta quando OFFLINE para mostrar página offline
const CACHE_NAME = 'futamigo-v3';
const OFFLINE_URL = '/offline/';

self.addEventListener('install', function(event) {
    // Instala sem fazer nenhuma requisição extra ao servidor
    // A página offline será cacheada na primeira oportunidade
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', function(event) {
    // Só intercepta requisições de navegação (páginas HTML)
    if (event.request.mode !== 'navigate') {
        return;
    }
    
    // Não interceptar a própria página offline
    const url = new URL(event.request.url);
    if (url.pathname === '/offline/') {
        return;
    }
    
    event.respondWith(
        fetch(event.request).then(function(response) {
            // Sucesso na rede - cacheia a página offline em background
            // (só uma vez, silenciosamente)
            if (response.ok) {
                caches.open(CACHE_NAME).then(function(cache) {
                    cache.match(OFFLINE_URL).then(function(cached) {
                        if (!cached) {
                            cache.add(OFFLINE_URL).catch(function() {});
                        }
                    });
                });
            }
            return response;
        }).catch(function() {
            // Sem internet - mostra página offline do cache
            return caches.open(CACHE_NAME).then(function(cache) {
                return cache.match(OFFLINE_URL);
            }).then(function(cachedResponse) {
                if (cachedResponse) {
                    return cachedResponse;
                }
                // Se nem o cache tem, retorna uma resposta básica
                return new Response(
                    '<html><body style="text-align:center;padding:50px;font-family:sans-serif">' +
                    '<h1>FutAmigo</h1><p>Você está sem internet.</p>' +
                    '<button onclick="location.reload()">Tentar novamente</button></body></html>',
                    { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
                );
            });
        })
    );
});
    """
    
    return HttpResponse(smart_sw, content_type='application/javascript')


def offline_page(request):
    """Página offline para PWA"""
    return render(request, 'bolao/offline.html')


@login_required
def notification_settings(request):
    """Página de configurações de notificações"""
    participante = request.user.participante
    
    # Garantir que existe uma configuração de notificação
    settings, created = NotificationSettings.objects.get_or_create(participante=participante)
    
    if request.method == 'POST':
        # Atualizar configurações
        settings.enabled = request.POST.get('enabled') == 'on'
        settings.nova_rodada = request.POST.get('nova_rodada') == 'on'
        settings.lembrete_prazo = request.POST.get('lembrete_prazo') == 'on'
        settings.resultados_publicados = request.POST.get('resultados_publicados') == 'on'
        settings.ranking_atualizado = request.POST.get('ranking_atualizado') == 'on'
        settings.save()
        
        messages.success(request, 'Configurações de notificações atualizadas com sucesso!')
        return JsonResponse({'success': True})
    
    # Histórico de notificações (últimas 10)
    historico = Notification.objects.filter(participante=participante)[:10]
    
    context = {
        'settings': settings,
        'historico': historico,
        'permission_supported': True,
    }
    return render(request, 'bolao/notification_settings.html', context)


@login_required
@require_POST
def save_push_subscription(request):
    """Salva a subscrição push do usuário"""
    try:
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        
        participante = request.user.participante
        settings, created = NotificationSettings.objects.get_or_create(participante=participante)
        
        # Receber dados da subscrição do frontend
        subscription_data = json.loads(request.body)
        
        # Log para debug (especialmente útil para mobile)
        logger.info(f"Push subscription recebida para {participante.nome_exibicao}")
        logger.info(f"Dados: {subscription_data}")
        
        # Validar dados mínimos necessários
        if 'endpoint' in subscription_data:
            # Formato novo com dados separados
            formatted_data = {
                'endpoint': subscription_data['endpoint'],
                'keys': subscription_data.get('keys', {}),
                'mobile_info': subscription_data.get('mobile_info', {})
            }
        else:
            # Formato antigo (subscription completa)
            formatted_data = subscription_data
        
        # Salvar os dados da subscrição
        settings.push_subscription = formatted_data
        settings.save()
        
        logger.info(f"Push subscription salva com sucesso para {participante.nome_exibicao}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Subscrição salva com sucesso!',
            'mobile_detected': subscription_data.get('mobile_info', {}).get('is_mobile', False)
        })
    
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON da push subscription: {e}")
        return JsonResponse({'success': False, 'error': 'Dados inválidos'})
    except Exception as e:
        logger.error(f"Erro ao salvar push subscription: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required  
@require_POST
def test_notification(request):
    """Envia uma notificação de teste"""
    try:
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        participante = request.user.participante
        
        # Capturar dados extras do request para debug
        request_data = {}
        if request.content_type == 'application/json':
            try:
                request_data = json.loads(request.body)
            except:
                pass
        
        # Log detalhado para debug mobile
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile = any(mobile in user_agent.lower() for mobile in ['mobile', 'android', 'iphone', 'ipad'])
        
        logger.info(f"Teste de notificação para {participante.nome_exibicao}")
        logger.info(f"User-Agent: {user_agent}")
        logger.info(f"Mobile detectado: {is_mobile}")
        logger.info(f"Dados extras: {request_data}")
        logger.info(f"HTTPS: {request.is_secure()}")
        
        # Criar notificação de teste
        notification = Notification.objects.create(
            participante=participante,
            tipo='sistema',
            titulo='🎉 Teste de Notificação',
            mensagem=f'Se você está vendo isso, as notificações estão funcionando! {("📱 Mobile" if is_mobile else "💻 Desktop")}',
            url_acao=request.build_absolute_uri('/'),
        )
        
        # Tentar enviar notificação
        success = send_push_notification(notification)
        
        if success:
            messages.success(request, 'Notificação de teste enviada com sucesso!')
            return JsonResponse({
                'success': True, 
                'message': 'Teste enviado!',
                'mobile_detected': is_mobile,
                'notification_id': notification.id
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Falha ao enviar notificação',
                'notification_id': notification.id
            })
            
    except Exception as e:
        logger.error(f"Erro no teste de notificação: {e}")
        logger.error(f"Stack trace: {e.__traceback__}")
        return JsonResponse({'success': False, 'error': str(e)})


def send_push_notification(notification):
    """Envia uma notificação push (preparado para implementação futura)"""
    try:
        # Aqui será implementado o envio real via web-push
        # Por enquanto, apenas simula o envio
        notification.status = 'sent'
        notification.enviada_em = timezone.now()
        notification.save()
        
        return True
    
    except Exception as e:
        notification.status = 'failed'
        notification.error_message = str(e)
        notification.save()
        return False


def send_notification_to_users(tipo, titulo, mensagem, rodada=None, url_acao=''):
    """Envia notificação para todos os usuários que têm esse tipo ativado"""
    from .models import NotificationSettings, Notification
    
    # Filtrar usuários que têm o tipo de notificação ativado
    field_map = {
        'nova_rodada': 'nova_rodada',
        'lembrete_prazo': 'lembrete_prazo', 
        'resultados': 'resultados_publicados',
        'ranking': 'ranking_atualizado',
    }
    
    if tipo in field_map:
        filter_kwargs = {
            'enabled': True,
            field_map[tipo]: True
        }
        settings_queryset = NotificationSettings.objects.filter(**filter_kwargs)
    else:
        # Para notificações de sistema, enviar para todos com notificações ativadas
        settings_queryset = NotificationSettings.objects.filter(enabled=True)
    
    notifications_created = []
    
    for setting in settings_queryset:
        notification = Notification.objects.create(
            participante=setting.participante,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            rodada_relacionada=rodada,
            url_acao=url_acao
        )
        notifications_created.append(notification)
        
        # Tentar enviar push notification
        send_push_notification(notification)
    
    return len(notifications_created)

