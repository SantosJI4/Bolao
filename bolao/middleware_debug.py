"""
Middleware para debug de performance e otimização
"""

import time
import logging
from django.conf import settings
from django.http import HttpResponse

logger = logging.getLogger(__name__)


class PerformanceMiddleware:
    """Middleware para monitorar performance das requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Marcar início da request
        start_time = time.time()
        
        # Processar request
        response = self.get_response(request)
        
        # Calcular tempo total
        total_time = time.time() - start_time
        total_time_ms = round(total_time * 1000, 2)
        
        # Log apenas se demorar mais que 1 segundo ou em DEBUG
        if total_time > 1.0 or settings.DEBUG:
            logger.info(f'🚀 {request.method} {request.path} - {total_time_ms}ms')
            
            # Adicionar header de debug
            response['X-Response-Time'] = f'{total_time_ms}ms'
            
            # Log de requests lentas
            if total_time > 2.0:
                logger.warning(f'⚠️  REQUEST LENTA: {request.path} - {total_time_ms}ms')
                
        return response


class DatabaseOptimizationMiddleware:
    """Middleware para otimizar queries do banco"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            # Reset contador de queries
            from django.db import connection, reset_queries
            reset_queries()
        
        response = self.get_response(request)
        
        if settings.DEBUG:
            # Log queries se houver muitas
            query_count = len(connection.queries)
            if query_count > 10:
                logger.warning(f'🗃️  MUITAS QUERIES: {request.path} - {query_count} queries')
                
                # Log das queries mais lentas
                for query in connection.queries:
                    if float(query['time']) > 0.01:  # > 10ms
                        logger.warning(f"   - {query['time']}s: {query['sql'][:100]}...")
        
        return response


class CacheOptimizationMiddleware:
    """Middleware para otimizar cache"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Adicionar headers de cache otimizados
        response = self.get_response(request)
        
        # Para arquivos estáticos, adicionar cache longo
        if request.path.startswith('/static/') or request.path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
            response['Cache-Control'] = 'public, max-age=86400'  # 24 horas
            
        # Para páginas dinâmicas, cache curto 
        elif request.path in ['/', '/classificacao/', '/jogos-ao-vivo/']:
            response['Cache-Control'] = 'public, max-age=60'  # 1 minuto
            
        return response


class ErrorHandlingMiddleware:
    """Middleware para tratar erros de forma mais amigável"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f'💥 ERRO em {request.path}: {str(e)}')
            
            if settings.DEBUG:
                raise  # Re-raise em desenvolvimento
            else:
                # Em produção, retorna erro amigável
                return HttpResponse(
                    'Erro temporário. Tente novamente em alguns minutos.',
                    status=500
                )


class SecurityOptimizationMiddleware:
    """Middleware para otimizações de segurança"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Headers de segurança otimizados
        if not settings.DEBUG:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            
        return response