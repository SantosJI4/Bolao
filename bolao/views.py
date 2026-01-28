from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, F
from django.conf import settings
from .models import Rodada, Jogo, Palpite, Participante, Classificacao, Time
from .forms import PerfilParticipanteForm


def home(request):
    """Página inicial mostrando rodadas e status"""
    rodada_atual = Rodada.objects.filter(ativa=True).first()
    rodadas_futuras = Rodada.objects.filter(data_inicio__gt=timezone.now()).order_by('numero')[:3]
    rodadas_passadas = Rodada.objects.filter(data_fim__lt=timezone.now()).order_by('-numero')[:3]
    
    # Se o usuário estiver logado, pegar o participante
    participante = None
    if request.user.is_authenticated:
        try:
            participante = request.user.participante
        except:
            pass
    
    context = {
        'rodada_atual': rodada_atual,
        'rodadas_futuras': rodadas_futuras,
        'rodadas_passadas': rodadas_passadas,
        'participante': participante,
    }
    
    return render(request, 'bolao/home.html', context)


@login_required
def rodada_palpites(request, rodada_id):
    """Página para fazer palpites da rodada atual"""
    rodada = get_object_or_404(Rodada, id=rodada_id)
    
    # Verifica se o usuário tem um participante associado
    try:
        participante = request.user.participante
    except Participante.DoesNotExist:
        messages.error(request, "Você não está cadastrado como participante do bolão. Entre em contato com o administrador.")
        return redirect('home')
    
    # Verifica se ainda pode palpitar
    if not rodada.pode_palpitar:
        messages.error(request, "Esta rodada não está disponível para palpites.")
        return redirect('home')
    
    jogos = rodada.jogo_set.all().order_by('data_hora')
    
    if request.method == 'POST':
        todos_palpites_validos = True
        palpites_salvos = []
        
        for jogo in jogos:
            gols_casa_key = f'gols_casa_{jogo.id}'
            gols_visitante_key = f'gols_visitante_{jogo.id}'
            
            if gols_casa_key in request.POST and gols_visitante_key in request.POST:
                try:
                    gols_casa = int(request.POST[gols_casa_key])
                    gols_visitante = int(request.POST[gols_visitante_key])
                    
                    if gols_casa >= 0 and gols_visitante >= 0 and gols_casa <= 20 and gols_visitante <= 20:
                        palpite, created = Palpite.objects.get_or_create(
                            participante=participante,
                            jogo=jogo,
                            defaults={
                                'gols_casa_palpite': gols_casa,
                                'gols_visitante_palpite': gols_visitante
                            }
                        )
                        
                        if not created:
                            palpite.gols_casa_palpite = gols_casa
                            palpite.gols_visitante_palpite = gols_visitante
                            palpite.save()
                        
                        palpites_salvos.append(palpite)
                except (ValueError, TypeError):
                    continue
        
        if palpites_salvos:
            messages.success(request, f"Palpites salvos com sucesso! {len(palpites_salvos)} jogos.")
            return redirect('home')
        else:
            messages.error(request, "Nenhum palpite foi salvo. Verifique os dados.")
    
    # Buscar palpites existentes
    palpites_existentes = {}
    for palpite in Palpite.objects.filter(participante=participante, jogo__rodada=rodada):
        palpites_existentes[palpite.jogo.id] = palpite
    
    context = {
        'rodada': rodada,
        'jogos': jogos,
        'participante': participante,
        'palpites_existentes': palpites_existentes,
    }
    
    return render(request, 'bolao/palpites.html', context)


def resultados_rodada(request, rodada_id):
    """Página para ver resultados de uma rodada específica"""
    rodada = get_object_or_404(Rodada, id=rodada_id)
    jogos = rodada.jogo_set.all().order_by('data_hora')
    
    # Se o usuário estiver logado, mostrar seus palpites
    palpites_usuario = {}
    if request.user.is_authenticated:
        try:
            participante = request.user.participante
            for palpite in Palpite.objects.filter(participante=participante, jogo__rodada=rodada):
                palpites_usuario[palpite.jogo.id] = palpite
        except:
            pass
    
    context = {
        'rodada': rodada,
        'jogos': jogos,
        'palpites_usuario': palpites_usuario,
    }
    
    return render(request, 'bolao/resultados.html', context)


def classificacao(request):
    """Página da classificação geral"""
    classificacoes = Classificacao.objects.all().order_by('posicao')
    
    # Estatísticas gerais
    total_participantes = Participante.objects.filter(ativo=True).count()
    total_jogos_finalizados = Jogo.objects.filter(resultado_finalizado=True).count()
    
    context = {
        'classificacoes': classificacoes,
        'total_participantes': total_participantes,
        'total_jogos_finalizados': total_jogos_finalizados,
    }
    
    return render(request, 'bolao/classificacao.html', context)


def login_participante(request):
    """Página de login para participantes"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Verifica se o usuário tem um participante associado
            try:
                participante = user.participante
                if participante.ativo:
                    auth_login(request, user)
                    messages.success(request, f"Bem-vindo(a), {participante.nome_exibicao}!")
                    return redirect('home')
                else:
                    messages.error(request, "Sua conta está inativa. Entre em contato com o administrador.")
            except Participante.DoesNotExist:
                messages.error(request, "Usuário não é um participante do bolão.")
        else:
            messages.error(request, "Usuário ou senha incorretos.")
    
    return render(request, 'bolao/login.html')


@login_required
def logout_participante(request):
    """Logout do participante"""
    auth_logout(request)
    messages.success(request, "Você foi desconectado com sucesso.")
    return redirect('home')


def perfil_participante(request, participante_id):
    """Página do perfil detalhado de um participante"""
    participante = get_object_or_404(Participante, id=participante_id, ativo=True)
    
    # Buscar estatísticas do participante
    palpites = Palpite.objects.filter(participante=participante, jogo__resultado_finalizado=True)
    
    total_palpites = palpites.count()
    acertos = palpites.filter(
        # Placar exato
        Q(gols_casa_palpite=F('jogo__gols_casa'), gols_visitante_palpite=F('jogo__gols_visitante')) |
        # Acertou o resultado (vitória casa)
        Q(gols_casa_palpite__gt=F('gols_visitante_palpite'), jogo__gols_casa__gt=F('jogo__gols_visitante')) |
        # Acertou o resultado (empate)
        Q(gols_casa_palpite=F('gols_visitante_palpite'), jogo__gols_casa=F('jogo__gols_visitante')) |
        # Acertou o resultado (vitória visitante)
        Q(gols_casa_palpite__lt=F('gols_visitante_palpite'), jogo__gols_casa__lt=F('jogo__gols_visitante'))
    ).count()
    
    empates_acertados = palpites.filter(
        gols_casa_palpite=F('gols_visitante_palpite'),
        jogo__gols_casa=F('jogo__gols_visitante')
    ).count()
    
    vitorias_acertadas = palpites.filter(
        Q(gols_casa_palpite__gt=F('gols_visitante_palpite'), jogo__gols_casa__gt=F('jogo__gols_visitante')) |
        Q(gols_casa_palpite__lt=F('gols_visitante_palpite'), jogo__gols_casa__lt=F('jogo__gols_visitante'))
    ).count()
    
    # Palpites recentes
    palpites_recentes = palpites.order_by('-data_palpite')[:10]
    
    # Classificação atual
    try:
        classificacao_atual = Classificacao.objects.get(participante=participante)
    except:
        classificacao_atual = None
    
    context = {
        'participante': participante,
        'total_palpites': total_palpites,
        'acertos': acertos,
        'empates_acertados': empates_acertados,
        'vitorias_acertadas': vitorias_acertadas,
        'palpites_recentes': palpites_recentes,
        'classificacao_atual': classificacao_atual,
        'porcentagem_acerto': round((acertos / total_palpites * 100), 1) if total_palpites > 0 else 0,
    }
    
    return render(request, 'bolao/perfil.html', context)


@login_required
def editar_perfil(request):
    """Página para editar o próprio perfil"""
    try:
        participante = request.user.participante
    except Participante.DoesNotExist:
        messages.error(request, "Você não está cadastrado como participante do bolão.")
        return redirect('home')
    
    if request.method == 'POST':
        form = PerfilParticipanteForm(request.POST, request.FILES, instance=participante)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil_participante', participante_id=participante.id)
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = PerfilParticipanteForm(instance=participante)
    
    context = {
        'form': form,
        'participante': participante
    }
    
    return render(request, 'bolao/editar_perfil.html', context)


def csrf_failure(request, reason=""):
    """
    View personalizada para falhas de CSRF
    Não mata a produção, oferece uma experiência amigável
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log do erro para debug
    logger.warning(f"CSRF Failure: {reason}")
    logger.warning(f"Path: {request.path}")
    logger.warning(f"Method: {request.method}")
    logger.warning(f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
    
    # Contexto para o template
    context = {
        'message': 'Verificação de segurança necessária. Recarregue a página.',
        'reason': reason,
        'path': request.path,
        'can_retry': True,
    }
    
    # Em desenvolvimento, mostra detalhes
    if settings.DEBUG:
        context.update({
            'debug_info': {
                'reason': reason,
                'path': request.path,
                'method': request.method,
                'headers': dict(request.headers),
            }
        })
    
    # Renderiza página amigável em vez de erro brutal
    return render(request, 'bolao/csrf_error.html', context, status=403)
