# 📊 Sistema de Analytics - FutAmigo

## O que foi implementado?

Um sistema completo de analytics que captura automaticamente:

### 🔍 **Dados Coletados**
- **Visitantes**: IP, dispositivo, navegador, localização
- **Sessões**: Duração, páginas visitadas, ações realizadas  
- **Ações**: Login, logout, palpites, visualizações
- **Performance**: Tempo de resposta das páginas
- **Dispositivos**: Mobile, tablet, desktop
- **Páginas populares**: Mais visitadas em tempo real

### 📱 **Painel Admin**
- **Dashboard em tempo real** com métricas atuais
- **Comparação** com dias anteriores
- **Usuários online** nos últimos 30 minutos  
- **Atividade recente** de todos os usuários
- **Estatísticas de dispositivos** e navegadores
- **Top usuários** mais ativos

## 🚀 Como usar?

### 1. **Instalar o Sistema**
```bash
# Execute o script de configuração
setup_analytics.bat

# OU manualmente:
pip install user-agents
python manage.py makemigrations bolao
python manage.py migrate
```

### 2. **Acessar o Dashboard**
- Entre no admin: `/admin/`
- Vá para: `/admin/analytics/`
- **Dashboard atualiza a cada 30 segundos automaticamente**

### 3. **Comandos Úteis**
```bash
# Calcular métricas do dia anterior (executar todo dia)
python manage.py calcular_metricas

# Resetar contadores de hoje
python manage.py calcular_metricas --reset-today

# Calcular métrica de data específica
python manage.py calcular_metricas --date 2026-02-07
```

## 📊 **Seções do Admin**

### **Sessões de Visitas**
- Lista todas as sessões dos usuários
- Mostra duração, dispositivo, páginas visitadas
- Filtros por data, dispositivo, usuário

### **Ações dos Usuários**  
- Cada clique/ação é registrada
- Tempo de resposta de cada página
- Filtros por tipo de ação, data

### **Métricas Diárias**
- Resumo agregado por dia
- Comparações entre períodos
- Estatísticas de dispositivos

### **Páginas Populares**
- Ranking de páginas mais acessadas
- Contadores diários e totais

## 🎯 **Principais Benefícios**

✅ **Visão completa** dos usuários  
✅ **Performance** em tempo real  
✅ **Comportamento** dos usuários  
✅ **Detectar problemas** rapidamente  
✅ **Otimizar** experiência do usuário  
✅ **Crescimento** do site monitorado  

## 🔧 **Configuração Automática**

O sistema já está **totalmente configurado**:
- ✅ Middleware ativo capturando dados
- ✅ Modelos criados no banco
- ✅ Admin configurado
- ✅ Dashboard funcionando
- ✅ APIs em tempo real

## ⚠️ **Importante**

- **Não rastreia** arquivos estáticos (/static/, /media/)
- **Não interfere** na performance do site
- **Dados sensíveis** não são capturados
- **GDPR compliant** - apenas dados técnicos

## 📈 **Automação Recomendada**

Configure um cron job para calcular métricas diárias:

```bash
# Todo dia às 01:00
0 1 * * * cd /path/to/project && python manage.py calcular_metricas
```

## 🎉 **Pronto para usar!**

Agora você tem um sistema de analytics profissional igual aos grandes sites!

**Acesse:** `/admin/analytics/` e veja a mágica acontecer! ✨