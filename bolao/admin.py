from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms
from .models import Time, Participante, Rodada, Jogo, Palpite, Classificacao
import re


class ResultadosLoteForm(forms.Form):
    """Formulário para inserir resultados em lote"""
    rodada = forms.ModelChoiceField(
        queryset=Rodada.objects.all(),
        label='Rodada',
        help_text='Selecione a rodada para inserir os resultados'
    )
    
    resultados = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 10,
            'cols': 50,
            'placeholder': 'Digite os resultados separados por vírgula ou quebra de linha.\nExemplo: 2x1, 0x0, 1x3, 2x2\nOu um resultado por linha:\n2x1\n0x0\n1x3\n2x2'
        }),
        label='Resultados',
        help_text='Formato: "golsCasa x golsVisitante". Ex: 2x1, 0x0, 1x3. Os resultados serão aplicados na ordem dos jogos da rodada.'
    )
    
    def clean_resultados(self):
        resultados_text = self.cleaned_data['resultados']
        
        # Aceita vírgulas ou quebras de linha como separadores
        if ',' in resultados_text:
            resultados_lista = [r.strip() for r in resultados_text.split(',') if r.strip()]
        else:
            resultados_lista = [r.strip() for r in resultados_text.split('\n') if r.strip()]
        
        # Valida cada resultado
        resultados_validados = []
        for i, resultado in enumerate(resultados_lista, 1):
            # Padrão: número x número (com espaços opcionais)
            match = re.match(r'^(\d+)\s*x\s*(\d+)$', resultado.lower())
            if not match:
                raise forms.ValidationError(f'Resultado {i} inválido: "{resultado}". Use o formato "2x1"')
            
            gols_casa = int(match.group(1))
            gols_visitante = int(match.group(2))
            
            if gols_casa < 0 or gols_visitante < 0:
                raise forms.ValidationError(f'Resultado {i}: gols não podem ser negativos')
            
            if gols_casa > 20 or gols_visitante > 20:
                raise forms.ValidationError(f'Resultado {i}: máximo 20 gols por time')
            
            resultados_validados.append((gols_casa, gols_visitante))
        
        return resultados_validados


# Inline para conectar User e Participante
class ParticipanteInline(admin.StackedInline):
    model = Participante
    can_delete = False
    verbose_name_plural = 'Participante'


# Customizar o User Admin
class UserAdmin(BaseUserAdmin):
    inlines = (ParticipanteInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'escudo_preview')
    list_filter = ('nome',)
    search_fields = ('nome', 'sigla')
    
    def escudo_preview(self, obj):
        if obj.escudo:
            return format_html('<img src="{}" width="30" height="30" style="border-radius: 50%;" />', obj.escudo.url)
        return "Sem escudo"
    escudo_preview.short_description = 'Escudo'


@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ('nome_exibicao', 'user', 'foto_preview', 'ativo', 'pontos_totais', 'data_cadastro')
    list_filter = ('ativo', 'data_cadastro')
    search_fields = ('nome_exibicao', 'user__username', 'user__email')
    readonly_fields = ('data_cadastro', 'pontos_totais')
    
    def foto_preview(self, obj):
        if obj.foto_perfil:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />', obj.foto_perfil.url)
        return format_html('<div style="width: 40px; height: 40px; border-radius: 50%; background-color: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #666;"><i class="fas fa-user"></i></div>')
    foto_preview.short_description = 'Foto'
    
    def pontos_totais(self, obj):
        return obj.pontos_totais
    pontos_totais.short_description = 'Pontos Totais'


class JogoInline(admin.TabularInline):
    model = Jogo
    extra = 10  # Para criar 10 jogos de uma vez (padrão do brasileirão)
    fields = ('time_casa', 'time_visitante', 'data_hora', 'gols_casa', 'gols_visitante', 'resultado_finalizado')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Se for uma nova rodada, não mostrar campos de resultado
        if obj is None:
            self.fields = ('time_casa', 'time_visitante', 'data_hora')
        else:
            self.fields = ('time_casa', 'time_visitante', 'data_hora', 'gols_casa', 'gols_visitante', 'resultado_finalizado')
        return formset


@admin.register(Rodada)
class RodadaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nome', 'status_display', 'data_inicio', 'data_fim', 'ativa', 'total_jogos')
    list_filter = ('ativa', 'data_inicio')
    inlines = [JogoInline]
    
    def status_display(self, obj):
        status = obj.status
        colors = {
            'futura': 'blue',
            'atual': 'green', 
            'encerrada': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(status, 'black'),
            status.title()
        )
    status_display.short_description = 'Status'
    
    def total_jogos(self, obj):
        return obj.jogo_set.count()
    total_jogos.short_description = 'Total de Jogos'
    
    actions = ['ativar_rodada', 'desativar_rodada', 'inserir_resultados_rapido']
    
    def ativar_rodada(self, request, queryset):
        # Desativa todas as outras rodadas primeiro
        Rodada.objects.all().update(ativa=False)
        # Ativa a rodada selecionada
        queryset.update(ativa=True)
        self.message_user(request, f"{queryset.count()} rodada(s) ativada(s)")
    ativar_rodada.short_description = "Ativar rodada selecionada"
    
    def desativar_rodada(self, request, queryset):
        queryset.update(ativa=False)
        self.message_user(request, f"{queryset.count()} rodada(s) desativada(s)")
    desativar_rodada.short_description = "Desativar rodada selecionada"
    
    def inserir_resultados_rapido(self, request, queryset):
        if queryset.count() != 1:
            messages.error(request, "Selecione apenas UMA rodada para inserir resultados.")
            return
        
        rodada = queryset.first()
        return HttpResponseRedirect(f'/admin/bolao/jogo/resultados-lote/?rodada_id={rodada.id}')
    inserir_resultados_rapido.short_description = "🚀 Inserir resultados em lote"


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'rodada', 'data_hora', 'resultado_display', 'resultado_finalizado', 'total_palpites')
    list_filter = ('rodada', 'resultado_finalizado', 'data_hora')
    search_fields = ('time_casa__nome', 'time_visitante__nome')
    
    change_list_template = 'admin/jogo_change_list.html'
    
    fieldsets = (
        ('Informações do Jogo', {
            'fields': ('rodada', 'time_casa', 'time_visitante', 'data_hora')
        }),
        ('Resultado', {
            'fields': ('gols_casa', 'gols_visitante', 'resultado_finalizado'),
            'description': 'Preencha o resultado após o fim do jogo'
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('resultados-lote/', self.admin_site.admin_view(self.resultados_lote_view), name='bolao_jogo_resultados_lote'),
        ]
        return custom_urls + urls
    
    def resultados_lote_view(self, request):
        """View para inserir resultados em lote"""
        if request.method == 'POST':
            form = ResultadosLoteForm(request.POST)
            if form.is_valid():
                rodada = form.cleaned_data['rodada']
                resultados = form.cleaned_data['resultados']
                
                # Busca jogos da rodada ordenados por data/hora
                jogos = Jogo.objects.filter(rodada=rodada).order_by('data_hora', 'id')
                
                if len(resultados) != jogos.count():
                    messages.error(request, f'A rodada {rodada} tem {jogos.count()} jogos, mas você forneceu {len(resultados)} resultados.')
                else:
                    # Aplica os resultados
                    jogos_atualizados = 0
                    for jogo, (gols_casa, gols_visitante) in zip(jogos, resultados):
                        jogo.gols_casa = gols_casa
                        jogo.gols_visitante = gols_visitante
                        jogo.resultado_finalizado = True
                        jogo.save()
                        jogos_atualizados += 1
                    
                    # Atualiza classificação
                    Classificacao.atualizar_classificacao()
                    
                    messages.success(request, f'✅ {jogos_atualizados} resultados inseridos com sucesso na {rodada}! Classificação atualizada.')
                    return HttpResponseRedirect('../')
        else:
            form = ResultadosLoteForm()
        
        context = {
            'form': form,
            'title': 'Inserir Resultados em Lote',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return render(request, 'admin/resultados_lote.html', context)
    
    def resultado_display(self, obj):
        if obj.resultado_finalizado:
            result = obj.resultado
            colors = {'V': 'green', 'E': 'orange', 'D': 'red'}
            labels = {'V': 'Vitória Casa', 'E': 'Empate', 'D': 'Vitória Visitante'}
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                colors.get(result, 'black'),
                labels.get(result, result)
            )
        return "Não finalizado"
    resultado_display.short_description = 'Resultado'
    
    def total_palpites(self, obj):
        return obj.palpite_set.count()
    total_palpites.short_description = 'Palpites'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('resultados-lote/', self.admin_site.admin_view(self.resultados_lote_view), name='bolao_jogo_resultados_lote'),
        ]
        return custom_urls + urls
    
    def resultados_lote_view(self, request):
        """View para inserir resultados em lote"""
        if request.method == 'POST':
            form = ResultadosLoteForm(request.POST)
            if form.is_valid():
                rodada = form.cleaned_data['rodada']
                resultados = form.cleaned_data['resultados']
                
                # Busca jogos da rodada ordenados por data/hora
                jogos = Jogo.objects.filter(rodada=rodada).order_by('data_hora', 'id')
                
                if len(resultados) != jogos.count():
                    messages.error(request, f'A rodada {rodada} tem {jogos.count()} jogos, mas você forneceu {len(resultados)} resultados.')
                else:
                    # Aplica os resultados
                    jogos_atualizados = 0
                    for jogo, (gols_casa, gols_visitante) in zip(jogos, resultados):
                        jogo.gols_casa = gols_casa
                        jogo.gols_visitante = gols_visitante
                        jogo.resultado_finalizado = True
                        jogo.save()
                        jogos_atualizados += 1
                    
                    # Atualiza classificação
                    Classificacao.atualizar_classificacao()
                    
                    messages.success(request, f'✅ {jogos_atualizados} resultados inseridos com sucesso na {rodada}! Classificação atualizada.')
                    return HttpResponseRedirect('../')
        else:
            form = ResultadosLoteForm()
        
        context = {
            'form': form,
            'title': 'Inserir Resultados em Lote',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return render(request, 'admin/resultados_lote.html', context)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Atualiza classificação quando um resultado é finalizado
        if obj.resultado_finalizado:
            Classificacao.atualizar_classificacao()
            messages.success(request, "Resultado salvo! Classificação atualizada automaticamente.")


@admin.register(Palpite)
class PalpiteAdmin(admin.ModelAdmin):
    list_display = ('participante', 'jogo', 'palpite_display', 'pontos_obtidos', 'acertou_display', 'data_palpite')
    list_filter = ('data_palpite', 'jogo__rodada', 'jogo__resultado_finalizado')
    search_fields = ('participante__nome_exibicao', 'jogo__time_casa__nome', 'jogo__time_visitante__nome')
    readonly_fields = ('pontos_obtidos', 'acertou_display', 'data_palpite')
    
    def palpite_display(self, obj):
        return format_html(
            '<span class="fw-bold">{} × {}</span>',
            obj.gols_casa_palpite,
            obj.gols_visitante_palpite
        )
    palpite_display.short_description = 'Palpite'
    
    def acertou_display(self, obj):
        if not obj.jogo.resultado_finalizado:
            return "Jogo não finalizado"
        
        if obj.acertou_placar_exato:
            return format_html(
                '<span style="color: gold; font-weight: bold;">⭐ Placar Exato</span>'
            )
        elif obj.acertou:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Resultado Correto</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Errou</span>'
            )
    acertou_display.short_description = 'Resultado'


@admin.register(Classificacao)
class ClassificacaoAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'participante', 'pontos_totais', 'acertos_totais', 'empates_acertados', 'vitorias_acertadas', 'ultima_atualizacao')
    list_filter = ('ultima_atualizacao',)
    search_fields = ('participante__nome_exibicao',)
    readonly_fields = ('posicao', 'participante', 'pontos_totais', 'acertos_totais', 'empates_acertados', 'vitorias_acertadas', 'ultima_atualizacao')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    actions = ['atualizar_classificacao_manual']
    
    def atualizar_classificacao_manual(self, request, queryset):
        Classificacao.atualizar_classificacao()
        self.message_user(request, "Classificação atualizada com sucesso!")
    atualizar_classificacao_manual.short_description = "Atualizar classificação manualmente"


# Customizações do admin site
admin.site.site_header = "FutAmigo - Painel Administrativo"
admin.site.site_title = "FutAmigo"
admin.site.index_title = "Gerenciamento do Bolão"
