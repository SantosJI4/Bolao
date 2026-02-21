"""
Management command para testar as informações de rodadas futuras e recentes
Execute: python manage.py testar_rodadas_info
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Avg
from bolao.models import Rodada, Jogo, Palpite
from django.db import models


class Command(BaseCommand):
    help = 'Testa as informações detalhadas de rodadas futuras e recentes'
    
    def handle(self, *args, **options):
        agora = timezone.now()
        
        self.stdout.write(self.style.SUCCESS('🔍 Testando informações de rodadas...'))
        
        # Rodadas ativas
        rodadas_ativas = list(Rodada.objects.filter(ativa=True).order_by('numero'))
        self.stdout.write(f'📋 Rodadas ativas encontradas: {len(rodadas_ativas)}')
        
        for rodada in rodadas_ativas:
            self.stdout.write(f'  - {rodada} (ativa={rodada.ativa})')
        
        # Rodadas futuras (todas as rodadas, não só ativas)
        todas_rodadas = list(Rodada.objects.all().order_by('numero'))
        rodadas_futuras = [r for r in todas_rodadas if r.data_inicio > agora][:3]
        self.stdout.write(f'\n🔮 Rodadas futuras: {len(rodadas_futuras)}')
        
        for rodada in rodadas_futuras:
            jogos_count = rodada.jogo_set.count()
            dias_restantes = (rodada.data_inicio - agora).days
            status_texto = f"{jogos_count} jogos" + (f" em {dias_restantes} dias" if dias_restantes > 0 else " hoje")
            
            self.stdout.write(f'  - {rodada}:')
            self.stdout.write(f'    Jogos: {jogos_count}')
            self.stdout.write(f'    Dias restantes: {dias_restantes}')
            self.stdout.write(f'    Status: {status_texto}')
        
        # Rodadas passadas (todas as rodadas, não só ativas)
        rodadas_passadas = sorted([r for r in todas_rodadas if r.data_fim < agora], key=lambda x: x.numero, reverse=True)[:3]
        self.stdout.write(f'\n📊 Resultados recentes: {len(rodadas_passadas)}')
        
        for rodada in rodadas_passadas:
            jogos_finalizados = rodada.jogo_set.filter(resultado_finalizado=True).count()
            total_jogos = rodada.jogo_set.count()
            
            # Principais jogos
            principais_jogos = list(rodada.jogo_set.filter(resultado_finalizado=True).select_related('time_casa', 'time_visitante')[:2])
            
            # Pontuação média
            palpites_rodada = Palpite.objects.filter(jogo__rodada=rodada, jogo__resultado_finalizado=True)
            # Como pontos_obtidos é uma property, calculamos manualmente
            total_pontos = 0
            total_palpites = 0
            for palpite in palpites_rodada:
                total_pontos += palpite.pontos_obtidos
                total_palpites += 1
            pontuacao_media = total_pontos / total_palpites if total_palpites > 0 else 0
            
            percentual = round((jogos_finalizados / total_jogos * 100) if total_jogos > 0 else 0)
            
            self.stdout.write(f'  - {rodada}:')
            self.stdout.write(f'    Jogos finalizados: {jogos_finalizados}/{total_jogos} ({percentual}%)')
            self.stdout.write(f'    Pontuação média: {round(pontuacao_media, 1)}')
            self.stdout.write(f'    Principais jogos: {len(principais_jogos)}')
            
            for jogo in principais_jogos:
                self.stdout.write(f'      * {jogo.time_casa.sigla} {jogo.gols_casa} x {jogo.gols_visitante} {jogo.time_visitante.sigla}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Teste concluído!'))