import requests

print("🔍 DIAGNÓSTICO DA API DE JOGOS AO VIVO")
print("=" * 50)

# 1. Testar API Externa
print("\n1. Testando API Externa (api-football)...")
try:
    headers = {
        'X-RapidAPI-Host': 'v3.football.api-sports.io',
        'X-RapidAPI-Key': 'b20093f89e13ee92bd30872fba5da1fe'
    }
    
    response = requests.get(
        'https://v3.football.api-sports.io/fixtures',
        headers=headers,
        params={'league': '71', 'season': '2026'},
        timeout=10
    )
    
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Externa funcionando!")
        print(f"🎯 Jogos encontrados: {len(data.get('response', []))}")
        print(f"📈 Requests restantes: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
    else:
        print(f"❌ Erro na API Externa: {response.status_code}")
        print(f"🔍 Resposta: {response.text[:200]}")

except Exception as e:
    print(f"💥 Erro ao conectar na API Externa: {e}")

# 2. Testar API Local do Django
print("\n2. Testando API Local (Django)...")
try:
    response = requests.get('http://127.0.0.1:8000/api/atualizar-placares/', timeout=5)
    
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Local funcionando!")
        print(f"🎯 Success: {data.get('success')}")
        print(f"🎮 Jogos: {len(data.get('jogos', []))}")
        print(f"⏰ Última atualização: {data.get('ultima_atualizacao')}")
        print(f"🌐 Fonte: {data.get('fonte')}")
        
        if data.get('error'):
            print(f"⚠️ Erro retornado: {data['error']}")
    else:
        print(f"❌ Erro na API Local: {response.status_code}")
        print(f"🔍 Resposta: {response.text[:200]}")

except requests.exceptions.ConnectionError:
    print("❌ Servidor Django não está acessível")
    print("💡 Verifique se o servidor está rodando em http://127.0.0.1:8000")

except Exception as e:
    print(f"💥 Erro ao conectar na API Local: {e}")

# 3. Testar diferentes temporadas
print("\n3. Testando temporadas alternativas...")
try:
    headers = {
        'X-RapidAPI-Host': 'v3.football.api-sports.io',
        'X-RapidAPI-Key': 'b20093f89e13ee92bd30872fba5da1fe'
    }
    
    for temporada in ['2024', '2025', '2026']:
        response = requests.get(
            'https://v3.football.api-sports.io/fixtures',
            headers=headers,
            params={'league': '71', 'season': temporada},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            jogos_count = len(data.get('response', []))
            print(f"📅 Temporada {temporada}: {jogos_count} jogos")
        else:
            print(f"❌ Erro na temporada {temporada}: {response.status_code}")

except Exception as e:
    print(f"💥 Erro ao testar temporadas: {e}")

print("\n" + "=" * 50)
print("🎯 RESUMO DO DIAGNÓSTICO:")
print("- Verifique se o servidor Django está rodando")
print("- Confirme se a API externa está acessível")
print("- Temporada 2026 pode não ter jogos agendados ainda")
print("=" * 50)