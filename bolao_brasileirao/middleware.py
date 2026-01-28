"""
Middleware personalizado para debug e tratamento de CSRF
"""
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponseForbidden
from django.template import loader
import logging

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
                logger.warning(f"CSRF Token ausente em POST para {request.path}")
                logger.warning(f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
                logger.warning(f"Referer: {request.META.get('HTTP_REFERER', 'None')}")
                
        return None
    
    def process_response(self, request, response):
        # Se for erro CSRF (403), adiciona headers de debug
        if response.status_code == 403 and not settings.DEBUG:
            logger.error(f"CSRF 403 error for {request.path}")
            logger.error(f"Method: {request.method}")
            logger.error(f"Origin: {request.META.get('HTTP_ORIGIN', 'None')}")
            
        return response


class SafeCSRFMiddleware(MiddlewareMixin):
    """
    Middleware que tenta recuperar de erros CSRF sem matar a aplicação
    """
    
    def process_exception(self, request, exception):
        # Se for erro relacionado a CSRF, tenta uma recuperação suave
        if 'CSRF' in str(exception) or 'csrf' in str(exception).lower():
            logger.error(f"CSRF Exception caught: {exception}")
            logger.error(f"Path: {request.path}")
            logger.error(f"Method: {request.method}")
            
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