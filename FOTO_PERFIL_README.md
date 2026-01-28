# Funcionalidade de Foto de Perfil

## Descrição
Esta funcionalidade permite que os participantes do bolão adicionem fotos de perfil personalizadas às suas contas.

## Recursos Implementados

### 1. Campo de Foto no Modelo
- Adicionado campo `foto_perfil` no modelo `Participante`
- Upload automático para pasta `media/perfis/`
- Nomes de arquivo personalizados baseados no username

### 2. Formulário de Edição
- Formulário dedicado para edição de perfil (`PerfilParticipanteForm`)
- Validação de tamanho (máximo 5MB)
- Validação de tipo de arquivo (apenas imagens)
- Preview da imagem antes do upload

### 3. Templates Atualizados
- **Template de edição** (`editar_perfil.html`): Interface para upload e edição
- **Template de perfil** (`perfil.html`): Exibição da foto no perfil do participante
- **Template de classificação** (`classificacao.html`): Fotos em miniatura na tabela
- **Navbar**: Foto do usuário logado no menu dropdown

### 4. Processamento Automático de Imagens
- Redimensionamento automático para máximo 400x400 pixels
- Conversão para JPEG com qualidade otimizada
- Tratamento de diferentes formatos (RGBA, P)

### 5. Interface de Administração
- Preview das fotos na lista de participantes no Django Admin
- Campo de foto visível na edição de participantes

## Como Usar

### Para Participantes
1. Fazer login no sistema
2. Clicar no menu do usuário (canto superior direito)
3. Selecionar "Editar Perfil"
4. Fazer upload de uma nova foto de perfil
5. Salvar as alterações

### Para Administradores
1. Acessar o Django Admin
2. Navegar para "Participantes"
3. Editar qualquer participante
4. Fazer upload da foto de perfil diretamente

## Limitações Técnicas
- **Tamanho máximo**: 5MB por arquivo
- **Formatos aceitos**: JPG, PNG, GIF
- **Resolução máxima**: 400x400 pixels (redimensionamento automático)
- **Armazenamento**: Arquivos salvos em `media/perfis/`

## URLs Adicionadas
- `/perfil/editar/` - Formulário de edição de perfil

## Arquivos Modificados/Criados

### Novos Arquivos
- `bolao/forms.py` - Formulário de edição de perfil
- `bolao/templates/bolao/editar_perfil.html` - Template de edição

### Arquivos Modificados
- `bolao/models.py` - Campo foto_perfil e métodos de processamento
- `bolao/views.py` - View para editar perfil
- `bolao/urls.py` - Nova URL para edição
- `bolao/admin.py` - Preview de fotos no admin
- `bolao/templates/bolao/base.html` - Foto no menu navbar
- `bolao/templates/bolao/perfil.html` - Exibição da foto no perfil
- `bolao/templates/bolao/classificacao.html` - Fotos na classificação

### Migrações
- `0003_participante_foto_perfil.py` - Adiciona campo foto_perfil
- `0004_alter_participante_foto_perfil.py` - Atualiza função de upload

## Considerações de Segurança
- Validação rigorosa de tipos de arquivo
- Limitação de tamanho para evitar abuso
- Redimensionamento automático para economizar espaço
- Nomes de arquivo seguros baseados em username

## Melhorias Futuras Possíveis
- Crop manual de imagens
- Múltiplos tamanhos de thumbnail
- Integração com avatars externos (Gravatar)
- Histórico de fotos anteriores
- Moderação de conteúdo automática