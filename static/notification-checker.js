/**
 * Sistema de Notificações em Tempo Real
 * Verifica por novas notificações e as exibe no navegador
 */

class NotificationChecker {
    constructor() {
        this.checkInterval = null;
        this.isChecking = false;
        this.lastCheck = null;
        this.shownNotifications = new Set();
        
        this.init();
    }
    
    async init() {
        // Verificar se o usuário está logado (procurar por elementos específicos)
        if (!document.querySelector('meta[name="csrf-token"]') && 
            !document.querySelector('[name="csrfmiddlewaretoken"]')) {
            console.log('👤 Usuário não logado - verificação de notificações desabilitada');
            return;
        }
        
        console.log('🔔 Sistema de notificações iniciado');
        
        // Aguardar permissão de notificações se ainda não foi concedida
        await this.ensureNotificationPermission();
        
        // Iniciar verificação periódica
        this.startChecking();
        
        // Parar verificação quando a página não estiver visível
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopChecking();
            } else {
                this.startChecking();
            }
        });
    }
    
    async ensureNotificationPermission() {
        if (!('Notification' in window)) {
            console.log('❌ Notificações não suportadas');
            return false;
        }
        
        if (Notification.permission === 'granted') {
            return true;
        }
        
        if (Notification.permission === 'default') {
            // Não solicitar automaticamente, apenas se o usuário interagir
            console.log('ℹ️ Permissão de notificação não solicitada automaticamente');
        }
        
        return Notification.permission === 'granted';
    }
    
    startChecking() {
        if (this.checkInterval) return;
        
        console.log('▶️ Iniciando verificação de notificações (30s)');
        
        // Primeira verificação imediata
        this.checkNewNotifications();
        
        // Verificar a cada 30 segundos
        this.checkInterval = setInterval(() => {
            this.checkNewNotifications();
        }, 30000);
    }
    
    stopChecking() {
        if (this.checkInterval) {
            console.log('⏹️ Parando verificação de notificações');
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
    
    async checkNewNotifications() {
        if (this.isChecking) return;
        
        this.isChecking = true;
        
        try {
            const headers = {
                'Content-Type': 'application/json',
            };
            
            // Adicionar CSRF token se disponível
            const csrfToken = document.querySelector('meta[name="csrf-token"]');
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken.getAttribute('content');
            }
            
            const response = await fetch('/api/get-new-notifications/', {
                method: 'GET',
                credentials: 'same-origin',
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.notifications.length > 0) {
                console.log(`📬 ${data.notifications.length} nova(s) notificação(ões)`);
                
                const notificationIds = [];
                for (const notif of data.notifications) {
                    await this.showNotification(notif);
                    notificationIds.push(notif.id);
                }
                
                // Marcar todas como vistas
                await this.markNotificationsViewed(notificationIds);
            }
            
        } catch (error) {
            console.log('⚠️ Erro ao verificar notificações:', error.message);
        } finally {
            this.isChecking = false;
            this.lastCheck = new Date();
        }
    }
    
    async showNotification(notifData) {
        // Evitar mostrar a mesma notificação duas vezes
        if (this.shownNotifications.has(notifData.id)) {
            return;
        }
        
        this.shownNotifications.add(notifData.id);
        
        // Tentar notificação nativa primeiro
        if (Notification.permission === 'granted') {
            try {
                const notification = new Notification(notifData.titulo, {
                    body: notifData.mensagem,
                    icon: '/static/futfavi.webp',
                    badge: '/static/futfavi.webp',
                    tag: `futamigo-${notifData.id}`,
                    vibrate: [200, 100, 200],
                    requireInteraction: false,
                    silent: false,
                    data: {
                        url: notifData.url_acao,
                        id: notifData.id
                    }
                });
                
                notification.onclick = function() {
                    window.focus();
                    if (notifData.url_acao && notifData.url_acao !== '/') {
                        window.location.href = notifData.url_acao;
                    }
                    notification.close();
                };
                
                // Auto-fechar após 5 segundos
                setTimeout(() => {
                    notification.close();
                }, 5000);
                
                console.log(`🔔 Notificação nativa exibida: ${notifData.titulo}`);
                return;
                
            } catch (error) {
                console.log('⚠️ Notificação nativa falhou:', error.message);
            }
        }
        
        // Fallback: notificação visual na página
        this.showInPageNotification(notifData);
    }
    
    showInPageNotification(notifData) {
        // Criar elemento de notificação
        const notifElement = document.createElement('div');
        notifElement.className = 'futamigo-notification';
        notifElement.innerHTML = `
            <div class="futamigo-notification-content">
                <div class="futamigo-notification-title">${this.escapeHtml(notifData.titulo)}</div>
                <div class="futamigo-notification-body">${this.escapeHtml(notifData.mensagem)}</div>
                <button class="futamigo-notification-close">&times;</button>
            </div>
        `;
        
        // Adicionar estilos se ainda não existem
        this.ensureNotificationStyles();
        
        // Adicionar ao DOM
        document.body.appendChild(notifElement);
        
        // Event listeners
        const closeBtn = notifElement.querySelector('.futamigo-notification-close');
        closeBtn.addEventListener('click', () => {
            this.removeNotification(notifElement);
        });
        
        // Clique na notificação abre URL
        notifElement.addEventListener('click', (e) => {
            if (e.target !== closeBtn && notifData.url_acao && notifData.url_acao !== '/') {
                window.location.href = notifData.url_acao;
            }
        });
        
        // Mostrar com animação
        setTimeout(() => {
            notifElement.classList.add('show');
        }, 100);
        
        // Auto-remover após 5 segundos
        setTimeout(() => {
            this.removeNotification(notifElement);
        }, 5000);
        
        console.log(`📱 Notificação in-page exibida: ${notifData.titulo}`);
    }
    
    removeNotification(element) {
        element.classList.remove('show');
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }, 300);
    }
    
    ensureNotificationStyles() {
        if (document.getElementById('futamigo-notification-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'futamigo-notification-styles';
        style.textContent = `
            .futamigo-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 350px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transform: translateX(400px);
                transition: transform 0.3s ease-in-out;
                cursor: pointer;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .futamigo-notification.show {
                transform: translateX(0);
            }
            
            .futamigo-notification-content {
                padding: 16px;
                position: relative;
            }
            
            .futamigo-notification-title {
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 4px;
                color: #333;
                line-height: 1.3;
            }
            
            .futamigo-notification-body {
                font-size: 13px;
                color: #666;
                line-height: 1.4;
            }
            
            .futamigo-notification-close {
                position: absolute;
                top: 8px;
                right: 8px;
                background: none;
                border: none;
                font-size: 18px;
                color: #999;
                cursor: pointer;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
            }
            
            .futamigo-notification-close:hover {
                background: #f0f0f0;
                color: #666;
            }
            
            .futamigo-notification:hover {
                box-shadow: 0 6px 15px rgba(0,0,0,0.2);
            }
            
            @media (max-width: 400px) {
                .futamigo-notification {
                    right: 10px;
                    left: 10px;
                    max-width: none;
                    transform: translateY(-400px);
                }
                
                .futamigo-notification.show {
                    transform: translateY(0);
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Métodos públicos para controle externo
    forceCheck() {
        this.checkNewNotifications();
    }
    
    getStatus() {
        return {
            isActive: !!this.checkInterval,
            isChecking: this.isChecking,
            lastCheck: this.lastCheck,
            shownCount: this.shownNotifications.size
        };
    }
    
    async markNotificationsViewed(notificationIds) {
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]');
            const headers = {
                'Content-Type': 'application/json',
            };
            
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken.getAttribute('content');
            }
            
            const response = await fetch('/api/mark-notifications-viewed/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: headers,
                body: JSON.stringify({
                    notification_ids: notificationIds
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log(`✅ ${data.marked} notificação(ões) marcada(s) como vista(s)`);
            }
        } catch (error) {
            console.log('⚠️ Erro ao marcar notificações:', error.message);
        }
    }
}

// Inicializar automaticamente quando a página carregar
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', () => {
        window.futamigoNotifications = new NotificationChecker();
    });
}

// Para debug no console
window.debugNotifications = function() {
    if (window.futamigoNotifications) {
        console.log('🔍 Status das notificações:', window.futamigoNotifications.getStatus());
        console.log('🔍 Forçando verificação...');
        window.futamigoNotifications.forceCheck();
    } else {
        console.log('❌ Sistema de notificações não inicializado');
    }
};