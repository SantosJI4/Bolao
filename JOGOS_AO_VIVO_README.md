# 📺 Sistema de Jogos Ao Vivo - FutAmigo

Nova funcionalidade que mostra placares e estatísticas em tempo real com sistema inteligente de cache para economizar requisições de API.

## ✨ Funcionalidades

### 🔥 **Principais Recursos:**
- **Placares em tempo real** com auto-atualização a cada 30 segundos
- **Sistema de cache inteligente** (2 minutos) para economizar requisições
- **Filtros inteligentes**: Todos, Ao Vivo, Agendados, Finalizados
- **Interface responsiva** com animações e badges pulsando
- **Dados simulados** do Brasileirão para teste (Flamengo x Palmeiras, etc.)

### 📱 **Interface Moderna:**
- Badge "LIVE" pulsando no menu principal
- Cards de jogos com status coloridos
- Escudos dos times quando disponíveis
- Auto-atualização silenciosa em background
- Animações suaves e efeitos visuais

## 🎛️ **Como Funciona:**

### **Cache Inteligente:**
```
Primeira requisição → API → Cache (2 min) → Usuário
Requisições seguintes → Cache → Usuário (sem API)
Cache expirou → Nova requisição API → Atualiza cache
```

### **Economia de Requisições:**
- ✅ **Cache de 2 minutos**: Múltiplos usuários usam mesmos dados
- ✅ **Auto-refresh de 30s**: Interface sempre atualizada
- ✅ **Cache de backup**: Funciona mesmo se API falhar
- ✅ **Requisições mínimas**: Ideal para APIs gratuitas

## 🔗 **APIs Suportadas:**

### **1. Football-Data.org** (Recomendada)
- 🟢 **10 requisições/minuto grátis**
- 📝 Registro: https://www.football-data.org/
- 🏆 Competições: Premier League, La Liga, Champions, etc.

### **2. API-Sports (RapidAPI)**
- 🟡 **100 requisições/dia grátis** 
- 📝 Registro: https://rapidapi.com/api-sports/api/api-football
- 🏆 Competições: Todas as principais ligas

### **3. Dados Simulados** (Atual)
- 🟢 **Totalmente grátis**
- 🇧🇷 Times brasileiros (Flamengo, Palmeiras, etc.)
- ⚡ Funciona sem configuração

## ⚙️ **Configuração de API Real:**

### **Passo 1: Escolher API**
```python
# No arquivo config_apis.py, veja as opções disponíveis
```

### **Passo 2: Obter Chave**
1. Registre-se no site da API escolhida
2. Confirme email e obtenha a chave
3. Anote o limite gratuito

### **Passo 3: Configurar no Código**
```python
# No arquivo bolao/views.py, na função atualizar_placares_api()

# SUBSTITUIR esta linha:
'X-Auth-Token': 'YOUR_API_KEY_HERE'

# POR sua chave real:
'X-Auth-Token': 'SUA_CHAVE_AQUI_123ABC'
```

### **Passo 4: Ativar API**
```python
# Descomentar estas linhas na view:
response = requests.get(API_URL, headers=headers, params=params, timeout=10)
if response.status_code == 200:
    data = response.json()
    jogos_api = data.get('matches', [])

# Comentar a seção de dados simulados:
# jogos_simulados = [...]
```

## 📊 **Estrutura de Dados:**

### **Jogo Object:**
```json
{
    "id": 1,
    "time_casa": "Flamengo",
    "time_visitante": "Palmeiras", 
    "escudo_casa": "/media/escudos/flamengo.png",
    "escudo_visitante": "/media/escudos/palmeiras.png",
    "gols_casa": 2,
    "gols_visitante": 1,
    "status": "LIVE",
    "minuto": 67,
    "competicao": "Brasileirão Série A",
    "horario": "2026-01-30T15:00:00Z",
    "ao_vivo": true
}
```

### **Status Possíveis:**
- `LIVE` / `IN_PLAY`: Jogo acontecendo agora
- `PAUSED`: Intervalo  
- `SCHEDULED` / `TIMED`: Agendado para o futuro
- `FINISHED`: Finalizado

## 🎨 **Personalização:**

### **Cores e Animações:**
```css
/* Badge Live pulsando */
.live-badge {
    animation: pulse-live-badge 2s infinite;
}

/* Cards de status */
.jogo-card.ao-vivo { border-color: #dc3545; }
.jogo-card.agendado { border-color: #ffc107; }
.jogo-card.finalizado { opacity: 0.8; }
```

### **Intervalos de Atualização:**
```javascript
// Arquivo: jogos_ao_vivo.html
const AUTO_REFRESH = 30000; // 30 segundos
const CACHE_TIMEOUT = 120;  // 2 minutos (backend)
```

## 🚀 **Performance:**

### **Otimizações Implementadas:**
- **Cache Django** para reduzir requisições API
- **AJAX requests** para atualizações sem reload  
- **Lazy loading** de imagens de escudos
- **Debounce** em filtros para evitar spam
- **Error fallback** para cache de backup

### **Limites Respeitados:**
- **API Gratuita**: Máximo requisições respeitado
- **Cache Backend**: 2 minutos para múltiplos users
- **Frontend**: Auto-refresh inteligente
- **Backup Cache**: 1 hora para emergências

## 🎯 **Casos de Uso:**

### **Durante um Jogo:**
1. Usuário entra na aba "Ao Vivo"
2. Vê placares atualizados automaticamente  
3. Badge "LIVE" indica jogos em andamento
4. Filtros permitem focar em jogos específicos

### **Planejamento:**
1. Filtro "Agendados" mostra próximos jogos
2. Horários localizados em português
3. Times e competições claramente identificados

### **Resultados:**
1. Filtro "Finalizados" mostra jogos terminados
2. Placares finais com badge "FINAL"
3. Histórico preservado durante o cache

## 🔧 **Troubleshooting:**

### **Problema: API não funciona**
```
Solução: Verificar chave API e limites
Status: Dados simulados como fallback
```

### **Problema: Placares não atualizam**  
```
Solução: Verificar cache e conexão
Status: Botão "Atualizar" manual disponível
```

### **Problema: Imagens não carregam**
```
Solução: URLs de escudos podem estar quebradas
Status: Ícones padrão como fallback
```

## 📈 **Estatísticas de Economia:**

### **Sem Cache (Problemático):**
- 10 usuários × 30s = 20 req/min
- Limite API estourado rapidamente ❌

### **Com Cache (Otimizado):**
- 1 requisição → 10 usuários por 2 min
- 0.5 req/min efetivas ✅

### **Resultado:**
- 💰 **97% economia** de requisições
- ⚡ **Interface sempre rápida**  
- 🔋 **API dura o mês todo**

---

## 🎉 **Funcionalidade Completa!**

A aba **"Ao Vivo"** está pronta e funcionando com:
- ✅ Interface moderna e responsiva
- ✅ Sistema de cache inteligente  
- ✅ Dados simulados funcionando
- ✅ Preparado para APIs reais
- ✅ Auto-atualização suave
- ✅ Filtros e animações

**Pronto para usar e impressionar! ⚽🔥**