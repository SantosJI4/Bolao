"""
Management command para testar todas as notificações automáticas do sistema
Execute: python manage.py testar_notificacoes_automaticas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from bolao.models import Rodada, Participante
from bolao.views import send_notification_to_users


class Command(BaseCommand):
    help = 'Testa todas as notificações automáticas do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            choices=['nova_rodada', 'lembrete_prazo', 'resultados', 'ranking', 'todos'],
            default='todos',
            help='Tipo de notificação para testar'
        )
    
    def handle(self, *args, **options):
        tipo = options['tipo']
        agora = timezone.now()
        
        # Buscar a rodada ativa atual ou primeira disponível
        try:
            rodada_atual = Rodada.objects.filter(ativa=True).first() or Rodada.objects.first()
        except:
            rodada_atual = None
            
        total_participantes = Participante.objects.filter(ativo=True).count()
        
        self.stdout.write(
            self.style.WARNING(
                f"🧪 Testando notificações automáticas - {total_participantes} participantes ativos"
            )
        )
        
        if tipo in ['nova_rodada', 'todos']:
            self._test_nova_rodada(rodada_atual)
            
        if tipo in ['lembrete_prazo', 'todos']:
            self._test_lembrete_prazo(rodada_atual)
            
        if tipo in ['resultados', 'todos']:
            self._test_resultados_publicados(rodada_atual)
            
        if tipo in ['ranking', 'todos']:
            self._test_ranking_atualizado()
    
    def _test_nova_rodada(self, rodada):
        """Testa notificação de nova rodada"""
        self.stdout.write("Nova rodada - Testando...")
        
        titulo = f"Nova Rodada {rodada.numero if rodada else 'X'} Liberada!"
        mensagem = f"A Rodada {rodada.numero if rodada else 'X'} já está aberta para palpites! Não perca o prazo."
        url_acao = "/palpites/"
        
        count = send_notification_to_users('nova_rodada', titulo, mensagem, rodada, url_acao)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"OK - {count} notificação(ões) de nova rodada enviada(s)"
            )
        )
    
    def _test_lembrete_prazo(self, rodada):
        """Testa notificação de lembrete de prazo"""
        self.stdout.write("Lembrete de prazo - Testando...")
        
        titulo = f"Prazo da Rodada {rodada.numero if rodada else 'X'} termina em 2h!"
        mensagem = f"Últimas horas para fazer seus palpites da Rodada {rodada.numero if rodada else 'X'}! Não perca o prazo!"
        url_acao = "/palpites/"
        
        count = send_notification_to_users('lembrete_prazo', titulo, mensagem, rodada, url_acao)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"OK - {count} notificação(ões) de lembrete enviada(s)"
            )
        )
    
    def _test_resultados_publicados(self, rodada):
        """Testa notificação de resultados publicados"""
        self.stdout.write("Resultados publicados - Testando...")
        
        titulo = f"Resultados da Rodada {rodada.numero if rodada else 'X'}!"
        mensagem = f"Os resultados da Rodada {rodada.numero if rodada else 'X'} foram publicados! Confira como foi sua rodada e veja a classificação atualizada."
        url_acao = "/resultados/"
        
        count = send_notification_to_users('resultados', titulo, mensagem, rodada, url_acao)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"OK - {count} notificação(ões) de resultados enviada(s)"
            )
        )
    
    def _test_ranking_atualizado(self):
        """Testa notificação de ranking atualizado"""
        self.stdout.write("Ranking atualizado - Testando...")
        
        titulo = "Ranking Atualizado!"
        mensagem = "O ranking foi recalculado! Confira sua nova posição na classificação."
        url_acao = "/classificacao/"
        
        count = send_notification_to_users('ranking', titulo, mensagem, None, url_acao)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"OK - {count} notificação(ões) de ranking enviada(s)"
            )
        )
        
    def handle(self, *args, **options):
        tipo = options['tipo']
        
        # Buscar a rodada ativa atual ou primeira disponível
        try:
            rodada_atual = Rodada.objects.filter(ativa=True).first() or Rodada.objects.first()
        except:
            rodada_atual = None
            
        total_participantes = Participante.objects.filter(ativo=True).count()
        
        self.stdout.write(
            self.style.WARNING(
                f"Testando notificacoes automaticas - {total_participantes} participantes ativos"
            )
        )
        
        if tipo in ['nova_rodada', 'todos']:
            self._test_nova_rodada(rodada_atual)
            
        if tipo in ['lembrete_prazo', 'todos']:
            self._test_lembrete_prazo(rodada_atual)
            
        if tipo in ['resultados', 'todos']:
            self._test_resultados_publicados(rodada_atual)
            
        if tipo in ['ranking', 'todos']:
            self._test_ranking_atualizado()
            
        self.stdout.write(
            self.style.SUCCESS(
                "Teste de notificacoes concluido! Verifique se as notificacoes aparecem no navegador em ate 30 segundos."
            )
        )