#!/usr/bin/env python
"""
Script auxiliar para criar novas atualizações no FutAmigo
Uso: python criar_atualizacao.py
"""

import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from bolao.models import AtualizacaoSite

def criar_atualizacao():
    print("🚀 Criador de Atualizações - FutAmigo")
    print("=" * 40)
    
    # Pega a última versão para sugerir a próxima
    ultima_atualizacao = AtualizacaoSite.objects.order_by('-data_lancamento').first()
    if ultima_atualizacao:
        print(f"📋 Última versão: {ultima_atualizacao.versao}")
        
        # Tenta sugerir próxima versão
        try:
            partes = ultima_atualizacao.versao.split('.')
            if len(partes) == 2:
                maior = int(partes[0])
                menor = int(partes[1]) + 1
                versao_sugerida = f"{maior}.{menor}"
            else:
                versao_sugerida = "1.1"
        except:
            versao_sugerida = "1.1"
            
        print(f"💡 Sugestão para próxima: {versao_sugerida}")
    else:
        versao_sugerida = "1.0"
        print("📋 Esta será a primeira atualização!")
    
    print()
    
    # Coleta dados
    versao = input(f"📝 Versão (sugestão: {versao_sugerida}): ").strip() or versao_sugerida
    
    if AtualizacaoSite.objects.filter(versao=versao).exists():
        print(f"❌ Erro: Versão {versao} já existe!")
        return
    
    titulo = input("📝 Título da atualização: ").strip()
    if not titulo:
        print("❌ Erro: Título é obrigatório!")
        return
    
    print("📝 Descrição (digite linha por linha, linha vazia para finalizar):")
    linhas_descricao = []
    while True:
        linha = input("   > ")
        if not linha.strip():
            break
        linhas_descricao.append(linha)
    
    if not linhas_descricao:
        print("❌ Erro: Descrição é obrigatória!")
        return
    
    descricao = '\n'.join(linhas_descricao)
    
    ativa = input("📝 Ativar imediatamente? (S/n): ").strip().lower()
    ativa = ativa != 'n'
    
    print()
    print("📋 Resumo da atualização:")
    print(f"   Versão: {versao}")
    print(f"   Título: {titulo}")
    print(f"   Ativa: {'Sim' if ativa else 'Não'}")
    print(f"   Descrição:")
    for linha in linhas_descricao:
        print(f"      {linha}")
    
    print()
    confirma = input("✅ Confirma a criação? (S/n): ").strip().lower()
    if confirma == 'n':
        print("❌ Operação cancelada!")
        return
    
    # Cria a atualização
    try:
        atualizacao = AtualizacaoSite.objects.create(
            versao=versao,
            titulo=titulo,
            descricao=descricao,
            ativa=ativa
        )
        
        print(f"✅ Atualização {versao} criada com sucesso!")
        print(f"📅 Data: {atualizacao.data_lancamento.strftime('%d/%m/%Y %H:%M')}")
        print(f"🔔 Status: {'Ativa' if ativa else 'Inativa'}")
        
        if ativa:
            print("💡 A atualização aparecerá para usuários que não a viram!")
        else:
            print("💡 Para ativar, acesse o admin e marque como 'Ativa'")
            
    except Exception as e:
        print(f"❌ Erro ao criar atualização: {e}")

if __name__ == "__main__":
    criar_atualizacao()