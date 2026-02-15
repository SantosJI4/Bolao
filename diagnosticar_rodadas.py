#!/usr/bin/env python
"""
Script para diagnosticar problemas com rodadas do bolão
"""

import os
import sys
import django
from datetime import datetime

# Setup do Django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
django.setup()

from django.utils import timezone
from bolao.models import Rodada, Jogo

def diagnosticar_rodadas():
    print("🔍 DIAGNÓSTICO DAS RODADAS")
    print("=" * 50)
    
    # 1. Listar todas as rodadas
    todas_rodadas = Rodada.objects.all().order_by('numero')
    print(f"📊 Total de rodadas cadastradas: {todas_rodadas.count()}")
    print()
    
    # 2. Rodadas ativas
    rodadas_ativas = Rodada.objects.filter(ativa=True)
    print(f"✅ Rodadas marcadas como ATIVA: {rodadas_ativas.count()}")
    
    if rodadas_ativas.count() > 1:
        print("⚠️  PROBLEMA: Há mais de 1 rodada ativa!")
        print("   O sistema foi projetado para ter apenas 1 rodada ativa por vez.")
        print()
        
    for rodada in rodadas_ativas:
        print(f"   - {rodada} | Início: {rodada.data_inicio} | Fim: {rodada.data_fim}")
        print(f"     Status: {rodada.status} | Pode palpitar: {rodada.pode_palpitar}")
        jogos = rodada.jogo_set.count()
        print(f"     Jogos cadastrados: {jogos}")
        print()
        
    # 3. Rodadas inativas
    rodadas_inativas = Rodada.objects.filter(ativa=False)
    print(f"❌ Rodadas marcadas como INATIVA: {rodadas_inativas.count()}")
    
    # 4. Verificar rodadas por período
    agora = timezone.now()
    print(f"⏰ Data/hora atual: {agora}")
    print()
    
    rodadas_futuras = Rodada.objects.filter(data_inicio__gt=agora).order_by('numero')
    print(f"🔮 Rodadas FUTURAS (por data): {rodadas_futuras.count()}")
    for rodada in rodadas_futuras[:3]:
        ativa_status = "✅ ATIVA" if rodada.ativa else "❌ INATIVA"
        print(f"   - {rodada} | {ativa_status} | Início: {rodada.data_inicio}")
        
    print()
    rodadas_em_curso = Rodada.objects.filter(
        data_inicio__lte=agora, 
        data_fim__gte=agora
    ).order_by('numero')
    print(f"▶️  Rodadas EM CURSO (por data): {rodadas_em_curso.count()}")
    for rodada in rodadas_em_curso:
        ativa_status = "✅ ATIVA" if rodada.ativa else "❌ INATIVA"
        print(f"   - {rodada} | {ativa_status} | Fim: {rodada.data_fim}")
        
    print()
    rodadas_passadas = Rodada.objects.filter(data_fim__lt=agora).order_by('-numero')
    print(f"📜 Rodadas PASSADAS (por data): {rodadas_passadas.count()}")
    for rodada in rodadas_passadas[:3]:
        ativa_status = "✅ ATIVA" if rodada.ativa else "❌ INATIVA"
        print(f"   - {rodada} | {ativa_status} | Fim: {rodada.data_fim}")
    
    print()
    print("=" * 50)
    
    # 5. Recomendações
    if rodadas_ativas.count() == 0:
        print("💡 RECOMENDAÇÃO: Nenhuma rodada está ativa!")
        proxima_rodada = rodadas_futuras.first()
        if proxima_rodada:
            print(f"   Sugestão: Ative a rodada {proxima_rodada.numero}")
        else:
            print("   Cadastre e ative uma rodada para que apareça para os usuários.")
            
    elif rodadas_ativas.count() > 1:
        print("💡 RECOMENDAÇÃO: Há múltiplas rodadas ativas!")
        print("   Use a ação 'Ativar rodada selecionada' no admin para ativar apenas 1.")
        print("   Isso desativará automaticamente todas as outras.")
        
    else:
        rodada_unica = rodadas_ativas.first()
        if rodada_unica.status == 'futura':
            print("💡 STATUS: A rodada ativa ainda não começou (futura).")
        elif rodada_unica.status == 'atual':
            print("💡 STATUS: A rodada ativa está no período correto!")
        else:
            print("💡 STATUS: A rodada ativa já passou do período.")
            proxima = rodadas_futuras.first()
            if proxima:
                print(f"   Sugestão: Ative a rodada {proxima.numero}")

def corrigir_rodadas_multiplas():
    """Garante que apenas a rodada mais recente esteja ativa"""
    rodadas_ativas = Rodada.objects.filter(ativa=True)
    
    if rodadas_ativas.count() > 1:
        print("🔧 CORRIGINDO: Múltiplas rodadas ativas encontradas...")
        
        # Encontra a rodada mais apropriada para estar ativa
        agora = timezone.now()
        
        # Primeiro tenta achar uma rodada em curso
        rodada_em_curso = rodadas_ativas.filter(
            data_inicio__lte=agora, 
            data_fim__gte=agora
        ).order_by('numero').first()
        
        if rodada_em_curso:
            rodada_escolhida = rodada_em_curso
            motivo = "está em curso"
        else:
            # Se não tem em curso, pega a próxima futura
            rodada_futura = rodadas_ativas.filter(data_inicio__gt=agora).order_by('numero').first()
            if rodada_futura:
                rodada_escolhida = rodada_futura
                motivo = "é a próxima futura"
            else:
                # Se não tem futura, pega a mais recente
                rodada_escolhida = rodadas_ativas.order_by('-numero').first()
                motivo = "é a mais recente"
        
        # Desativa todas
        Rodada.objects.filter(ativa=True).update(ativa=False)
        
        # Ativa apenas a escolhida
        rodada_escolhida.ativa = True
        rodada_escolhida.save()
        
        print(f"✅ Mantida ativa apenas: {rodada_escolhida} (porque {motivo})")
        print(f"❌ Desativadas: {rodadas_ativas.count() - 1} outras rodadas")
        
        return True
    return False

if __name__ == '__main__':
    diagnosticar_rodadas()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--corrigir':
        print()
        corrigir = input("Quer corrigir automaticamente? (s/N): ").lower().strip()
        if corrigir == 's':
            corrigir_rodadas_multiplas()
            print("\n" + "=" * 50)
            print("🔄 DIAGNÓSTICO APÓS CORREÇÃO:")
            print("=" * 50)
            diagnosticar_rodadas()