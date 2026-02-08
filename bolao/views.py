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
    atualizacao_nao_vista = None
    
    if request.user.is_authenticated:
        try:
            participante = request.user.participante
            
            # Verifica se há atualizações não vistas
            from .models import AtualizacaoSite, AtualizacaoVista
            atualizacoes_ativas = AtualizacaoSite.objects.filter(ativa=True)
            atualizacoes_vistas = AtualizacaoVista.objects.filter(participante=participante).values_list('atualizacao_id', flat=True)
            
            # Pega a atualização mais recente não vista
            atualizacao_nao_vista = atualizacoes_ativas.exclude(id__in=atualizacoes_vistas).first()
            
        except:
            pass
    
    context = {
        'rodada_atual': rodada_atual,
        'rodadas_futuras': rodadas_futuras,
        'rodadas_passadas': rodadas_passadas,
        'participante': participante,
        'atualizacao_nao_vista': atualizacao_nao_vista,
    }
    
    return render(request, 'bolao/home.html', context)


@login_required
def rodada_palpites(request, rodada_id):
    """Página para fazer palpites ou visualizar palpites da rodada"""
    rodada = get_object_or_404(Rodada, id=rodada_id)
    
    # Verifica se o usuário tem um participante associado
    try:
        participante = request.user.participante
    except Participante.DoesNotExist:
        messages.error(request, "Você não está cadastrado como participante do bolão. Entre em contato com o administrador.")
        return redirect('home')
    
    # Se não pode mais palpitar, muda para modo visualização
    pode_palpitar = rodada.pode_palpitar
    
    jogos = rodada.jogo_set.all().order_by('data_hora')
    
    # Buscar palpites existentes do usuário
    palpites_existentes = {}
    for palpite in Palpite.objects.filter(participante=participante, jogo__rodada=rodada):
        palpites_existentes[palpite.jogo.id] = palpite
    
    # Se não pode palpitar, buscar todos os palpites para a planilha
    todos_palpites = {}
    participantes_ativos = []
    if not pode_palpitar:
        participantes_ativos = Participante.objects.filter(ativo=True).order_by('nome_exibicao')
        for jogo in jogos:
            todos_palpites[jogo.id] = {}
            for palpite in Palpite.objects.filter(jogo=jogo):
                todos_palpites[jogo.id][palpite.participante.id] = palpite
    
    if request.method == 'POST' and pode_palpitar:
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
    
    context = {
        'rodada': rodada,
        'jogos': jogos,
        'participante': participante,
        'palpites_existentes': palpites_existentes,
        'pode_palpitar': pode_palpitar,
        'todos_palpites': todos_palpites,
        'participantes_ativos': participantes_ativos,
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
    
    # Calcular pontos totais
    pontos_totais = sum(palpite.pontos_obtidos for palpite in palpites)
    
    # Calcular último saldo (pontos da última rodada)
    from .models import Rodada
    ultima_rodada = Rodada.objects.filter(
        jogo__resultado_finalizado=True
    ).order_by('-numero').first()
    
    ultimo_saldo = 0
    if ultima_rodada:
        palpites_ultima_rodada = palpites.filter(jogo__rodada=ultima_rodada)
        ultimo_saldo = sum(palpite.pontos_obtidos for palpite in palpites_ultima_rodada)
    
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
        'pontos_totais': pontos_totais,
        'ultimo_saldo': ultimo_saldo,
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


def termos_uso(request):
    """Página com os termos de uso do site"""
    return render(request, 'bolao/termos_uso.html')


def atualizacoes(request):
    """Página com todas as atualizações do site"""
    from .models import AtualizacaoSite
    atualizacoes_list = AtualizacaoSite.objects.filter(ativa=True).order_by('-data_lancamento')
    
    context = {
        'atualizacoes': atualizacoes_list,
    }
    
    return render(request, 'bolao/atualizacoes.html', context)


@login_required
@require_POST
def marcar_atualizacao_vista(request, versao):
    """Marca uma atualização como vista pelo usuário"""
    from django.http import JsonResponse
    from .models import AtualizacaoSite, AtualizacaoVista
    
    try:
        participante = request.user.participante
        atualizacao = get_object_or_404(AtualizacaoSite, versao=versao)
        
        # Cria ou atualiza o registro de visualização
        vista, created = AtualizacaoVista.objects.get_or_create(
            participante=participante,
            atualizacao=atualizacao
        )
        
        return JsonResponse({'success': True})
    except:
        return JsonResponse({'success': False}, status=400)


import requests
import json
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http import JsonResponse


def jogos_ao_vivo(request):
    """Página de jogos ao vivo com placares em tempo real"""
    return render(request, 'bolao/jogos_ao_vivo.html')


def atualizar_placares_api(request):
    """API para atualizar placares do Brasileirão - APENAS BRASILEIRÃO SÉRIE A"""
    from django.core.cache import cache
    import requests
    from datetime import datetime, timedelta
    
    # Chaves de cache específicas
    CACHE_KEY = 'brasileirao_placares'
    CACHE_BACKUP_KEY = 'brasileirao_placares_backup'
    CACHE_TIMEOUT = 120  # 2 minutos para jogos ao vivo
    CACHE_BACKUP_TIMEOUT = 1800  # 30 minutos backup
    
    # Tenta pegar do cache primeiro
    placares_cache = cache.get(CACHE_KEY)
    
    if placares_cache:
        return JsonResponse({
            'success': True,
            'jogos': placares_cache['jogos'],
            'ultima_atualizacao': placares_cache['ultima_atualizacao'],
            'fonte': 'cache',
            'proxima_atualizacao': placares_cache.get('proxima_atualizacao')
        })
    
    try:
        # Configuração da API-Football
        API_URL = "https://v3.football.api-sports.io/fixtures"
        
        headers = {
            'X-RapidAPI-Key': 'b20093f89e13ee92bd30872fba5da1fe',
            'X-RapidAPI-Host': 'v3.football.api-sports.io'
        }
        
        jogos_api = []
        fonte = 'sem_dados'
        
        # 1. BUSCAR JOGOS AO VIVO - APENAS BRASILEIRÃO SÉRIE A
        try:
            params_live = {
                'live': 'all'  # Buscar todos os jogos ao vivo
            }
            response_live = requests.get(API_URL, headers=headers, params=params_live, timeout=10)
            
            if response_live.status_code == 200:
                data_live = response_live.json()
                jogos_live_todos = data_live.get('response', [])
                
                # Filtrar APENAS Brasileirão Série A (Liga ID = 71)
                jogos_live_brasileirao = []
                for jogo in jogos_live_todos:
                    if jogo['league']['id'] == 71:  # APENAS Liga 71
                        jogos_live_brasileirao.append(jogo)
                
                if jogos_live_brasileirao:
                    jogos_api.extend(jogos_live_brasileirao)
                    fonte = 'ao_vivo_brasileirao'
                    
        except Exception as e:
            print(f"Erro jogos ao vivo Brasileirão: {e}")
        
        # 2. SE NÃO HÁ JOGOS AO VIVO, BUSCAR PRÓXIMOS JOGOS - APENAS BRASILEIRÃO
        if not jogos_api:
            try:
                hoje = datetime.now()
                
                # Buscar próximos 7 dias
                for i in range(8):
                    data = (hoje + timedelta(days=i)).strftime('%Y-%m-%d')
                    
                    # Testar temporadas: 2025, 2026, 2024
                    for temporada in ['2025', '2026', '2024']:
                        try:
                            params = {
                                'league': '71',  # APENAS Brasileirão Série A
                                'season': temporada,
                                'date': data,
                                'timezone': 'America/Sao_Paulo'
                            }
                            
                            response = requests.get(API_URL, headers=headers, params=params, timeout=10)
                            
                            if response.status_code == 200:
                                data_resp = response.json()
                                jogos_data = data_resp.get('response', [])
                                
                                if jogos_data:
                                    jogos_api.extend(jogos_data)
                                    fonte = f'brasileirao_{temporada}_{data}'
                                    break
                                    
                        except Exception as e:
                            continue
                    
                    if jogos_api:  # Se encontrou jogos, para de buscar
                        break
                            
            except Exception as e:
                print(f"Erro próximos jogos Brasileirão: {e}")
        
        # 3. FALLBACK: ÚLTIMOS JOGOS DO BRASILEIRÃO 2024 PARA DEMONSTRAÇÃO
        if not jogos_api:
            try:
                params_recentes = {
                    'league': '71',  # APENAS Brasileirão Série A
                    'season': '2024',
                    'last': 10,
                    'timezone': 'America/Sao_Paulo'
                }
                
                response_recentes = requests.get(API_URL, headers=headers, params=params_recentes, timeout=10)
                
                if response_recentes.status_code == 200:
                    data_recentes = response_recentes.json()
                    jogos_recentes = data_recentes.get('response', [])
                    
                    if jogos_recentes:
                        jogos_api = jogos_recentes[:8]  # Máximo 8 jogos
                        fonte = 'recentes_brasileirao_2024'
                        
            except Exception as e:
                print(f"Erro fallback Brasileirão: {e}")
        
        # 4. SE AINDA NÃO TEM NADA, DADOS SIMULADOS DO BRASILEIRÃO
        if not jogos_api:
            agora = datetime.now()
            jogos_api = [
                {
                    'fixture': {
                        'id': 999991,
                        'date': agora.isoformat(),
                        'status': {'short': '2H', 'long': 'Second Half', 'elapsed': 67},
                        'venue': {'name': 'Maracanã', 'city': 'Rio de Janeiro'}
                    },
                    'teams': {
                        'home': {'name': 'Flamengo', 'logo': 'https://media.api-sports.io/football/teams/18.png'},
                        'away': {'name': 'Palmeiras', 'logo': 'https://media.api-sports.io/football/teams/130.png'}
                    },
                    'goals': {'home': 2, 'away': 1},
                    'league': {'name': 'Brasileirão Série A', 'round': 'Regular Season - 5', 'country': 'Brazil'}
                },
                {
                    'fixture': {
                        'id': 999992,
                        'date': (agora + timedelta(hours=2)).isoformat(),
                        'status': {'short': 'NS', 'long': 'Not Started', 'elapsed': None},
                        'venue': {'name': 'Neo Química Arena', 'city': 'São Paulo'}
                    },
                    'teams': {
                        'home': {'name': 'Corinthians', 'logo': 'https://media.api-sports.io/football/teams/131.png'},
                        'away': {'name': 'São Paulo', 'logo': 'https://media.api-sports.io/football/teams/126.png'}
                    },
                    'goals': {'home': None, 'away': None},
                    'league': {'name': 'Brasileirão Série A', 'round': 'Regular Season - 5', 'country': 'Brazil'}
                }
            ]
            fonte = 'simulados_brasileirao'
        
        # Processa os jogos encontrados - APENAS BRASILEIRÃO SÉRIE A
        jogos_processados = []
        for jogo in jogos_api:
            try:
                # Filtro adicional: apenas Liga 71 (Brasileirão Série A)
                if jogo['league']['id'] != 71:
                    continue  # Pula jogos que não são do Brasileirão
                
                # Converte horário para fuso do Brasil
                data_jogo = jogo['fixture']['date']
                if isinstance(data_jogo, str):
                    try:
                        dt = datetime.fromisoformat(data_jogo.replace('Z', '+00:00'))
                        data_formatada = dt.strftime('%d/%m %H:%M')
                    except:
                        data_formatada = data_jogo
                else:
                    data_formatada = str(data_jogo)
                
                # Status do jogo
                status = jogo['fixture']['status']['short']
                status_longo = jogo['fixture']['status']['long']
                minuto = jogo['fixture']['status'].get('elapsed')
                
                # Classificar status
                ao_vivo = status in ['1H', '2H', 'HT', 'ET', 'P', 'LIVE']
                finalizado = status in ['FT', 'AET', 'PEN']
                agendado = status in ['TBD', 'NS', 'PST']
                
                # Extrai estatísticas se disponível
                estatisticas = extrair_estatisticas(jogo)
                
                jogo_info = {
                    'id': jogo['fixture']['id'],
                    'time_casa': jogo['teams']['home']['name'],
                    'time_visitante': jogo['teams']['away']['name'],
                    'escudo_casa': jogo['teams']['home'].get('logo', ''),
                    'escudo_visitante': jogo['teams']['away'].get('logo', ''),
                    'gols_casa': jogo['goals']['home'] if jogo['goals']['home'] is not None else 0,
                    'gols_visitante': jogo['goals']['away'] if jogo['goals']['away'] is not None else 0,
                    'status': status,
                    'status_longo': status_longo,
                    'minuto': minuto,
                    'competicao': 'Brasileirão Série A',
                    'rodada': jogo['league'].get('round', 'Rodada'),
                    'horario_formatado': data_formatada,
                    'horario': jogo['fixture']['date'],
                    'estadio': jogo['fixture']['venue']['name'] if jogo['fixture'].get('venue') else None,
                    'cidade': jogo['fixture']['venue']['city'] if jogo['fixture'].get('venue') else None,
                    'ao_vivo': ao_vivo,
                    'finalizado': finalizado,
                    'agendado': agendado,
                    'estatisticas': estatisticas
                }
                jogos_processados.append(jogo_info)
                
            except Exception as e:
                print(f"Erro ao processar jogo: {e}")
                continue
        
        # Ordena: ao vivo primeiro, depois agendados, depois finalizados
        jogos_processados.sort(key=lambda x: (
            0 if x['ao_vivo'] else 1 if x['agendado'] else 2,
            x['horario']
        ))
        
        # Limita a 15 jogos máximo
        jogos_processados = jogos_processados[:15]
        
        # Dados para cache
        proxima_atualizacao = datetime.now() + timedelta(seconds=CACHE_TIMEOUT)
        cache_data = {
            'jogos': jogos_processados,
            'ultima_atualizacao': datetime.now().strftime('%H:%M:%S'),
            'proxima_atualizacao': proxima_atualizacao.strftime('%H:%M:%S'),
            'total_jogos': len(jogos_processados),
            'ao_vivo': len([j for j in jogos_processados if j['ao_vivo']]),
            'agendados': len([j for j in jogos_processados if j['agendado']]),
            'finalizados': len([j for j in jogos_processados if j['finalizado']])
        }
        
        # Salva no cache
        cache.set(CACHE_KEY, cache_data, CACHE_TIMEOUT)
        cache.set(CACHE_BACKUP_KEY, cache_data, CACHE_BACKUP_TIMEOUT)
        
        return JsonResponse({
            'success': True,
            'jogos': jogos_processados,
            'ultima_atualizacao': cache_data['ultima_atualizacao'],
            'proxima_atualizacao': cache_data['proxima_atualizacao'],
            'estatisticas': {
                'total_jogos': cache_data['total_jogos'],
                'ao_vivo': cache_data['ao_vivo'],
                'agendados': cache_data['agendados'],
                'finalizados': cache_data['finalizados']
            },
            'fonte': fonte,
            'debug': f'Buscou {len(jogos_api)} jogos do Brasileirão - fonte: {fonte}'
        })
        
    except Exception as e:
        # Tenta cache backup
        backup_cache = cache.get(CACHE_BACKUP_KEY)
        if backup_cache:
            return JsonResponse({
                'success': True,
                'jogos': backup_cache['jogos'],
                'ultima_atualizacao': backup_cache['ultima_atualizacao'],
                'fonte': 'cache_backup',
                'erro': f'API indisponível: {str(e)}'
            })
        
        # Último recurso: dados simulados do Brasileirão
        return JsonResponse({
            'success': True,
            'jogos': [
                {
                    'id': 999999,
                    'time_casa': 'Flamengo',
                    'time_visitante': 'Palmeiras',
                    'gols_casa': 2,
                    'gols_visitante': 1,
                    'status': '2H',
                    'status_longo': 'Segundo Tempo',
                    'minuto': 67,
                    'ao_vivo': True,
                    'finalizado': False,
                    'agendado': False,
                    'competicao': 'Brasileirão Série A',
                    'rodada': 'Rodada 5',
                    'horario_formatado': datetime.now().strftime('%d/%m %H:%M'),
                    'estadio': 'Maracanã',
                    'cidade': 'Rio de Janeiro',
                    'escudo_casa': '',
                    'escudo_visitante': '',
                    'estatisticas': None
                }
            ],
            'ultima_atualizacao': datetime.now().strftime('%H:%M:%S'),
            'fonte': 'erro_fallback',
            'erro': f'API falhou: {str(e)}',
            'estatisticas': {'total_jogos': 1, 'ao_vivo': 1, 'agendados': 0, 'finalizados': 0}
        })


def extrair_estatisticas(jogo):
    """Extrai estatísticas detalhadas do jogo se disponível"""
    try:
        stats = jogo.get('statistics', [])
        if not stats:
            return None
            
        estatisticas = {
            'casa': {},
            'visitante': {}
        }
        
        # Mapeamento de estatísticas importantes
        stats_map = {
            'Shots on Goal': 'chutes_no_gol',
            'Shots off Goal': 'chutes_para_fora', 
            'Total Shots': 'total_chutes',
            'Ball Possession': 'posse_de_bola',
            'Fouls': 'faltas',
            'Yellow Cards': 'cartoes_amarelos',
            'Red Cards': 'cartoes_vermelhos',
            'Offsides': 'impedimentos',
            'Corner Kicks': 'escanteios',
            'Passes %': 'precisao_passes',
            'expected_goals': 'gols_esperados'
        }
        
        for team_stats in stats:
            team = 'casa' if team_stats['team']['id'] == jogo['teams']['home']['id'] else 'visitante'
            
            for stat in team_stats['statistics']:
                stat_name = stat['type']
                stat_value = stat['value']
                
                if stat_name in stats_map:
                    key = stats_map[stat_name]
                    estatisticas[team][key] = stat_value
        
        return estatisticas
        
    except Exception:
        return None

