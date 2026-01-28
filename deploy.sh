#!/bin/bash
# FutAmigo - Deploy Script para Square Cloud
echo "🚀 FutAmigo - Deploy para Square Cloud"
echo "======================================"

# 1. Verificar se está em produção
echo "📋 Verificando configurações..."
python manage.py check --deploy

# 2. Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# 3. Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# 4. Aplicar migrações
echo "🗄️ Aplicando migrações..."
python manage.py migrate

# 5. Verificar se há superusuário
echo "👤 Para criar superusuário, execute:"
echo "python manage.py createsuperuser"

echo ""
echo "✅ Deploy preparado com sucesso!"
echo "🌐 Site: https://futamigo.squareweb.app"
echo "🔧 Admin: https://futamigo.squareweb.app/admin"
echo "🚀 Para executar: python manage.py runserver 0.0.0.0:80"

# Comando para rodar em produção no Square Cloud
echo ""
echo "📌 Square Cloud Configuration:"
echo "START=python manage.py runserver 0.0.0.0:80"