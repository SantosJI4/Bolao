#!/usr/bin/env python
"""
Script para adicionar escudos aos novos times
"""
import os
import sys
import django
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')
django.setup()

from bolao.models import Time

def criar_escudo_generico(sigla, cor='#0066CC'):
    """Cria um escudo genérico com a sigla do time"""
    from PIL import Image, ImageDraw, ImageFont
    
    # Criar uma imagem 128x128
    size = 128
    img = Image.new('RGB', (size, size), 'white')
    draw = ImageDraw.Draw(img)
    
    # Desenhar círculo de fundo
    margin = 10
    draw.ellipse([margin, margin, size-margin, size-margin], fill=cor, outline='#333333', width=3)
    
    # Tentar usar uma fonte do sistema, se não conseguir usar a padrão
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        except:
            font = ImageFont.load_default()
    
    # Calcular posição centralizada do texto
    bbox = draw.textbbox((0, 0), sigla, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    # Desenhar texto
    draw.text((x, y), sigla, fill='white', font=font)
    
    # Salvar em BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()

def atualizar_escudos():
    # Cores para os times (baseadas nas cores tradicionais)
    cores_times = {
        'CAP': '#CC0000',    # Athletico-PR - Vermelho
        'CAM': '#000000',    # Atlético-MG - Preto
        'CHA': '#00CC00',    # Chapecoense - Verde
        'MIR': '#FF8800',    # Mirassol - Laranja
        'RBB': '#0033CC',    # Red Bull Bragantino - Azul
        'REM': '#0066CC',    # Remo - Azul
        'VAS': '#000000',    # Vasco - Preto
    }
    
    # Times que precisam de escudos
    times_sem_escudo = Time.objects.filter(escudo__isnull=True)
    
    if not times_sem_escudo.exists():
        times_sem_escudo = Time.objects.filter(escudo='')
    
    print(f"Adicionando escudos para {times_sem_escudo.count()} times...")
    
    for time in times_sem_escudo:
        cor = cores_times.get(time.sigla, '#0066CC')  # Azul padrão se não encontrar
        
        try:
            # Criar escudo genérico
            escudo_data = criar_escudo_generico(time.sigla, cor)
            
            # Salvar no modelo
            filename = f"escudo_{time.sigla.lower()}.png"
            time.escudo.save(filename, ContentFile(escudo_data), save=True)
            
            print(f"  ✅ Escudo criado para {time.nome} ({time.sigla})")
            
        except Exception as e:
            print(f"  ❌ Erro ao criar escudo para {time.nome}: {e}")
    
    print(f"\n📊 Resumo:")
    times_com_escudo = Time.objects.exclude(escudo__isnull=True).exclude(escudo='')
    print(f"Times com escudo: {times_com_escudo.count()}")
    print(f"Total de times: {Time.objects.count()}")

if __name__ == '__main__':
    try:
        atualizar_escudos()
        print("\n✅ Atualização dos escudos concluída!")
    except Exception as e:
        print(f"\n❌ Erro durante a atualização: {e}")
        sys.exit(1)