"""
Configuração para APIs de futebol ao vivo

Para configurar uma API real:
1. Escolha uma das APIs gratuitas abaixo
2. Registre-se e obtenha uma chave
3. Substitua 'YOUR_API_KEY_HERE' pela sua chave real
4. Descomente o código da API escolhida na view

APIs Gratuitas Recomendadas:

1. Football-Data.org
   - 10 requisições/minuto grátis
   - URL: https://www.football-data.org/
   - Exemplo de chave: 'abc123def456'
   
2. API-Sports (RapidAPI)
   - 100 requisições/dia grátis
   - URL: https://rapidapi.com/api-sports/api/api-football
   - Header: X-RapidAPI-Key
   
3. OpenLiga-DB (grátis, alemão)
   - Totalmente gratuita
   - URL: https://www.openligadb.de/
   
4. TheSportsDB (grátis)
   - 1000 requisições/mês
   - URL: https://www.thesportsdb.com/

CONFIGURAÇÕES ATUAIS:
- Cache: 2 minutos (120 segundos)
- Auto-atualização: 30 segundos no frontend
- Backup cache: Ativado
- Simulação: Dados brasileiros fictícios
"""

# Configurações da API
API_SETTINGS = {
    'FOOTBALL_DATA_ORG': {
        'url': 'https://api.football-data.org/v4/matches',
        'key': 'YOUR_API_KEY_HERE',  # Substitua pela sua chave
        'headers': {'X-Auth-Token': 'YOUR_API_KEY_HERE'},
        'free_limit': '10 req/min',
    },
    
    'API_SPORTS': {
        'url': 'https://v3.football.api-sports.io/fixtures',
        'key': 'YOUR_API_KEY_HERE',  # Substitua pela sua chave
        'headers': {
            'X-RapidAPI-Key': 'YOUR_API_KEY_HERE',
            'X-RapidAPI-Host': 'v3.football.api-sports.io'
        },
        'free_limit': '100 req/day',
    }
}

# Configurações de cache
CACHE_SETTINGS = {
    'PLACARES_TIMEOUT': 120,  # 2 minutos
    'BACKUP_TIMEOUT': 3600,   # 1 hora para backup
    'AUTO_REFRESH': 30,       # 30 segundos no frontend
}

# IDs de competições populares (Football-Data.org)
COMPETICOES_IDS = {
    'PREMIER_LEAGUE': 2021,
    'CHAMPIONSHIP': 2016,
    'LA_LIGA': 2014,
    'BUNDESLIGA': 2002,
    'SERIE_A': 2019,
    'LIGUE_1': 2015,
    'CHAMPIONS_LEAGUE': 2001,
    'COPA_LIBERTADORES': 2152,
}

# Instruções de instalação
INSTALL_INSTRUCTIONS = """
Para ativar API real:

1. Instale requests (já incluído no requirements.txt):
   pip install requests

2. Registre-se em uma das APIs gratuitas acima

3. No arquivo views.py, substitua 'YOUR_API_KEY_HERE' pela sua chave

4. Descomente o código da API na função atualizar_placares_api()

5. Comente ou remova a seção de dados simulados

Exemplo Football-Data.org:
headers = {'X-Auth-Token': 'SUA_CHAVE_AQUI'}

Exemplo API-Sports:
headers = {
    'X-RapidAPI-Key': 'SUA_CHAVE_AQUI',
    'X-RapidAPI-Host': 'v3.football.api-sports.io'
}
"""