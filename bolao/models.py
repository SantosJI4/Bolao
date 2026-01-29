from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image
import os


def redimensionar_imagem_perfil(instance, filename):
    """Redimensiona automaticamente a imagem de perfil"""
    # Define o nome do arquivo
    ext = filename.split('.')[-1]
    filename = f"{instance.user.username}_perfil.{ext}"
    return os.path.join('perfis', filename)


class Time(models.Model):
    """Modelo para os times do brasileirão"""
    nome = models.CharField(max_length=50, unique=True)
    sigla = models.CharField(max_length=3, unique=True)
    escudo = models.ImageField(upload_to='escudos/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Time'
        verbose_name_plural = 'Times'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class Participante(models.Model):
    """Modelo para os participantes do bolão"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_exibicao = models.CharField(max_length=100)
    foto_perfil = models.ImageField(upload_to=redimensionar_imagem_perfil, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    invisivel = models.BooleanField(default=False, help_text='Se marcado, não aparecerá na classificação')
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Participante'
        verbose_name_plural = 'Participantes'
        ordering = ['nome_exibicao']
    
    def __str__(self):
        return self.nome_exibicao
    
    def get_foto_url(self):
        """Retorna URL da foto ou None se não tiver foto"""
        if self.foto_perfil:
            return self.foto_perfil.url
        return None
    
    @property
    def tem_foto(self):
        """Verifica se o participante tem foto de perfil"""
        return bool(self.foto_perfil)
    
    def save(self, *args, **kwargs):
        """Redimensiona a imagem ao salvar"""
        super().save(*args, **kwargs)
        
        if self.foto_perfil:
            try:
                # Abre a imagem
                img = Image.open(self.foto_perfil.path)
                
                # Converte para RGB se necessário (para evitar problemas com RGBA)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Se a imagem for maior que 400x400, redimensiona
                if img.height > 400 or img.width > 400:
                    output_size = (400, 400)
                    img.thumbnail(output_size, Image.Resampling.LANCZOS)
                    img.save(self.foto_perfil.path, format='JPEG', quality=85)
            except Exception as e:
                # Se houver erro no processamento da imagem, apenas ignora
                pass
    
    @property
    def pontos_totais(self):
        """Calcula o total de pontos do participante"""
        palpites = self.palpite_set.filter(jogo__resultado_finalizado=True)
        return sum(palpite.pontos_obtidos for palpite in palpites)


class Rodada(models.Model):
    """Modelo para as rodadas do campeonato"""
    numero = models.PositiveIntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(38)])
    nome = models.CharField(max_length=100, blank=True)  # Ex: "Rodada 1", "Final"
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    ativa = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Rodada'
        verbose_name_plural = 'Rodadas'
        ordering = ['numero']
    
    def __str__(self):
        return f"Rodada {self.numero}" + (f" - {self.nome}" if self.nome else "")
    
    @property
    def status(self):
        """Retorna o status da rodada: futura, atual, encerrada"""
        from django.utils import timezone
        now = timezone.now()
        
        if now < self.data_inicio:
            return 'futura'
        elif now <= self.data_fim and self.ativa:
            return 'atual'
        else:
            return 'encerrada'
    
    @property
    def pode_palpitar(self):
        """Verifica se ainda é possível palpitar nesta rodada"""
        return self.status == 'atual' and self.ativa


class Jogo(models.Model):
    """Modelo para os jogos de cada rodada"""
    rodada = models.ForeignKey(Rodada, on_delete=models.CASCADE)
    time_casa = models.ForeignKey(Time, on_delete=models.CASCADE, related_name='jogos_casa')
    time_visitante = models.ForeignKey(Time, on_delete=models.CASCADE, related_name='jogos_visitante')
    data_hora = models.DateTimeField()
    
    # Resultados
    gols_casa = models.PositiveIntegerField(null=True, blank=True)
    gols_visitante = models.PositiveIntegerField(null=True, blank=True)
    resultado_finalizado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Jogo'
        verbose_name_plural = 'Jogos'
        ordering = ['data_hora']
        unique_together = ('rodada', 'time_casa', 'time_visitante')
    
    def __str__(self):
        if self.resultado_finalizado:
            return f"{self.time_casa} {self.gols_casa} x {self.gols_visitante} {self.time_visitante}"
        return f"{self.time_casa} x {self.time_visitante}"
    
    @property
    def resultado(self):
        """Retorna o resultado do jogo: V (vitória casa), E (empate), D (derrota casa)"""
        if not self.resultado_finalizado or self.gols_casa is None or self.gols_visitante is None:
            return None
        
        if self.gols_casa > self.gols_visitante:
            return 'V'  # Vitória do time da casa
        elif self.gols_casa < self.gols_visitante:
            return 'D'  # Derrota do time da casa (vitória visitante)
        else:
            return 'E'  # Empate


class Palpite(models.Model):
    """Modelo para os palpites dos participantes"""
    
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    jogo = models.ForeignKey(Jogo, on_delete=models.CASCADE)
    gols_casa_palpite = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)], default=0)
    gols_visitante_palpite = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)], default=0)
    data_palpite = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Palpite'
        verbose_name_plural = 'Palpites'
        unique_together = ('participante', 'jogo')
        ordering = ['-data_palpite']
    
    def __str__(self):
        return f"{self.participante.nome_exibicao} - {self.jogo.time_casa} {self.gols_casa_palpite} x {self.gols_visitante_palpite} {self.jogo.time_visitante}"
    
    @property
    def pontos_obtidos(self):
        """Calcula os pontos obtidos com base no resultado real do jogo"""
        if not self.jogo.resultado_finalizado:
            return 0
        
        # Pontuação baseada no acerto dos gols
        if (self.gols_casa_palpite == self.jogo.gols_casa and 
            self.gols_visitante_palpite == self.jogo.gols_visitante):
            return 3  # Placar exato = 3 pontos
        elif self.resultado_palpite == self.jogo.resultado:
            return 1  # Acertou apenas o resultado (quem ganha) = 1 ponto
        else:
            return 0  # Errou = 0 pontos
    
    @property
    def resultado_palpite(self):
        """Retorna o resultado do palpite baseado nos gols"""
        if self.gols_casa_palpite > self.gols_visitante_palpite:
            return 'V'  # Vitória do time da casa
        elif self.gols_casa_palpite < self.gols_visitante_palpite:
            return 'D'  # Vitória do visitante
        else:
            return 'E'  # Empate
    
    @property
    def acertou(self):
        """Verifica se o palpite está correto (resultado ou placar exato)"""
        if not self.jogo.resultado_finalizado:
            return False
        return (self.gols_casa_palpite == self.jogo.gols_casa and 
                self.gols_visitante_palpite == self.jogo.gols_visitante) or \
               self.resultado_palpite == self.jogo.resultado
    
    @property
    def acertou_placar_exato(self):
        """Verifica se acertou o placar exato"""
        return (self.jogo.resultado_finalizado and 
                self.gols_casa_palpite == self.jogo.gols_casa and 
                self.gols_visitante_palpite == self.jogo.gols_visitante)


class Classificacao(models.Model):
    """Modelo para armazenar a classificação atualizada"""
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE)
    posicao = models.PositiveIntegerField()
    pontos_totais = models.PositiveIntegerField(default=0)
    acertos_totais = models.PositiveIntegerField(default=0)
    ultimo_saldo = models.IntegerField(default=0)  # Saldo da última rodada
    ultima_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Classificação'
        verbose_name_plural = 'Classificações'
        ordering = ['posicao']
    
    def __str__(self):
        return f"{self.posicao}º - {self.participante.nome_exibicao} ({self.pontos_totais} pts)"
    
    @classmethod
    def atualizar_classificacao(cls):
        """Método para atualizar toda a classificação"""
        from django.db.models import Count, Q, F
        
        # Limpa classificação atual
        cls.objects.all().delete()
        
        # Pega a última rodada com jogos finalizados
        ultima_rodada = Rodada.objects.filter(
            jogo__resultado_finalizado=True
        ).order_by('-numero').first()
        
        participantes = Participante.objects.filter(ativo=True, invisivel=False)
        classificacao_data = []
        
        for participante in participantes:
            palpites_finalizados = Palpite.objects.filter(
                participante=participante,
                jogo__resultado_finalizado=True
            )
            
            pontos_totais = sum(palpite.pontos_obtidos for palpite in palpites_finalizados)
            acertos_totais = sum(1 for palpite in palpites_finalizados if palpite.acertou)
            
            # Calcula saldo da última rodada (pontos ganhos menos pontos perdidos)
            ultimo_saldo = 0
            if ultima_rodada:
                palpites_ultima_rodada = Palpite.objects.filter(
                    participante=participante,
                    jogo__rodada=ultima_rodada,
                    jogo__resultado_finalizado=True
                )
                pontos_ultima_rodada = sum(palpite.pontos_obtidos for palpite in palpites_ultima_rodada)
                total_jogos_ultima_rodada = palpites_ultima_rodada.count()
                # Saldo = pontos ganhos - pontos que podia ter ganho
                ultimo_saldo = pontos_ultima_rodada - (total_jogos_ultima_rodada * 0)  # Simplificado: pontos ganhos
                ultimo_saldo = pontos_ultima_rodada  # Por enquanto, só os pontos da última rodada
            
            classificacao_data.append({
                'participante': participante,
                'pontos_totais': pontos_totais,
                'acertos_totais': acertos_totais,
                'ultimo_saldo': ultimo_saldo,
            })
        
        # Ordena por pontos (decrescente), depois por acertos (decrescente)
        classificacao_data.sort(key=lambda x: (x['pontos_totais'], x['acertos_totais']), reverse=True)
        
        # Cria registros de classificação
        for posicao, data in enumerate(classificacao_data, 1):
            cls.objects.create(
                posicao=posicao,
                **data
            )
