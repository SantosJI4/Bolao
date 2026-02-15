from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django import forms
from .models import Time, Participante, Rodada, Jogo, Palpite, Classificacao, AtualizacaoSite, AtualizacaoVista, SessaoVisita, AcaoUsuario, MetricaDiaria, PaginaPopular, NotificationSettings, Notification
import re
from django.utils import timezone


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


class NotificationForm(forms.Form):
    """Formulário para enviar notificações personalizadas"""
    TIPO_CHOICES = [
        ('sistema', 'Notificação do Sistema'),
        ('nova_rodada', 'Nova Rodada'),
        ('lembrete_prazo', 'Lembrete de Prazo'),
        ('resultados', 'Resultados Publicados'),
        ('ranking', 'Ranking Atualizado'),
    ]
    
    DESTINATARIOS_CHOICES = [
        ('todos', 'Todos os Participantes'),
        ('ativos', 'Apenas Participantes Ativos'),
        ('com_notifs', 'Apenas com Notificações Ativadas'),
        ('selecionados', 'Participantes Selecionados'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        initial='sistema',
        label='Tipo de Notificação',
        help_text='Escolha o tipo de notificação'
    )
    
    titulo = forms.CharField(
        max_length=100,
        label='Título',
        help_text='Título da notificação (máximo 100 caracteres)',
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 🎉 Novidade no FutAmigo!'})
    )
    
    mensagem = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Digite a mensagem da notificação...\nDica: Use emojis para tornar mais atrativa! 🚀'
        }),
        label='Mensagem',
        help_text='Conteúdo da notificação'
    )
    
    url_acao = forms.URLField(
        required=False,
        label='URL de Ação (Opcional)',
        help_text='URL para onde direcionar quando a notificação for clicada',
        widget=forms.URLInput(attrs={'placeholder': '/classificacao/'})
    )
    
    destinatarios = forms.ChoiceField(
        choices=DESTINATARIOS_CHOICES,
        initial='com_notifs',
        label='Destinatários',
        help_text='Para quem enviar a notificação'
    )
    
    participantes_selecionados = forms.ModelMultipleChoiceField(
        queryset=Participante.objects.filter(ativo=True),
        required=False,
        label='Participantes Específicos',
        help_text='Só é usado se "Participantes Selecionados" for escolhido acima',
        widget=admin.widgets.FilteredSelectMultiple('participantes', False)
    )
    
    rodada_relacionada = forms.ModelChoiceField(
        queryset=Rodada.objects.all(),
        required=False,
        label='Rodada Relacionada (Opcional)',
        help_text='Se a notificação for sobre uma rodada específica'
    )
    
    enviar_imediatamente = forms.BooleanField(
        required=False,
        initial=True,
        label='Enviar Imediatamente',
        help_text='Se marcado, envia agora. Senão, agenda para envio posterior'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        destinatarios = cleaned_data.get('destinatarios')
        participantes_selecionados = cleaned_data.get('participantes_selecionados')
        
        if destinatarios == 'selecionados' and not participantes_selecionados:
            raise forms.ValidationError('Selecione pelo menos um participante quando escolher "Participantes Selecionados"')
        
        return cleaned_data


class PalpitesLoteForm(forms.Form):
    """Formulário para inserir palpites em lote"""
    participante = forms.ModelChoiceField(
        queryset=Participante.objects.all(),
        label='Participante',
        help_text='Selecione o participante para inserir os palpites'
    )
    
    rodada = forms.ModelChoiceField(
        queryset=Rodada.objects.all(),
        label='Rodada',
        help_text='Selecione a rodada para inserir os palpites'
    )
    
    palpites = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 10,
            'cols': 60,
            'placeholder': '''Digite os palpites nos formatos:
Formato 1 (placar direto): 1x1, 2x0, 0x3
Formato 2 (com times): fla 1x2 pal, atm 0x1 bah, cor 3x1 gre
Formato 3 (misto): 1x1, fla 2x0 pal, 0x3

Exemplos:
- fla 1x2 pal (Flamengo 1x2 Palmeiras)  
- atm 0x1 bah (Atlético-MG 0x1 Bahia)
- cor 3x1 gre (Corinthians 3x1 Grêmio)
- 2x1 (usa a ordem dos jogos da rodada)'''
        }),
        label='Palpites',
        help_text='Aceita diferentes formatos: apenas placares (2x1) ou com times (fla 1x2 pal)'
    )
    
    substituir_existentes = forms.BooleanField(
        required=False,
        initial=False,
        label='Substituir palpites existentes',
        help_text='Se marcado, irá sobrescrever palpites já existentes'
    )
    
    def clean_palpites(self):
        palpites_text = self.cleaned_data['palpites']
        rodada = self.cleaned_data.get('rodada')
        
        if not rodada:
            raise forms.ValidationError('Selecione uma rodada primeiro')
        
        # Aceita vírgulas ou quebras de linha como separadores
        if ',' in palpites_text:
            palpites_lista = [p.strip() for p in palpites_text.split(',') if p.strip()]
        else:
            palpites_lista = [p.strip() for p in palpites_text.split('\n') if p.strip()]
        
        # Obter jogos da rodada
        jogos = list(rodada.jogo_set.all().order_by('data_hora'))
        
        # Validar cada palpite
        palpites_validados = []
        for i, palpite in enumerate(palpites_lista):
            try:
                palpite_data = self._parse_palpite(palpite, jogos, i)
                palpites_validados.append(palpite_data)
            except forms.ValidationError as e:
                raise forms.ValidationError(f'Palpite {i+1} inválido: "{palpite}". {str(e)}')
        
        return palpites_validados
    
    def _parse_palpite(self, palpite_str, jogos, index):
        """Parse um palpite individual"""
        palpite_str = palpite_str.strip().lower()
        
        # Formato 1: apenas placar (2x1)
        match_simples = re.match(r'^(\d+)\s*x\s*(\d+)$', palpite_str)
        if match_simples:
            if index >= len(jogos):
                raise forms.ValidationError(f'Não há jogo na posição {index+1}')
            
            gols_casa = int(match_simples.group(1))
            gols_visitante = int(match_simples.group(2))
            jogo = jogos[index]
            
            return {
                'jogo': jogo,
                'gols_casa': gols_casa,
                'gols_visitante': gols_visitante
            }
        
        # Formato 2: com times (fla 1x2 pal)
        match_times = re.match(r'^([a-zA-Z]+)\s+(\d+)\s*x\s*(\d+)\s+([a-zA-Z]+)$', palpite_str)
        if match_times:
            time_casa_sigla = match_times.group(1)
            gols_casa = int(match_times.group(2))
            gols_visitante = int(match_times.group(3))
            time_visitante_sigla = match_times.group(4)
            
            # Encontrar o jogo correspondente
            jogo_encontrado = None
            for jogo in jogos:
                if (self._match_time(jogo.time_casa, time_casa_sigla) and 
                    self._match_time(jogo.time_visitante, time_visitante_sigla)):
                    jogo_encontrado = jogo
                    break
            
            if not jogo_encontrado:
                raise forms.ValidationError(f'Jogo não encontrado para {time_casa_sigla} x {time_visitante_sigla}')
            
            return {
                'jogo': jogo_encontrado,
                'gols_casa': gols_casa,
                'gols_visitante': gols_visitante
            }
        
        raise forms.ValidationError('Use formato "2x1" ou "fla 1x2 pal"')
    
    def _match_time(self, time, sigla_busca):
        """Verifica se a sigla corresponde ao time"""
        sigla_busca = sigla_busca.lower()
        time_nome = time.nome.lower()
        time_sigla = time.sigla.lower() if time.sigla else ''
        
        # Mapeamento de apelidos comuns
        apelidos = {
            'fla': ['flamengo'],
            'pal': ['palmeiras'],
            'cor': ['corinthians'],
            'sao': ['sao paulo', 'são paulo'],
            'gre': ['gremio', 'grêmio'],
            'int': ['internacional'],
            'atm': ['atletico mg', 'atlético mg', 'atletico-mg'],
            'cap': ['atletico pr', 'atlético pr', 'atletico-pr'],
            'bah': ['bahia'],
            'flu': ['fluminense'],
            'bot': ['botafogo'],
            'vas': ['vasco'],
            'san': ['santos'],
            'cru': ['cruzeiro'],
            'for': ['fortaleza'],
            'cea': ['ceara', 'ceará'],
            'goi': ['goias', 'goiás'],
            'cui': ['cuiaba', 'cuiabá'],
            'bre': ['bragantino', 'red bull bragantino'],
            'ame': ['america mg', 'américa mg'],
            'ath': ['athletico-pr', 'athletico'],
            'ava': ['avai', 'avaí'],
            'juw': ['juventude']
        }
        
        # Verifica sigla exata
        if sigla_busca == time_sigla:
            return True
        
        # Verifica se é apelido conhecido
        if sigla_busca in apelidos:
            for apelido in apelidos[sigla_busca]:
                if apelido in time_nome:
                    return True
        
        # Verifica se a sigla está contida no nome do time
        if sigla_busca in time_nome:
            return True
        
        return False


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
    list_display = ('nome_exibicao', 'user', 'foto_preview', 'ativo', 'invisivel', 'pontos_totais', 'data_cadastro')
    list_filter = ('ativo', 'invisivel', 'data_cadastro')
    search_fields = ('nome_exibicao', 'user__username', 'user__email')
    readonly_fields = ('data_cadastro', 'pontos_totais')
    actions = ['inserir_palpites_rapido', 'enviar_notificacao_personalizada']
    
    def foto_preview(self, obj):
        if obj.foto_perfil:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />', obj.foto_perfil.url)
        return '<div style="width: 40px; height: 40px; border-radius: 50%; background-color: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #666;"><i class="fas fa-user"></i></div>'
    foto_preview.short_description = 'Foto'
    
    def pontos_totais(self, obj):
        return obj.pontos_totais
    pontos_totais.short_description = 'Pontos Totais'
    
    def inserir_palpites_rapido(self, request, queryset):
        if queryset.count() != 1:
            messages.error(request, "Selecione apenas UM participante para inserir palpites.")
            return
        
        participante = queryset.first()
        return HttpResponseRedirect(f'/admin/bolao/participante/palpites-lote/?participante_id={participante.id}')
    inserir_palpites_rapido.short_description = "🎯 Inserir palpites em lote"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('palpites-lote/', self.admin_site.admin_view(self.palpites_lote_view), name='bolao_participante_palpites_lote'),
            path('jogos-rodada/', self.admin_site.admin_view(self.jogos_rodada_view), name='bolao_participante_jogos_rodada'),
        ]
        return custom_urls + urls
    
    def palpites_lote_view(self, request):
        """View para inserir palpites em lote"""
        participante_id = request.GET.get('participante_id')
        participante = None
        
        if participante_id:
            try:
                participante = Participante.objects.get(id=participante_id)
            except Participante.DoesNotExist:
                messages.error(request, "Participante não encontrado.")
                return HttpResponseRedirect('../../')
        
        if request.method == 'POST':
            form = PalpitesLoteForm(request.POST)
            if form.is_valid():
                participante = form.cleaned_data['participante']
                rodada = form.cleaned_data['rodada']
                palpites = form.cleaned_data['palpites']
                substituir_existentes = form.cleaned_data['substituir_existentes']
                
                palpites_criados = 0
                palpites_atualizados = 0
                erros = []
                
                for palpite_data in palpites:
                    jogo = palpite_data['jogo']
                    gols_casa = palpite_data['gols_casa']
                    gols_visitante = palpite_data['gols_visitante']
                    
                    try:
                        # Verifica se já existe palpite
                        palpite_existente = Palpite.objects.filter(
                            participante=participante,
                            jogo=jogo
                        ).first()
                        
                        if palpite_existente:
                            if substituir_existentes:
                                palpite_existente.gols_casa_palpite = gols_casa
                                palpite_existente.gols_visitante_palpite = gols_visitante
                                palpite_existente.save()
                                palpites_atualizados += 1
                            else:
                                erros.append(f'Palpite já existe para {jogo} (use "substituir existentes" se quiser sobrescrever)')
                        else:
                            # Cria novo palpite
                            Palpite.objects.create(
                                participante=participante,
                                jogo=jogo,
                                gols_casa_palpite=gols_casa,
                                gols_visitante_palpite=gols_visitante
                            )
                            palpites_criados += 1
                            
                    except Exception as e:
                        erros.append(f'Erro ao processar {jogo}: {str(e)}')
                
                # Mensagem de resultado
                if palpites_criados > 0 or palpites_atualizados > 0:
                    msg = f'✅ Palpites inseridos para {participante.nome_exibicao}!'
                    if palpites_criados > 0:
                        msg += f' {palpites_criados} criados,'
                    if palpites_atualizados > 0:
                        msg += f' {palpites_atualizados} atualizados.'
                    messages.success(request, msg)
                
                if erros:
                    for erro in erros:
                        messages.warning(request, erro)
                
                if not erros or (palpites_criados > 0 or palpites_atualizados > 0):
                    return HttpResponseRedirect('../../')
        else:
            initial_data = {}
            if participante:
                initial_data['participante'] = participante
            form = PalpitesLoteForm(initial=initial_data)
        
        context = {
            'form': form,
            'title': f'Inserir Palpites em Lote - {participante.nome_exibicao if participante else ""}',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'participante': participante,
        }
        
        return render(request, 'admin/palpites_lote.html', context)
    
    def jogos_rodada_view(self, request):
        """API para buscar jogos de uma rodada via AJAX"""
        rodada_id = request.GET.get('rodada_id')
        
        if not rodada_id:
            return JsonResponse({'error': 'rodada_id é obrigatório'}, status=400)
        
        try:
            rodada = Rodada.objects.get(id=rodada_id)
            jogos = rodada.jogo_set.all().order_by('data_hora', 'id')
            
            jogos_data = []
            for jogo in jogos:
                jogos_data.append({
                    'id': jogo.id,
                    'time_casa': jogo.time_casa.nome,
                    'time_visitante': jogo.time_visitante.nome,
                    'data_hora': jogo.data_hora.strftime('%d/%m %H:%M') if jogo.data_hora else 'Data não definida'
                })
            
            return JsonResponse({
                'jogos': jogos_data,
                'rodada': rodada.nome,
                'total': len(jogos_data)
            })
            
        except Rodada.DoesNotExist:
            return JsonResponse({'error': 'Rodada não encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def enviar_notificacao_personalizada(self, request, queryset):
        """Action para enviar notificação personalizada para participantes selecionados"""
        participantes_ids = list(queryset.values_list('id', flat=True))
        
        if not participantes_ids:
            messages.error(request, "Nenhum participante selecionado!")
            return
        
        # Redirect para página de notificação personalizada com IDs dos participantes
        ids_str = ','.join(map(str, participantes_ids))
        url = f'/admin/bolao/participante/enviar-notificacao/?participantes={ids_str}'
        return HttpResponseRedirect(url)
    enviar_notificacao_personalizada.short_description = "🔔 Enviar notificação personalizada"

    def enviar_notificacao_view(self, request):
        """Página para enviar notificação personalizada"""
        # IDs dos participantes (se vem da action)
        participantes_ids = request.GET.get('participantes', '').split(',') if request.GET.get('participantes') else []
        
        if request.method == 'POST':
            form = NotificationForm(request.POST)
            
            if form.is_valid():
                # Obter dados do formulário
                tipo = form.cleaned_data['tipo']
                titulo = form.cleaned_data['titulo']
                mensagem = form.cleaned_data['mensagem']
                url_acao = form.cleaned_data.get('url_acao', '')
                destinatarios = form.cleaned_data['destinatarios']
                participantes_selecionados = form.cleaned_data.get('participantes_selecionados', [])
                rodada_relacionada = form.cleaned_data.get('rodada_relacionada')
                enviar_imediatamente = form.cleaned_data['enviar_imediatamente']
                
                # Determinar participantes para envio
                if destinatarios == 'todos':
                    participantes = Participante.objects.all()
                elif destinatarios == 'ativos':
                    participantes = Participante.objects.filter(ativo=True)
                elif destinatarios == 'com_notifs':
                    participantes = Participante.objects.filter(
                        ativo=True,
                        notification_settings__enabled=True
                    )
                elif destinatarios == 'selecionados':
                    if participantes_ids:
                        # Usar IDs da action
                        participantes = Participante.objects.filter(id__in=participantes_ids)
                    else:
                        # Usar participantes do formulário
                        participantes = participantes_selecionados
                
                # Criar notificações
                notifications_created = []
                
                for participante in participantes:
                    notification = Notification.objects.create(
                        participante=participante,
                        tipo=tipo,
                        titulo=titulo,
                        mensagem=mensagem,
                        rodada_relacionada=rodada_relacionada,
                        url_acao=url_acao
                    )
                    notifications_created.append(notification)
                
                # Enviar notificações se solicitado
                if enviar_imediatamente:
                    from .views import send_push_notification
                    
                    enviadas = 0
                    for notification in notifications_created:
                        if send_push_notification(notification):
                            enviadas += 1
                    
                    messages.success(request, 
                        f'🎉 Notificação enviada para {len(notifications_created)} participante(s)! '
                        f'{enviadas} entregue(s) com sucesso.')
                else:
                    messages.success(request, 
                        f'📝 Notificação criada para {len(notifications_created)} participante(s)! '
                        f'Use o admin de Notificações para enviá-las.')
                
                return redirect('/admin/bolao/notification/')
        else:
            # Form inicial
            initial_data = {}
            if participantes_ids:
                # Se vem da action, usar modo selecionados
                initial_data['destinatarios'] = 'selecionados'
                initial_data['participantes_selecionados'] = Participante.objects.filter(id__in=participantes_ids)
            
            form = NotificationForm(initial=initial_data)
        
        # Contexto para template com estatísticas
        context = {
            'form': form,
            'title': 'Enviar Notificação Personalizada',
            'participantes_count': len(participantes_ids) if participantes_ids else 0,
            'opts': self.model._meta,
            'has_change_permission': True,
            **self._get_notification_stats(),
        }
        
        return render(request, 'admin/bolao/enviar_notificacao.html', context)

    @staticmethod
    def _get_notification_stats():
        """Retorna estatísticas para o painel de notificações"""
        from datetime import timedelta
        hoje = timezone.now().date()
        return {
            'total_participantes': Participante.objects.filter(ativo=True).count(),
            'com_notifs_ativadas': NotificationSettings.objects.filter(enabled=True).count(),
            'com_push_subscription': NotificationSettings.objects.exclude(push_subscription__isnull=True).exclude(push_subscription={}).count(),
            'notifs_enviadas_hoje': Notification.objects.filter(criada_em__date=hoje).count(),
        }


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
            return '<span style="color: gold; font-weight: bold;">⭐ Placar Exato</span>'
        elif obj.acertou:
            return '<span style="color: green; font-weight: bold;">✓ Resultado Correto</span>'
        else:
            return '<span style="color: red; font-weight: bold;">✗ Errou</span>'
    acertou_display.short_description = 'Resultado'


@admin.register(Classificacao)
class ClassificacaoAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'participante', 'pontos_totais', 'acertos_totais', 'ultimo_saldo', 'ultima_atualizacao')
    list_filter = ('ultima_atualizacao',)
    search_fields = ('participante__nome_exibicao',)
    readonly_fields = ('posicao', 'participante', 'pontos_totais', 'acertos_totais', 'ultimo_saldo', 'ultima_atualizacao')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    actions = ['atualizar_classificacao_manual']
    
    def atualizar_classificacao_manual(self, request, queryset):
        Classificacao.atualizar_classificacao()
        self.message_user(request, "Classificação atualizada com sucesso!")
    atualizar_classificacao_manual.short_description = "Atualizar classificação manualmente"


@admin.register(AtualizacaoSite)
class AtualizacaoSiteAdmin(admin.ModelAdmin):
    """Administração das atualizações do site"""
    list_display = ('versao', 'titulo', 'data_lancamento', 'ativa', 'tem_link', 'usuarios_que_viram')
    list_filter = ('ativa', 'data_lancamento')
    search_fields = ('versao', 'titulo', 'descricao')
    ordering = ('-data_lancamento',)
    list_editable = ('ativa',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('versao', 'titulo', 'descricao', 'ativa')
        }),
        ('Link Opcional', {
            'fields': ('link_pagina', 'texto_link'),
            'description': 'Adicione um link para uma página específica que será mostrado na atualização.',
            'classes': ('collapse',)
        }),
    )
    
    def tem_link(self, obj):
        """Mostra se a atualização tem link"""
        return "🔗" if obj.link_pagina else "—"
    
    tem_link.short_description = "Link"
    
    def usuarios_que_viram(self, obj):
        """Mostra quantos usuários já viram a atualização"""
        count = AtualizacaoVista.objects.filter(atualizacao=obj).count()
        return f"{count} usuários"
    
    usuarios_que_viram.short_description = "Visualizações"


@admin.register(AtualizacaoVista)
class AtualizacaoVistaAdmin(admin.ModelAdmin):
    """Administração das visualizações de atualizações"""
    list_display = ('participante', 'atualizacao_versao', 'data_visualizacao')
    list_filter = ('data_visualizacao', 'atualizacao__versao')
    search_fields = ('participante__nome_exibicao', 'atualizacao__versao', 'atualizacao__titulo')
    ordering = ('-data_visualizacao',)
    
    def atualizacao_versao(self, obj):
        """Mostra a versão da atualização"""
        return f"v{obj.atualizacao.versao} - {obj.atualizacao.titulo}"
    
    atualizacao_versao.short_description = "Atualização"
    
    def has_add_permission(self, request):
        """Não permite adicionar manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Não permite editar"""
        return False


# Customizações do admin site
admin.site.site_header = "FutAmigo - Painel Administrativo"
admin.site.site_title = "FutAmigo"
admin.site.index_title = "Gerenciamento do Bolão"

# Adiciona link para Analytics na página inicial do admin
from django.urls import reverse
from django.utils.html import format_html

def analytics_link():
    return format_html(
        '<a href="/admin/analytics/" style="color: #0066cc; font-weight: bold;">📊 Dashboard de Analytics</a>'
    )

# Adiciona o link ao context do admin
admin.site.index_template = 'admin/index.html'


# =================== ADMIN ANALYTICS ===================

@admin.register(SessaoVisita)
class SessaoVisitaAdmin(admin.ModelAdmin):
    """Admin para Sessões de Visita"""
    list_display = [
        'get_usuario', 'ip_address', 'dispositivo_tipo', 'navegador', 
        'data_inicio', 'duracao_formatada', 'paginas_visitadas', 'ativo'
    ]
    list_filter = [
        'dispositivo_tipo', 'ativo', 'data_inicio', 'navegador', 'sistema_operacional'
    ]
    search_fields = ['ip_address', 'participante__nome_exibicao', 'navegador']
    readonly_fields = [
        'session_id', 'ip_address', 'user_agent', 'data_inicio', 'data_fim', 
        'duracao_minutos', 'paginas_visitadas'
    ]
    ordering = ['-data_inicio']
    date_hierarchy = 'data_inicio'
    
    def get_usuario(self, obj):
        if obj.participante:
            return format_html(
                '<strong style="color: #0066cc;">{}</strong>',
                obj.participante.nome_exibicao
            )
        return format_html(
            '<span style="color: #666;">Anônimo ({})</span>',
            obj.ip_address
        )
    get_usuario.short_description = 'Usuário'
    
    def duracao_formatada(self, obj):
        if obj.duracao_minutos:
            if obj.duracao_minutos < 1:
                return f"{int(obj.duracao_minutos * 60)}s"
            elif obj.duracao_minutos < 60:
                return f"{obj.duracao_minutos:.1f}min"
            else:
                horas = int(obj.duracao_minutos // 60)
                minutos = int(obj.duracao_minutos % 60)
                return f"{horas}h {minutos}min"
        return "Em andamento" if obj.ativo else "N/A"
    duracao_formatada.short_description = 'Duração'
    
    def has_add_permission(self, request):
        return False


@admin.register(AcaoUsuario)
class AcaoUsuarioAdmin(admin.ModelAdmin):
    """Admin para Ações dos Usuários"""
    list_display = [
        'get_usuario', 'tipo_acao', 'pagina_titulo', 'tempo_resposta_formatado', 
        'timestamp', 'get_status_code'
    ]
    list_filter = ['tipo_acao', 'timestamp', 'sessao__dispositivo_tipo']
    search_fields = [
        'sessao__participante__nome_exibicao', 'pagina_titulo', 'pagina_url',
        'sessao__ip_address'
    ]
    readonly_fields = [
        'sessao', 'tipo_acao', 'pagina_url', 'pagina_titulo', 
        'tempo_resposta', 'timestamp', 'metadados'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    def get_usuario(self, obj):
        if obj.sessao.participante:
            return obj.sessao.participante.nome_exibicao
        return f"IP: {obj.sessao.ip_address}"
    get_usuario.short_description = 'Usuário'
    
    def tempo_resposta_formatado(self, obj):
        if obj.tempo_resposta:
            if obj.tempo_resposta < 1000:
                return f"{obj.tempo_resposta:.0f}ms"
            else:
                return f"{obj.tempo_resposta/1000:.2f}s"
        return "N/A"
    tempo_resposta_formatado.short_description = 'Tempo Resp.'
    
    def get_status_code(self, obj):
        if obj.metadados and 'status_code' in obj.metadados:
            status = obj.metadados['status_code']
            if status == 200:
                color = '#28a745'
            elif status == 404:
                color = '#ffc107'
            elif status >= 500:
                color = '#dc3545'
            else:
                color = '#6c757d'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, status
            )
        return "N/A"
    get_status_code.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False


@admin.register(MetricaDiaria)
class MetricaDiariaAdmin(admin.ModelAdmin):
    """Admin para Métricas Diárias"""
    list_display = [
        'data', 'total_visitas', 'visitantes_unicos', 'usuarios_logados',
        'total_pageviews', 'tempo_medio_formatado', 'palpites_realizados'
    ]
    list_filter = ['data']
    ordering = ['-data']
    readonly_fields = [
        'data', 'total_visitas', 'visitantes_unicos', 'usuarios_logados',
        'usuarios_anonimos', 'total_pageviews', 'tempo_medio_sessao',
        'bounce_rate', 'palpites_realizados', 'mobile_visitas',
        'desktop_visitas', 'tablet_visitas'
    ]
    
    def tempo_medio_formatado(self, obj):
        if obj.tempo_medio_sessao:
            return f"{obj.tempo_medio_sessao:.1f}min"
        return "0min"
    tempo_medio_formatado.short_description = 'Tempo Médio'
    
    def has_add_permission(self, request):
        return False


@admin.register(PaginaPopular)
class PaginaPopularAdmin(admin.ModelAdmin):
    """Admin para Páginas Populares"""
    list_display = ['titulo', 'url', 'visitas_hoje', 'visitas_total', 'ultima_atualizacao']
    list_filter = ['ultima_atualizacao']
    search_fields = ['titulo', 'url']
    ordering = ['-visitas_hoje']
    readonly_fields = ['url', 'titulo', 'visitas_hoje', 'visitas_total', 'ultima_atualizacao']
    
    def has_add_permission(self, request):
        return False


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """Admin para Configurações de Notificações"""
    list_display = ['participante', 'enabled', 'nova_rodada', 'lembrete_prazo', 
                   'resultados_publicados', 'ranking_atualizado', 'data_atualizacao']
    list_filter = ['enabled', 'nova_rodada', 'lembrete_prazo', 'resultados_publicados', 'ranking_atualizado']
    search_fields = ['participante__nome_exibicao', 'participante__user__username']
    readonly_fields = ['data_criacao', 'data_atualizacao']
    ordering = ['-data_atualizacao']
    
    fieldsets = (
        ('Participante', {
            'fields': ('participante',)
        }),
        ('Configurações Gerais', {
            'fields': ('enabled',)
        }),
        ('Tipos de Notificação', {
            'fields': ('nova_rodada', 'lembrete_prazo', 'resultados_publicados', 'ranking_atualizado')
        }),
        ('Dados Técnicos', {
            'fields': ('push_subscription', 'data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando
            return self.readonly_fields + ['participante']
        return self.readonly_fields


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin para Notificações"""
    list_display = ['participante', 'tipo', 'titulo_resumido', 'status', 'criada_em', 'enviada_em']
    list_filter = ['tipo', 'status', 'criada_em']
    search_fields = ['participante__nome_exibicao', 'titulo', 'mensagem']
    readonly_fields = ['criada_em', 'enviada_em', 'clicada_em', 'push_id']
    ordering = ['-criada_em']
    
    fieldsets = (
        ('Destinatário', {
            'fields': ('participante',)
        }),
        ('Conteúdo', {
            'fields': ('tipo', 'titulo', 'mensagem', 'url_acao')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Relacionamentos', {
            'fields': ('rodada_relacionada',)
        }),
        ('Timestamps', {
            'fields': ('criada_em', 'enviada_em', 'clicada_em'),
            'classes': ('collapse',)
        }),
        ('Dados Técnicos', {
            'fields': ('push_id',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['reenviar_notificacao', 'marcar_como_enviada', 'criar_notificacao_massa']
    
    def titulo_resumido(self, obj):
        if len(obj.titulo) > 30:
            return f"{obj.titulo[:30]}..."
        return obj.titulo
    titulo_resumido.short_description = 'Título'
    
    def reenviar_notificacao(self, request, queryset):
        """Action para reenviar notificações"""
        from .views import send_push_notification
        
        count = 0
        for notification in queryset:
            if send_push_notification(notification):
                count += 1
        
        self.message_user(request, f'{count} notificação(ões) reenviada(s) com sucesso!')
    reenviar_notificacao.short_description = 'Reenviar notificações selecionadas'
    
    def marcar_como_enviada(self, request, queryset):
        """Action para marcar notificações como enviadas"""
        updated = queryset.update(status='sent', enviada_em=timezone.now())
        self.message_user(request, f'{updated} notificação(ões) marcada(s) como enviada(s)!')
    marcar_como_enviada.short_description = 'Marcar como enviadas'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando
            return self.readonly_fields + ['participante', 'tipo']
        return self.readonly_fields
    
    def criar_notificacao_massa(self, request, queryset):
        """Action para ir para página de criação em massa"""
        return HttpResponseRedirect('/admin/bolao/notification/envio-massa/')
    criar_notificacao_massa.short_description = '🚀 Criar notificação em massa'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('envio-massa/', self.admin_site.admin_view(self.envio_massa_view), 
                 name='bolao_notification_envio_massa'),
        ]
        return custom_urls + urls
    
    def envio_massa_view(self, request):
        """Página para envio de notificações em massa"""
        if request.method == 'POST':
            form = NotificationForm(request.POST)
            
            if form.is_valid():
                # Processar envio
                tipo = form.cleaned_data['tipo']
                titulo = form.cleaned_data['titulo']
                mensagem = form.cleaned_data['mensagem']
                url_acao = form.cleaned_data.get('url_acao', '')
                destinatarios = form.cleaned_data['destinatarios']
                participantes_selecionados = form.cleaned_data.get('participantes_selecionados', [])
                rodada_relacionada = form.cleaned_data.get('rodada_relacionada')
                enviar_imediatamente = form.cleaned_data['enviar_imediatamente']
                
                # Determinar participantes
                if destinatarios == 'todos':
                    participantes = Participante.objects.all()
                elif destinatarios == 'ativos':
                    participantes = Participante.objects.filter(ativo=True)
                elif destinatarios == 'com_notifs':
                    # Participantes com notificações ativadas
                    participantes_com_settings = NotificationSettings.objects.filter(enabled=True).values_list('participante', flat=True)
                    participantes = Participante.objects.filter(
                        id__in=participantes_com_settings,
                        ativo=True
                    )
                elif destinatarios == 'selecionados':
                    participantes = participantes_selecionados
                
                # Criar notificações
                notifications_created = []
                
                for participante in participantes:
                    notification = Notification.objects.create(
                        participante=participante,
                        tipo=tipo,
                        titulo=titulo,
                        mensagem=mensagem,
                        rodada_relacionada=rodada_relacionada,
                        url_acao=url_acao
                    )
                    notifications_created.append(notification)
                
                # Enviar se solicitado
                if enviar_imediatamente:
                    from .views import send_push_notification
                    
                    enviadas = 0
                    for notification in notifications_created:
                        if send_push_notification(notification):
                            enviadas += 1
                    
                    messages.success(request, 
                        f'🎉 Notificação criada e enviada para {len(notifications_created)} participante(s)! '
                        f'{enviadas} entregue(s) com sucesso.')
                else:
                    messages.success(request, 
                        f'📝 Notificação criada para {len(notifications_created)} participante(s)! '
                        f'Use as actions acima para enviá-las.')
                
                return redirect('/admin/bolao/notification/')
        else:
            form = NotificationForm()
        
        context = {
            'form': form,
            'title': '🚀 Envio de Notificações em Massa',
            'subtitle': 'Envie notificações personalizadas para todos os participantes',
            'participantes_count': 0,
            'opts': self.model._meta,
            'has_change_permission': True,
            **self._get_notification_stats(),
        }
        
        return render(request, 'admin/bolao/enviar_notificacao.html', context)

    @staticmethod
    def _get_notification_stats():
        """Retorna estatísticas para o painel de notificações"""
        from datetime import timedelta
        hoje = timezone.now().date()
        return {
            'total_participantes': Participante.objects.filter(ativo=True).count(),
            'com_notifs_ativadas': NotificationSettings.objects.filter(enabled=True).count(),
            'com_push_subscription': NotificationSettings.objects.exclude(push_subscription__isnull=True).exclude(push_subscription={}).count(),
            'notifs_enviadas_hoje': Notification.objects.filter(criada_em__date=hoje).count(),
        }
