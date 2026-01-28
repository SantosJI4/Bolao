from django import forms
from .models import Participante


class PerfilParticipanteForm(forms.ModelForm):
    """Formulário para editar perfil do participante"""
    
    class Meta:
        model = Participante
        fields = ['nome_exibicao', 'foto_perfil']
        widgets = {
            'nome_exibicao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu nome de exibição no bolão'
            }),
            'foto_perfil': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'nome_exibicao': 'Nome de Exibição',
            'foto_perfil': 'Foto de Perfil'
        }
        help_texts = {
            'foto_perfil': 'Formatos aceitos: JPG, PNG, GIF. Tamanho máximo: 5MB.'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna o nome obrigatório
        self.fields['nome_exibicao'].required = True
        
    def clean_foto_perfil(self):
        """Validação customizada para a foto de perfil"""
        foto = self.cleaned_data.get('foto_perfil')
        
        if foto:
            # Verifica o tamanho do arquivo (5MB = 5 * 1024 * 1024 bytes)
            if foto.size > 5 * 1024 * 1024:
                raise forms.ValidationError('O arquivo é muito grande. Tamanho máximo permitido: 5MB.')
            
            # Verifica se é uma imagem válida
            if not foto.content_type.startswith('image/'):
                raise forms.ValidationError('Por favor, envie apenas arquivos de imagem.')
                
        return foto