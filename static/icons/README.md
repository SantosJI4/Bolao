# Ícones PWA - FutAmigo

## Instruções para Gerar Ícones

Para que a PWA funcione corretamente, você precisa gerar os ícones nos tamanhos especificados no manifest.json.

### Tamanhos Necessários:
- 72x72px
- 96x96px
- 128x128px
- 144x144px
- 152x152px
- 192x192px
- 384x384px
- 512x512px

### Como Gerar:

1. **Usando uma imagem base (logo do FutAmigo):**
   - Crie uma imagem quadrada com pelo menos 512x512px
   - Use uma ferramenta como Photoshop, GIMP ou online

2. **Ferramentas Online Recomendadas:**
   - https://www.favicon-generator.org/
   - https://realfavicongenerator.net/
   - https://app-manifest-generator.netlify.app/

3. **Usando ImageMagick (linha de comando):**
   ```bash
   # Instale o ImageMagick primeiro
   magick convert logo.png -resize 72x72 icon-72x72.png
   magick convert logo.png -resize 96x96 icon-96x96.png
   magick convert logo.png -resize 128x128 icon-128x128.png
   magick convert logo.png -resize 144x144 icon-144x144.png
   magick convert logo.png -resize 152x152 icon-152x152.png
   magick convert logo.png -resize 192x192 icon-192x192.png
   magick convert logo.png -resize 384x384 icon-384x384.png
   magick convert logo.png -resize 512x512 icon-512x512.png
   ```

### Dicas:
- Use um fundo transparente ou sólido
- Mantenha o design simples e reconhecível
- Certifique-se de que o ícone funciona bem em diferentes tamanhos
- Use o mesmo estilo visual da marca FutAmigo

### Screenshots (Opcional):
Para melhorar a experiência de instalação, adicione screenshots em:
- `screenshots/desktop.png` (1280x720px)
- `screenshots/mobile.png` (640x1136px)

Estas são capturas de tela da aplicação em funcionamento.