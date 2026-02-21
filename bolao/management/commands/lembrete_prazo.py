"""
Management command para enviar lembretes de prazo de palpites
Execute via crontab: python manage.py lembrete_prazo
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bolao.models import Rodada
from bolao.views import send_notification_to_users


class Command(BaseCommand):
    help = 'Envia lembrete de prazo de palpites para rodadas ativas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--horas-antecedencia',
            type=int,
            default=2,
            help='Quantas horas antes do prazo enviar o lembrete (padrão: 2)'
        )
    
    def handle(self, *args, **options):
        horas_antecedencia = options['horas_antecedencia']
        agora = timezone.now()
        limite_lembrete = agora + timedelta(hours=horas_antecedencia)
        
        # Buscar rodadas ativas que vão fechar nas próximas X horas
        rodadas_para_lembrete = Rodada.objects.filter(
            ativa=True,
            data_fim__gt=agora,  # Ainda não fechou
            data_fim__lte=limite_lembrete  # Vai fechar nas próximas X horas
        )
        
        for rodada in rodadas_para_lembrete:
            tempo_restante = rodada.data_fim - agora
            horas = int(tempo_restante.total_seconds() // 3600)
            minutos = int((tempo_restante.total_seconds() % 3600) // 60)
            
            if horas > 0:
                tempo_str = f"{horas}h"
                if minutos > 0:
                    tempo_str += f"{minutos}m"
            else:
                tempo_str = f"{minutos}m"
            
            titulo = f"Prazo da {rodada} termina em {tempo_str}!"
            mensagem = f"Últimas horas para fazer seus palpites da {rodada}! Não perca o prazo: {rodada.data_fim.strftime('%d/%m %H:%M')}"
            url_acao = "/palpites/"
            
            count = send_notification_to_users('lembrete_prazo', titulo, mensagem, rodada, url_acao)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Lembrete enviado para {rodada} - {count} notificação(ões) enviada(s)'
                )
            )
        
        if not rodadas_para_lembrete.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Nenhuma rodada ativa encontrada com prazo nas próximas {horas_antecedencia} horas'
                )
            )