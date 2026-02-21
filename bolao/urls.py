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
    path('ao-vivo/', views.jogos_ao_vivo, name='jogos_ao_vivo'),
    path('api/atualizar-placares/', views.atualizar_placares_api, name='atualizar_placares_api'),
    # PWA URLs
    path('manifest.json', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('offline/', views.offline_page, name='offline'),
    # Notification URLs
    path('notificacoes/', views.notification_settings, name='notification_settings'),
    path('notification-settings/', views.notification_settings, name='notification_settings_en'),
    path('test-notif/', views.test_notifications_simple, name='test_notifications_simple'),
    path('api/save-push-subscription/', views.save_push_subscription, name='save_push_subscription'),
    path('api/test-notification/', views.test_notification, name='test_notification'),
    path('api/get-new-notifications/', views.get_new_notifications, name='get_new_notifications'),
    path('api/mark-notifications-viewed/', views.mark_notifications_viewed, name='mark_notifications_viewed'),
    path('api/notification-settings/', views.api_notification_settings, name='api_notification_settings'),
    path('api/enable-all-notifications/', views.api_enable_all_notifications, name='api_enable_all_notifications'),
]