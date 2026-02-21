"""
Management command para criar rodadas de teste
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from bolao.models import Rodada


class Command(BaseCommand):
    help = 'Cria rodadas futuras para teste'
    
    def handle(self, *args, **options):
        agora = timezone.now()
        
        self.stdout.write('🔧 Criando rodadas de teste...')
        
        # Criar Rodada 6 (futura)
        rodada6, created = Rodada.objects.get_or_create(
            numero=6,
            defaults={
                'nome': 'RODADA 6',
                'data_inicio': agora + timedelta(days=3),
                'data_fim': agora + timedelta(days=8),
                'ativa': False
            }
        )
        status = 'criada' if created else 'já existe'
        self.stdout.write(f'📅 Rodada 6: {status} - {rodada6.data_inicio.strftime("%d/%m/%Y %H:%M")}')
        
        # Criar Rodada 7 (futura)
        rodada7, created = Rodada.objects.get_or_create(
            numero=7,
            defaults={
                'nome': 'RODADA 7',
                'data_inicio': agora + timedelta(days=10),
                'data_fim': agora + timedelta(days=15),
                'ativa': False
            }
        )
        status = 'criada' if created else 'já existe'
        self.stdout.write(f'📅 Rodada 7: {status} - {rodada7.data_inicio.strftime("%d/%m/%Y %H:%M")}')
        
        # Criar Rodada 8 (futura)
        rodada8, created = Rodada.objects.get_or_create(
            numero=8,
            defaults={
                'nome': 'RODADA 8',
                'data_inicio': agora + timedelta(days=17),
                'data_fim': agora + timedelta(days=22),
                'ativa': False
            }
        )
        status = 'criada' if created else 'já existe'
        self.stdout.write(f'📅 Rodada 8: {status} - {rodada8.data_inicio.strftime("%d/%m/%Y %H:%M")}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Rodadas de teste criadas com sucesso!'))
        self.stdout.write('🔍 Execute "python manage.py testar_rodadas_info" para verificar')