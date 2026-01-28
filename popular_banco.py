import os
import sys
import django

# Configura o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
django.setup()

from django.contrib.auth.models import User
from bolao.models import Time, Participante, Rodada, Jogo
from datetime import datetime, timedelta
from django.utils import timezone

def criar_times():
    """Cria os 20 times do Brasileirão Série A"""
    times_brasileirao = [
        {'nome': 'Flamengo', 'sigla': 'FLA'},
        {'nome': 'Palmeiras', 'sigla': 'PAL'},
        {'nome': 'São Paulo', 'sigla': 'SAO'},
        {'nome': 'Corinthians', 'sigla': 'COR'},
        {'nome': 'Santos', 'sigla': 'SAN'},
        {'nome': 'Grêmio', 'sigla': 'GRE'},
        {'nome': 'Internacional', 'sigla': 'INT'},
        {'nome': 'Fluminense', 'sigla': 'FLU'},
        {'nome': 'Botafogo', 'sigla': 'BOT'},
        {'nome': 'Vasco da Gama', 'sigla': 'VAS'},
        {'nome': 'Atlético Mineiro', 'sigla': 'CAM'},
        {'nome': 'Cruzeiro', 'sigla': 'CRU'},
        {'nome': 'Bahia', 'sigla': 'BAH'},
        {'nome': 'Vitória', 'sigla': 'VIT'},
        {'nome': 'Fortaleza', 'sigla': 'FOR'},
        {'nome': 'Ceará', 'sigla': 'CEA'},
        {'nome': 'Atlético Paranaense', 'sigla': 'CAP'},
        {'nome': 'Coritiba', 'sigla': 'CFC'},
        {'nome': 'Bragantino', 'sigla': 'BRA'},
        {'nome': 'Cuiabá', 'sigla': 'CUI'},
    ]
    
    times_criados = []
    for time_data in times_brasileirao:
        time, created = Time.objects.get_or_create(
            nome=time_data['nome'],
            defaults={'sigla': time_data['sigla']}
        )
        if created:
            print(f"Time criado: {time.nome}")
        times_criados.append(time)
    
    return times_criados

def criar_superuser():
    """Cria o superusuário admin"""
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@bolao.com',
            password='admin123'
        )
        print(f"Superusuário criado: {admin.username}")
        return admin
    else:
        print("Superusuário 'admin' já existe.")
        return User.objects.get(username='admin')

def criar_participantes_exemplo():
    """Cria alguns participantes de exemplo"""
    participantes_exemplo = [
        {'username': 'joao', 'nome': 'João Silva'},
        {'username': 'maria', 'nome': 'Maria Santos'},
        {'username': 'carlos', 'nome': 'Carlos Oliveira'},
        {'username': 'ana', 'nome': 'Ana Costa'},
        {'username': 'pedro', 'nome': 'Pedro Almeida'},
    ]
    
    participantes_criados = []
    for part_data in participantes_exemplo:
        if not User.objects.filter(username=part_data['username']).exists():
            user = User.objects.create_user(
                username=part_data['username'],
                password='123456',
                first_name=part_data['nome'].split()[0],
                last_name=' '.join(part_data['nome'].split()[1:])
            )
            
            participante = Participante.objects.create(
                user=user,
                nome_exibicao=part_data['nome'],
                ativo=True
            )
            print(f"Participante criado: {participante.nome_exibicao}")
            participantes_criados.append(participante)
    
    return participantes_criados

def criar_rodada_exemplo(times):
    """Cria uma rodada de exemplo"""
    # Verifica se já existe uma rodada
    if Rodada.objects.exists():
        print("Já existem rodadas no sistema.")
        return
    
    # Cria a primeira rodada
    rodada = Rodada.objects.create(
        numero=1,
        nome="1ª Rodada",
        data_inicio=timezone.now(),
        data_fim=timezone.now() + timedelta(days=7),
        ativa=True
    )
    
    # Cria alguns jogos de exemplo (5 jogos para a rodada)
    jogos_exemplo = [
        (times[0], times[1]),  # Flamengo x Palmeiras
        (times[2], times[3]),  # São Paulo x Corinthians
        (times[4], times[5]),  # Santos x Grêmio
        (times[6], times[7]),  # Internacional x Fluminense
        (times[8], times[9]),  # Botafogo x Vasco
    ]
    
    for i, (time_casa, time_visitante) in enumerate(jogos_exemplo):
        data_jogo = timezone.now() + timedelta(days=1, hours=i*2)
        
        jogo = Jogo.objects.create(
            rodada=rodada,
            time_casa=time_casa,
            time_visitante=time_visitante,
            data_hora=data_jogo
        )
        print(f"Jogo criado: {jogo}")
    
    print(f"Rodada criada: {rodada}")

def main():
    print("🏆 Populando banco de dados do FutAmigo...")
    print("=" * 50)
    
    # Cria superusuário
    admin = criar_superuser()
    
    # Cria times
    print("\n📋 Criando times...")
    times = criar_times()
    
    # Cria participantes de exemplo
    print("\n👥 Criando participantes de exemplo...")
    participantes = criar_participantes_exemplo()
    
    # Cria rodada de exemplo
    print("\n⚽ Criando rodada de exemplo...")
    criar_rodada_exemplo(times)
    
    print("\n" + "=" * 50)
    print("✅ Banco de dados populado com sucesso!")
    print("\n🔑 CREDENCIAIS DE ACESSO:")
    print("   Admin: username=admin, password=admin123")
    print("   Participantes: username=joao/maria/carlos/ana/pedro, password=123456")
    print("\n🌐 Para iniciar o servidor:")
    print("   python manage.py runserver")
    print("\n📝 Acesse o admin em: http://127.0.0.1:8000/admin/")

if __name__ == '__main__':
    main()