#!/usr/bin/env python
"""
Script para atualizar a lista de times do Brasileirão 2026
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
django.setup()

from bolao.models import Time

def atualizar_times():
    # Nova lista de times para 2026
    novos_times = [
        {'nome': 'Athletico-PR', 'sigla': 'CAP'},
        {'nome': 'Atlético-MG', 'sigla': 'CAM'}, 
        {'nome': 'Bahia', 'sigla': 'BAH'},
        {'nome': 'Botafogo', 'sigla': 'BOT'},
        {'nome': 'Chapecoense', 'sigla': 'CHA'},
        {'nome': 'Corinthians', 'sigla': 'COR'},
        {'nome': 'Coritiba', 'sigla': 'COT'},
        {'nome': 'Cruzeiro', 'sigla': 'CRU'},
        {'nome': 'Flamengo', 'sigla': 'FLA'},
        {'nome': 'Fluminense', 'sigla': 'FLU'},
        {'nome': 'Grêmio', 'sigla': 'GRE'},
        {'nome': 'Internacional', 'sigla': 'INT'},
        {'nome': 'Mirassol', 'sigla': 'MIR'},
        {'nome': 'Palmeiras', 'sigla': 'PAL'},
        {'nome': 'Red Bull Bragantino', 'sigla': 'RBB'},
        {'nome': 'Remo', 'sigla': 'REM'},
        {'nome': 'Santos', 'sigla': 'SAN'},
        {'nome': 'São Paulo', 'sigla': 'SAO'},
        {'nome': 'Vasco', 'sigla': 'VAS'},
        {'nome': 'Vitória', 'sigla': 'VIT'},
    ]
    
    # Obter nomes dos novos times
    nomes_novos_times = [time['nome'] for time in novos_times]
    
    # Verificar times existentes
    times_existentes = Time.objects.all()
    print(f"Times atualmente no banco: {times_existentes.count()}")
    
    # Remover times que não estão na nova lista
    times_para_remover = times_existentes.exclude(nome__in=nomes_novos_times)
    if times_para_remover.exists():
        print(f"\nRemovendo {times_para_remover.count()} times:")
        for time in times_para_remover:
            print(f"  - {time.nome}")
            time.delete()
    
    # Adicionar novos times
    times_adicionados = 0
    for time_info in novos_times:
        time, created = Time.objects.get_or_create(
            nome=time_info['nome'],
            defaults={'sigla': time_info['sigla']}
        )
        
        if created:
            print(f"  + Adicionado: {time.nome} ({time.sigla})")
            times_adicionados += 1
        else:
            # Atualizar sigla se necessário
            if time.sigla != time_info['sigla']:
                time.sigla = time_info['sigla']
                time.save()
                print(f"  ~ Atualizado: {time.nome} - sigla: {time.sigla}")
    
    print(f"\nResumo:")
    print(f"Times removidos: {times_para_remover.count()}")
    print(f"Times adicionados: {times_adicionados}")
    print(f"Total de times no banco: {Time.objects.count()}")
    
    # Listar todos os times atuais
    print(f"\nTimes atuais no banco:")
    for time in Time.objects.all().order_by('nome'):
        print(f"  {time.nome} ({time.sigla})")

if __name__ == '__main__':
    try:
        atualizar_times()
        print("\n✅ Atualização dos times concluída com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante a atualização: {e}")
        sys.exit(1)