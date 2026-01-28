# 🏆 Bolão Brasileirão

Sistema completo de bolão para palpites do Campeonato Brasileiro Série A, desenvolvido em Django.

## 📋 Funcionalidades

### Para o Administrador
- **Painel administrativo completo** para gerenciar participantes, times, rodadas e jogos
- **Cadastro automático de usuários** para participantes
- **Inserção de resultados** dos jogos com cálculo automático de pontos
- **Gestão de rodadas** (ativar/desativar para palpites)
- **Atualização automática da classificação** após cada resultado inserido
- **Visualização detalhada** de palpites e estatísticas

### Para os Participantes
- **Interface moderna e responsiva** com design casual
- **Sistema de login** personalizado
- **Palpites por rodada** (Vitória Casa, Empate, Vitória Visitante)
- **Classificação em tempo real** com posicionamento
- **Histórico de resultados** com feedback visual
- **Perfil detalhado** com estatísticas pessoais

## 🎯 Sistema de Pontuação

- **Empate correto**: 1 ponto
- **Resultado correto** (vitória): 3 pontos  
- **Palpite errado**: 0 pontos

## 🚀 Como Usar

### 1. Acesso Administrativo
```
URL: http://127.0.0.1:8000/admin/
Usuário: admin
Senha: admin123
```

#### No painel admin você pode:
1. **Cadastrar participantes**: Criar usuários e vincular ao bolão
2. **Gerenciar times**: Cadastrar os 20 times com escudos
3. **Criar rodadas**: Definir datas e ativar para palpites
4. **Cadastrar jogos**: 10 confrontos por rodada
5. **Inserir resultados**: Placar final que calcula pontos automaticamente

### 2. Acesso dos Participantes
```
URL: http://127.0.0.1:8000/
Participantes de exemplo:
- joao / 123456
- maria / 123456  
- carlos / 123456
- ana / 123456
- pedro / 123456
```

#### Como participante você pode:
1. **Fazer palpites**: Na rodada ativa, escolher resultado de cada jogo
2. **Ver classificação**: Posição atual e estatísticas detalhadas
3. **Acompanhar resultados**: Histórico com seus acertos e erros
4. **Visualizar perfil**: Suas estatísticas e aproveitamento

## 🛠️ Configuração do Projeto

### Pré-requisitos
- Python 3.8+
- Ambiente virtual (venv)

### Instalação
```bash
# 1. Clone/baixe o projeto
cd "c:\Users\Maurício Santana\Documents\FUT"

# 2. Ative o ambiente virtual
.\venv\Scripts\Activate.ps1

# 3. Instale dependências (já instaladas)
pip install -r requirements.txt

# 4. Execute migrações (já executadas)
python manage.py migrate

# 5. Popule banco de dados (já executado)
python popular_banco.py

# 6. Inicie o servidor
python manage.py runserver
```

### Acessos
- **Site principal**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/

## 📱 Interface do Sistema

### Página Inicial
- **Rodada atual**: Destacada com botão para palpitar
- **Próximas rodadas**: Listadas como bloqueadas
- **Resultados recentes**: Links para ver detalhes
- **Widget classificação**: Posição atual do usuário

### Palpites
- **Formulário intuitivo**: Radio buttons para cada jogo
- **Visualização clara**: Times com escudos e data/hora
- **Salvamento flexível**: Pode alterar até o prazo final
- **Feedback visual**: Palpites já registrados destacados

### Classificação
- **Tabela completa**: Posição, pontos, acertos, aproveitamento
- **Pódio destacado**: Top 3 com ícones especiais
- **Estatísticas**: Total de participantes e jogos
- **Atualização automática**: Sempre que há novos resultados

### Resultados
- **Comparação visual**: Seu palpite vs resultado real
- **Feedback claro**: Acertos em verde, erros em vermelho
- **Resumo da rodada**: Total de pontos ganhos
- **Estatísticas**: Aproveitamento percentual

## 🎨 Design

- **Cores neutras**: Preto, branco e tons de cinza
- **Design casual**: Interface amigável e moderna
- **Responsivo**: Funciona bem em desktop e mobile
- **Bootstrap 5**: Framework CSS moderno
- **Font Awesome**: Ícones consistentes
- **Animações suaves**: Hover e transições

## ⚙️ Tecnologias

- **Backend**: Django 6.0.1
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Banco de dados**: SQLite (desenvolvimento)
- **Imagens**: Pillow para upload de escudos
- **Templates**: Django Template Language

## 📊 Models do Sistema

### Time
- Nome, sigla, escudo

### Participante  
- Usuário Django vinculado
- Nome de exibição, status ativo

### Rodada
- Número, nome, datas, status ativo

### Jogo
- Times, data/hora, resultado, status

### Palpite
- Participante, jogo, resultado apostado

### Classificação
- Posição, pontos, estatísticas detalhadas

## 🔧 Funcionalidades Técnicas

### Admin Customizado
- **Inlines**: Edição de jogos dentro das rodadas
- **Actions**: Ativar/desativar rodadas em lote
- **Filtros**: Por data, status, participante
- **Visual**: Cores e ícones para status
- **Automação**: Atualização de classificação

### Sistema de Pontos
- **Cálculo automático**: Property nos models
- **Atualização em tempo real**: Signals do Django
- **Classificação inteligente**: Ordenação por pontos

### Interface Responsiva
- **Mobile-first**: Design adaptável
- **Cards**: Layout modular
- **Feedback visual**: Estados claros
- **Navegação intuitiva**: Breadcrumbs e botões

## 📝 Próximas Melhorias

- [ ] Sistema de notificações por email
- [ ] API REST para mobile app
- [ ] Chat entre participantes
- [ ] Estatísticas avançadas e gráficos
- [ ] Sistema de premiação
- [ ] Integração com resultados externos
- [ ] Backup automático
- [ ] Modo escuro

## 🤝 Suporte

Para dúvidas ou problemas:
1. Verifique as credenciais de acesso
2. Confirme se o servidor está rodando
3. Consulte os logs no terminal
4. Reinicie o servidor se necessário

---

**Desenvolvido com Django e muito ☕**