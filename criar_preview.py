from PIL import Image, ImageDraw, ImageFont
import os

# Criar imagem de preview para redes sociais (1200x630 - padrão Open Graph)
width, height = 1200, 630
background_color = (40, 167, 69)  # Verde do Bootstrap success
text_color = (255, 255, 255)

# Criar imagem
img = Image.new('RGB', (width, height), background_color)
draw = ImageDraw.Draw(img)

# Tentar usar fonte maior, senão usar padrão
try:
    font_title = ImageFont.truetype("arial.ttf", 80)
    font_subtitle = ImageFont.truetype("arial.ttf", 40)
except:
    try:
        font_title = ImageFont.truetype("calibri.ttf", 80)
        font_subtitle = ImageFont.truetype("calibri.ttf", 40)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()

# Texto principal
title = "FutAmigo"
subtitle = "Bolão do Brasileirão"
description = "Faça seus palpites e compete com os amigos!"

# Calcular posições centralizadas
title_bbox = draw.textbbox((0, 0), title, font=font_title)
title_width = title_bbox[2] - title_bbox[0]
title_x = (width - title_width) // 2

subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
subtitle_x = (width - subtitle_width) // 2

desc_bbox = draw.textbbox((0, 0), description, font=font_subtitle)
desc_width = desc_bbox[2] - desc_bbox[0]
desc_x = (width - desc_width) // 2

# Desenhar textos
draw.text((title_x, 150), title, fill=text_color, font=font_title)
draw.text((subtitle_x, 250), subtitle, fill=text_color, font=font_subtitle)
draw.text((desc_x, 350), description, fill=text_color, font=font_subtitle)

# Adicionar ícone de futebol (emoji simples)
draw.ellipse([550, 450, 650, 550], fill=text_color)
draw.ellipse([570, 470, 630, 530], fill=background_color)
draw.text((590, 480), "⚽", fill=text_color, font=font_subtitle)

# Salvar na pasta static
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

img.save(os.path.join(static_dir, "futamigo-preview.png"), "PNG")
print("✅ Imagem de preview criada: static/futamigo-preview.png")
print("📐 Tamanho: 1200x630px (padrão Open Graph)")
print("🎨 Cor: Verde FutAmigo com texto branco")