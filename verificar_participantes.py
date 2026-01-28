import os
import sys
import django

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
django.setup()

from django.contrib.auth.models import User
from bolao.models import Participante

def criar_participante_admin():
    """Cria participante para o usuário admin se não existir"""
    try:
        admin = User.objects.get(username='admin')
        try:
            participante = admin.participante
            print(f"✅ Participante do admin já existe: {participante.nome_exibicao}")
        except Participante.DoesNotExist:
            participante = Participante.objects.create(
                user=admin,
                nome_exibicao="Administrador",
                ativo=True
            )
            print(f"✅ Participante criado para admin: {participante.nome_exibicao}")
    except User.DoesNotExist:
        print("❌ Usuário admin não encontrado")

def verificar_participantes():
    """Verifica todos os participantes existentes"""
    print("\n📋 Participantes cadastrados:")
    participantes = Participante.objects.all()
    
    if participantes:
        for p in participantes:
            print(f"  - {p.nome_exibicao} (usuário: {p.user.username})")
    else:
        print("  Nenhum participante encontrado")

def main():
    print("🔧 Verificando e criando participantes...")
    print("=" * 50)
    
    criar_participante_admin()
    verificar_participantes()
    
    print("\n" + "=" * 50)
    print("✅ Verificação concluída!")

if __name__ == '__main__':
    main()