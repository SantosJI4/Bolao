import os
import django
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
django.setup()

from bolao.models import Time
from django.core.files import File

def criar_escudo_placeholder(sigla):
    """Cria um escudo placeholder com a sigla do time"""
    # Criar uma imagem circular
    img = Image.new('RGB', (100, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Criar círculo colorido
    cores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']
    cor = cores[hash(sigla) % len(cores)]
    
    # Desenhar círculo
    draw.ellipse([10, 10, 90, 90], fill=cor, outline='white', width=3)
    
    # Tentar adicionar texto (sigla)
    try:
        font = ImageFont.truetype('arial.ttf', 20)
    except:
        font = ImageFont.load_default()
    
    # Calcular posição do texto para centralizá-lo
    bbox = draw.textbbox((0, 0), sigla, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (100 - text_width) // 2
    y = (100 - text_height) // 2
    
    # Desenhar texto
    draw.text((x, y), sigla, fill='white', font=font)
    
    # Salvar em BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

def adicionar_escudos():
    """Adiciona escudos placeholder para os times"""
    times = Time.objects.all()
    
    for time in times:
        if not time.escudo:
            print(f"Adicionando escudo para {time.nome}...")
            
            # Criar escudo placeholder
            img_buffer = criar_escudo_placeholder(time.sigla)
            
            # Criar nome do arquivo
            nome_arquivo = f"{time.sigla.lower()}_escudo.png"
            
            # Salvar no campo ImageField
            time.escudo.save(
                nome_arquivo,
                File(img_buffer),
                save=True
            )
            
            print(f"Escudo adicionado para {time.nome}")

if __name__ == '__main__':
    adicionar_escudos()
    print("Processo concluído!")