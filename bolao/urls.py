from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_participante, name='login'),
    path('logout/', views.logout_participante, name='logout'),
    path('rodada/<int:rodada_id>/palpites/', views.rodada_palpites, name='rodada_palpites'),
    path('rodada/<int:rodada_id>/resultados/', views.resultados_rodada, name='resultados_rodada'),
    path('classificacao/', views.classificacao, name='classificacao'),
    path('participante/<int:participante_id>/', views.perfil_participante, name='perfil_participante'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('termos/', views.termos_uso, name='termos_uso'),
    path('atualizacoes/', views.atualizacoes, name='atualizacoes'),
    path('marcar-atualizacao-vista/<str:versao>/', views.marcar_atualizacao_vista, name='marcar_atualizacao_vista'),
]