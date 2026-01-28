# Production deployment checklist
echo "🚀 FutAmigo - Deploy Checklist"
echo "================================"

# 1. Instalar dependências
pip install -r requirements.txt

# 2. Coletar arquivos estáticos
python manage.py collectstatic --noinput

# 3. Aplicar migrações
python manage.py migrate

# 4. Criar superusuário (se necessário)
# python manage.py createsuperuser

# 5. Verificar configurações
python manage.py check --deploy

echo "✅ Deploy preparado com sucesso!"
echo "🌐 Site: https://futamigo.squareweb.app"
echo "🔧 Admin: https://futamigo.squareweb.app/admin"