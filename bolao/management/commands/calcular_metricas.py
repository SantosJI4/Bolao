from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from bolao.models import SessaoVisita, AcaoUsuario, MetricaDiaria, PaginaPopular
from django.db.models import Count, Avg, Q


class Command(BaseCommand):
    help = 'Gera métricas diárias de analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Data específica para calcular (YYYY-MM-DD), padrão: ontem'
        )
        parser.add_argument(
            '--reset-today',
            action='store_true',
            help='Reseta contadores de páginas populares de hoje'
        )

    def handle(self, *args, **options):
        if options['reset_today']:
            self.reset_today_counters()
            return

        # Determina a data para calcular
        if options['date']:
            target_date = timezone.datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            target_date = date.today() - timedelta(days=1)  # Ontem por padrão

        self.stdout.write(f'Calculando métricas para {target_date}')
        
        self.calculate_daily_metrics(target_date)
        
        self.stdout.write(
            self.style.SUCCESS(f'Métricas calculadas com sucesso para {target_date}')
        )

    def calculate_daily_metrics(self, target_date):
        """Calcula e salva as métricas do dia especificado"""
        # Data de início e fim do dia
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(target_date, timezone.datetime.min.time())
        )
        end_datetime = timezone.make_aware(
            timezone.datetime.combine(target_date, timezone.datetime.max.time())
        )

        # Sessões do dia
        sessoes_do_dia = SessaoVisita.objects.filter(
            data_inicio__range=[start_datetime, end_datetime]
        )

        # Ações do dia
        acoes_do_dia = AcaoUsuario.objects.filter(
            timestamp__range=[start_datetime, end_datetime]
        )

        # Cálculos básicos
        total_visitas = sessoes_do_dia.count()
        visitantes_unicos = sessoes_do_dia.aggregate(
            unique_ips=Count('ip_address', distinct=True)
        )['unique_ips'] or 0

        usuarios_logados = sessoes_do_dia.filter(
            participante__isnull=False
        ).count()
        
        usuarios_anonimos = total_visitas - usuarios_logados

        total_pageviews = acoes_do_dia.filter(tipo_acao='page_view').count()

        # Tempo médio de sessão (apenas sessões finalizadas)
        sessoes_finalizadas = sessoes_do_dia.filter(data_fim__isnull=False)
        tempo_medio = sessoes_finalizadas.aggregate(
            media=Avg('duracao_minutos')
        )['media'] or 0

        # Taxa de rejeição (sessões com apenas 1 página)
        sessoes_bounce = sessoes_do_dia.filter(paginas_visitadas=1).count()
        bounce_rate = (sessoes_bounce / total_visitas * 100) if total_visitas > 0 else 0

        # Palpites realizados
        palpites_realizados = acoes_do_dia.filter(tipo_acao='palpite').count()

        # Dispositivos
        mobile_visitas = sessoes_do_dia.filter(dispositivo_tipo='mobile').count()
        desktop_visitas = sessoes_do_dia.filter(dispositivo_tipo='desktop').count()
        tablet_visitas = sessoes_do_dia.filter(dispositivo_tipo='tablet').count()

        # Cria ou atualiza a métrica do dia
        metrica, created = MetricaDiaria.objects.update_or_create(
            data=target_date,
            defaults={
                'total_visitas': total_visitas,
                'visitantes_unicos': visitantes_unicos,
                'usuarios_logados': usuarios_logados,
                'usuarios_anonimos': usuarios_anonimos,
                'total_pageviews': total_pageviews,
                'tempo_medio_sessao': tempo_medio,
                'bounce_rate': bounce_rate,
                'palpites_realizados': palpites_realizados,
                'mobile_visitas': mobile_visitas,
                'desktop_visitas': desktop_visitas,
                'tablet_visitas': tablet_visitas
            }
        )

        status = "criada" if created else "atualizada"
        self.stdout.write(f'Métrica {status}: {metrica}')

    def reset_today_counters(self):
        """Reseta os contadores de hoje das páginas populares"""
        PaginaPopular.objects.update(visitas_hoje=0)
        self.stdout.write(
            self.style.SUCCESS('Contadores de hoje resetados com sucesso')
        )