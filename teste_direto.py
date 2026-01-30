#!/usr/bin/env python3
import os
import sys
import django
import json
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('C:\\Users\\Maurício Santana\\Documents\\FUT')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
django.setup()

# Importar a função da view
from bolao.views import atualizar_placares_api

print("🚀 TESTANDO FUNÇÃO DIRETA - TEMPORADA 2026")
print("=" * 50)

try:
    # Simular um request
    class MockRequest:
        def __init__(self):
            pass
    
    mock_request = MockRequest()
    
    # Chamar função diretamente
    print("🔍 Executando atualizar_placares_api()...")
    resultado = atualizar_placares_api(mock_request)
    
    print(f"✅ Função executou com sucesso!")
    print(f"🎯 Tipo do resultado: {type(resultado)}")
    
    # Como é um JsonResponse, vamos extrair o conteúdo
    if hasattr(resultado, 'content'):
        import json
        data = json.loads(resultado.content.decode('utf-8'))
        
        print(f"📈 Success: {data.get('success', False)}")
        print(f"🎮 Jogos: {len(data.get('jogos', []))}")
        print(f"⏰ Última atualização: {data.get('ultima_atualizacao', 'N/A')}")
        print(f"🌐 Fonte: {data.get('fonte', 'N/A')}")
        
        if data.get('estatisticas'):
            stats = data['estatisticas']
            print(f"📊 Estatísticas:")
            print(f"   Total: {stats.get('total_jogos', 0)}")
            print(f"   Ao vivo: {stats.get('ao_vivo', 0)}")
            print(f"   Agendados: {stats.get('agendados', 0)}")
            print(f"   Finalizados: {stats.get('finalizados', 0)}")
        
        if data.get('error'):
            print(f"⚠️ Erro retornado: {data['error']}")
        
        if data.get('jogos'):
            print(f"\n🏆 PRIMEIROS JOGOS:")
            for idx, jogo in enumerate(data['jogos'][:2]):
                print(f"{idx+1}. {jogo.get('time_casa')} vs {jogo.get('time_visitante')}")
                print(f"   📊 {jogo.get('gols_casa', '-')} x {jogo.get('gols_visitante', '-')}")
                print(f"   ⏰ Status: {jogo.get('status', 'N/A')}")
        else:
            print("\n⚠️ Nenhum jogo retornado (normal para temporada 2026 recém iniciada)")
    
    else:
        print(f"📦 Resultado completo: {resultado}")
        
except Exception as e:
    print(f"💥 Erro ao executar função: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)

# Teste adicional: verificar se há jogos agendados na temporada 2026
print("\n🔍 TESTE ADICIONAL: Buscando todos os jogos da temporada 2026")

try:
    import requests
    
    headers = {
        'X-RapidAPI-Host': 'v3.football.api-sports.io',
        'X-RapidAPI-Key': 'b20093f89e13ee92bd30872fba5da1fe'
    }
    
    # Buscar todos os jogos da temporada 2026
    response = requests.get('https://v3.football.api-sports.io/fixtures', 
                           headers=headers,
                           params={
                               'league': '71',
                               'season': '2026'
                           })
    
    if response.status_code == 200:
        data = response.json()
        total_jogos = len(data.get('response', []))
        print(f"📊 Total de jogos na temporada 2026: {total_jogos}")
        
        if total_jogos > 0:
            print("✅ Temporada 2026 tem jogos!")
            # Mostrar primeiro jogo
            primeiro_jogo = data['response'][0]
            print(f"🏆 Primeiro jogo: {primeiro_jogo['teams']['home']['name']} vs {primeiro_jogo['teams']['away']['name']}")
            print(f"📅 Data: {primeiro_jogo['fixture']['date']}")
            print(f"⏰ Status: {primeiro_jogo['fixture']['status']['long']}")
        else:
            print("⚠️ Temporada 2026 ainda não tem jogos agendados")
    else:
        print(f"❌ Erro na API: {response.status_code}")
        
except Exception as e:
    print(f"💥 Erro no teste adicional: {e}")

print("=" * 50)