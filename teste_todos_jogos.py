import requests

# Buscar todos os jogos da temporada 2024 (sem filtrar por data)
headers = {
    'X-RapidAPI-Host': 'v3.football.api-sports.io',
    'X-RapidAPI-Key': 'b20093f89e13ee92bd30872fba5da1fe'
}

print("🔍 BUSCANDO TODOS OS JOGOS DA TEMPORADA 2024")
print("=" * 50)

response = requests.get('https://v3.football.api-sports.io/fixtures', 
                       headers=headers,
                       params={
                           'league': '71',
                           'season': '2024'
                           # Sem filtro de data - todos os jogos
                       })

if response.status_code == 200:
    data = response.json()
    jogos_count = len(data.get('response', []))
    
    print(f"🎯 Total de jogos na temporada 2024: {jogos_count}")
    
    if jogos_count > 0:
        print("\n✅ EXEMPLOS DE JOGOS ENCONTRADOS:")
        
        # Mostrar alguns jogos como exemplo
        for idx, jogo in enumerate(data['response'][:5]):  # Primeiros 5 jogos
            home = jogo['teams']['home']['name']
            away = jogo['teams']['away']['name']
            status = jogo['fixture']['status']['long']
            status_short = jogo['fixture']['status']['short']
            goals_home = jogo['goals']['home']
            goals_away = jogo['goals']['away']
            date = jogo['fixture']['date'][:10]  # Apenas a data
            
            print(f"\n{idx+1}. 🏆 {home} vs {away}")
            print(f"   📊 {goals_home} x {goals_away}")
            print(f"   ⏰ {status} ({status_short})")
            print(f"   📅 {date}")
        
        print(f"\n... e mais {jogos_count - 5} jogos")
        
        # Testar nossa função de conversão de dados
        print("\n🔧 TESTANDO CONVERSÃO DE DADOS:")
        jogo_exemplo = data['response'][0]
        
        # Simular conversão como nossa view faz
        jogo_convertido = {
            'id': jogo_exemplo['fixture']['id'],
            'time_casa': jogo_exemplo['teams']['home']['name'],
            'time_visitante': jogo_exemplo['teams']['away']['name'],
            'gols_casa': jogo_exemplo['goals']['home'],
            'gols_visitante': jogo_exemplo['goals']['away'],
            'status': jogo_exemplo['fixture']['status']['short'],
            'minuto': jogo_exemplo['fixture']['status']['elapsed'],
            'competicao': 'Brasileirão Série A',
            'rodada': f"Rodada {jogo_exemplo['league']['round'].split(' ')[-1] if 'Regular Season' in jogo_exemplo['league']['round'] else jogo_exemplo['league']['round']}",
            'horario': jogo_exemplo['fixture']['date'],
            'estadio': jogo_exemplo['fixture']['venue']['name'],
            'cidade': jogo_exemplo['fixture']['venue']['city']
        }
        
        print("📦 Dados convertidos:")
        for key, value in jogo_convertido.items():
            print(f"   {key}: {value}")
            
    else:
        print("❌ Nenhum jogo encontrado")
else:
    print(f"❌ Erro {response.status_code}: {response.text}")

print(f"\n📊 Requisições restantes: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
print("=" * 50)