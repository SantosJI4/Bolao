#!/usr/bin/env python
"""
Script para criar uma atualização de exemplo demonstrando as novas funcionalidades
"""

import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from bolao.models import AtualizacaoSite

# Verifica se já existe uma atualização
if not AtualizacaoSite.objects.filter(versao='1.0').exists():
    atualizacao = AtualizacaoSite.objects.create(
        versao='1.0',
        titulo='Termos de Uso e Sistema de Atualizações',
        descricao='''🎉 Grandes novidades no FutAmigo!

📋 **Termos de Uso Oficiais**
• Agora você pode consultar os termos de uso completos do site
• Link disponível no footer da página
• Esclarece responsabilidades e regras importantes

🔔 **Sistema de Atualizações**
• Novo sistema de notificações para atualizações
• Pop-up automático mostra as novidades
• Histórico completo de todas as atualizações

⚠️ **Lembretes Importantes**
• O site NÃO se responsabiliza por erros de digitação
• Após fechamento do prazo, NÃO é possível alterar palpites
• Não insista em solicitar mudanças após o prazo

🔧 **Melhorias Gerais**
• Interface mais informativa
• Melhor comunicação com os usuários
• Links rápidos no footer da página

Desejamos uma ótima experiência a todos! ⚽''',
        ativa=True
    )
    print(f"✅ Atualização {atualizacao.versao} criada com sucesso!")
    print(f"📝 Título: {atualizacao.titulo}")
else:
    print("⚠️ Atualização 1.0 já existe!")