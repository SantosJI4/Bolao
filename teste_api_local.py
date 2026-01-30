import requests
import time

print("🚀 TESTANDO API LOCAL COM TEMPORADA 2026")
print("=" * 50)

# Aguardar servidor inicializar
print("⏳ Aguardando servidor inicializar...")
time.sleep(3)

try:
    # Testar API local
    print("🔍 Testando endpoint: /api/atualizar-placares/")
    response = requests.get('http://127.0.0.1:8001/api/atualizar-placares/', timeout=15)
    
    print(f"📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API Local respondeu com sucesso!")
        
        print(f"🎯 Success: {data.get('success', False)}")
        print(f"📈 Jogos retornados: {len(data.get('jogos', []))}")
        print(f"⏰ Última atualização: {data.get('ultima_atualizacao', 'N/A')}")
        print(f"📅 Próxima atualização: {data.get('proxima_atualizacao', 'N/A')}")
        print(f"🌐 Fonte: {data.get('fonte', 'N/A')}")
        
        # Estatísticas se disponível
        if data.get('estatisticas'):
            stats = data['estatisticas']
            print(f"📊 Estatísticas:")
            print(f"   📋 Total de jogos: {stats.get('total_jogos', 0)}")
            print(f"   🔴 Ao vivo: {stats.get('ao_vivo', 0)}")
            print(f"   ⏰ Agendados: {stats.get('agendados', 0)}")
            print(f"   ✅ Finalizados: {stats.get('finalizados', 0)}")
        
        # Mostrar jogos se houver
        if data.get('jogos'):
            print("\n🏆 JOGOS ENCONTRADOS:")
            for idx, jogo in enumerate(data['jogos'][:3]):  # Primeiros 3
                print(f"\n{idx+1}. {jogo.get('time_casa', 'N/A')} vs {jogo.get('time_visitante', 'N/A')}")
                print(f"   📊 Placar: {jogo.get('gols_casa', '-')} x {jogo.get('gols_visitante', '-')}")
                print(f"   ⏰ Status: {jogo.get('status', 'N/A')}")
                print(f"   🏟️ Estádio: {jogo.get('estadio', 'N/A')}")
                print(f"   📅 Data: {jogo.get('horario', 'N/A')}")
        else:
            print("\n⚠️ Nenhum jogo encontrado (normal - temporada 2026 ainda não tem jogos agendados)")
            
    else:
        print(f"❌ Erro na API Local: {response.status_code}")
        try:
            error_data = response.json()
            print(f"🔍 Erro detalhado: {error_data}")
        except:
            print(f"🔍 Resposta: {response.text[:500]}...")
            
except requests.exceptions.ConnectionError:
    print("❌ Servidor Django não está rodando em http://127.0.0.1:8001")
    print("💡 Execute: python manage.py runserver 8001")
    
except requests.exceptions.Timeout:
    print("⏰ Timeout na requisição - servidor pode estar sobrecarregado")
    
except Exception as e:
    print(f"💥 Erro inesperado: {e}")

print("\n" + "=" * 50)