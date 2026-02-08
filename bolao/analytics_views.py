from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import date, timedelta
from .models import SessaoVisita, AcaoUsuario, MetricaDiaria, PaginaPopular, Participante
from django.http import JsonResponse


@staff_member_required
def analytics_dashboard(request):
    """Dashboard de analytics para staff"""
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    semana_passada = hoje - timedelta(days=7)
    mes_passado = hoje - timedelta(days=30)

    # Métricas de hoje
    sessoes_hoje = SessaoVisita.objects.filter(
        data_inicio__date=hoje
    )
    
    metricas_hoje = {
        'visitas': sessoes_hoje.count(),
        'usuarios_unicos': sessoes_hoje.aggregate(
            unique_ips=Count('ip_address', distinct=True)
        )['unique_ips'] or 0,
        'usuarios_logados': sessoes_hoje.filter(participante__isnull=False).count(),
        'pageviews': AcaoUsuario.objects.filter(
            timestamp__date=hoje,
            tipo_acao='page_view'
        ).count(),
        'tempo_medio': sessoes_hoje.filter(
            data_fim__isnull=False
        ).aggregate(media=Avg('duracao_minutos'))['media'] or 0
    }

    # Métricas de ontem (para comparação)
    try:
        metrica_ontem = MetricaDiaria.objects.get(data=ontem)
        metricas_ontem = {
            'visitas': metrica_ontem.total_visitas,
            'usuarios_unicos': metrica_ontem.visitantes_unicos,
            'usuarios_logados': metrica_ontem.usuarios_logados,
            'pageviews': metrica_ontem.total_pageviews,
            'tempo_medio': metrica_ontem.tempo_medio_sessao
        }
    except MetricaDiaria.DoesNotExist:
        metricas_ontem = {
            'visitas': 0,
            'usuarios_unicos': 0,
            'usuarios_logados': 0,
            'pageviews': 0,
            'tempo_medio': 0
        }

    # Sessões ativas agora
    sessoes_ativas = SessaoVisita.objects.filter(
        ativo=True,
        data_inicio__gte=timezone.now() - timedelta(minutes=30)
    ).count()

    # Últimas ações
    ultimas_acoes = AcaoUsuario.objects.select_related(
        'sessao', 'sessao__participante'
    ).order_by('-timestamp')[:20]

    # Páginas mais visitadas hoje
    paginas_populares = PaginaPopular.objects.order_by('-visitas_hoje')[:10]

    # Dispositivos (últimos 7 dias)
    dispositivos = SessaoVisita.objects.filter(
        data_inicio__date__gte=semana_passada
    ).values('dispositivo_tipo').annotate(
        count=Count('id')
    ).order_by('-count')

    # Navegadores (últimos 7 dias)
    navegadores = SessaoVisita.objects.filter(
        data_inicio__date__gte=semana_passada
    ).values('navegador').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Tendência semanal
    metricas_semana = MetricaDiaria.objects.filter(
        data__gte=semana_passada
    ).order_by('-data')

    # Usuários mais ativos
    try:
        usuarios_ativos = SessaoVisita.objects.filter(
            data_inicio__date__gte=semana_passada,
            participante__isnull=False
        ).values(
            'participante__nome_exibicao'
        ).annotate(
            total_sessoes=Count('id'),
            total_acoes=Count('acoes')
        ).order_by('-total_acoes')[:10]
    except:
        usuarios_ativos = []

    context = {
        'metricas_hoje': metricas_hoje,
        'metricas_ontem': metricas_ontem,
        'sessoes_ativas': sessoes_ativas,
        'ultimas_acoes': ultimas_acoes,
        'paginas_populares': paginas_populares,
        'dispositivos': dispositivos,
        'navegadores': navegadores,
        'metricas_semana': metricas_semana,
        'usuarios_ativos': usuarios_ativos,
        'hoje': hoje,
        'agora': timezone.now(),
    }

    return render(request, 'admin/analytics_dashboard.html', context)


@staff_member_required
def analytics_api(request):
    """API para dados de analytics em tempo real"""
    tipo = request.GET.get('tipo', 'sessoes_ativas')
    
    if tipo == 'sessoes_ativas':
        # Sessões ativas nos últimos 30 minutos
        count = SessaoVisita.objects.filter(
            ativo=True,
            data_inicio__gte=timezone.now() - timedelta(minutes=30)
        ).count()
        return JsonResponse({'count': count})
    
    elif tipo == 'pageviews_hoje':
        count = AcaoUsuario.objects.filter(
            timestamp__date=date.today(),
            tipo_acao='page_view'
        ).count()
        return JsonResponse({'count': count})
    
    elif tipo == 'ultimas_acoes':
        acoes = AcaoUsuario.objects.select_related(
            'sessao', 'sessao__participante'
        ).order_by('-timestamp')[:10]
        
        data = []
        for acao in acoes:
            usuario = acao.sessao.participante.nome_exibicao if acao.sessao.participante else f"IP: {acao.sessao.ip_address}"
            data.append({
                'usuario': usuario,
                'acao': acao.get_tipo_acao_display(),
                'pagina': acao.pagina_titulo or 'N/A',
                'tempo': acao.timestamp.strftime('%H:%M:%S')
            })
        
        return JsonResponse({'acoes': data})
    
    return JsonResponse({'error': 'Tipo não reconhecido'})