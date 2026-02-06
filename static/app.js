// Главный файл приложения - инициализация всех модулей
class App {
    constructor() {
        this.modules = new Map();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeModules();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.onDOMReady();
        });
        
        window.addEventListener('load', () => {
            this.onWindowLoad();
        });
        
        window.addEventListener('beforeunload', () => {
            this.onBeforeUnload();
        });
    }

    onDOMReady() {
        this.initializeModules();
    }

    onWindowLoad() {
        this.finalizeInitialization();
    }

    onBeforeUnload() {
        this.cleanup();
    }

    initializeModules() {
        // Инициализируем модули в правильном порядке
        this.initializeModule('wizard', () => {
            if (window.wizardManager) {
                return window.wizardManager;
            }
            // Если wizardManager не найден, попробуем инициализировать его
            if (typeof WizardManager !== 'undefined') {
                window.wizardManager = new WizardManager();
                return window.wizardManager;
            }
            return null;
        });
        
        this.initializeModule('htmlEditor', () => {
            if (window.htmlEditor) {
                return window.htmlEditor;
            }
            return null;
        });
        
        this.initializeModule('formManager', () => {
            if (window.formManager) {
                return window.formManager;
            }
            return null;
        });
        
        this.initializeModule('modalManager', () => {
            if (window.modalManager) {
                return window.modalManager;
            }
            return null;
        });
        
        this.initializeModule('contentBlockManager', () => {
            if (window.contentBlockManager) {
                return window.contentBlockManager;
            }
            return null;
        });
    }

    initializeModule(name, initializer) {
        try {
            const module = initializer();
            if (module) {
                this.modules.set(name, module);
                // Модуль инициализирован
            } else {
                console.warn(`App: Модуль ${name} не найден`);
            }
        } catch (error) {
            console.error(`App: Ошибка инициализации модуля ${name}:`, error);
        }
    }

    finalizeInitialization() {
        // Инициализация завершена
        this.setupGlobalEventHandlers();
        
        // Добавляем глобальные функции для совместимости
        this.setupGlobalFunctions();
    }
    
    setupGlobalFunctions() {
        // Fallback для toggleInputType на случай, если wizard.js еще не загрузился
        if (!window.toggleInputType) {
            window.toggleInputType = (fieldName, type) => {
                console.warn('toggleInputType: wizardManager не инициализирован, попробуйте позже');
                // Попробуем снова через небольшую задержку
                setTimeout(() => {
                    if (window.wizardManager && typeof window.wizardManager.toggleInputType === 'function') {
                        return window.wizardManager.toggleInputType(fieldName, type);
                    }
                }, 100);
            };
        }
        // Глобальные функции настроены
    }

    setupGlobalEventHandlers() {
        // Обработчики для глобальных событий
        this.setupNavigationHandlers();
        this.setupFormHandlers();
        this.setupModalHandlers();
    }

    setupNavigationHandlers() {
        // Обработчики для навигации
        const navLinks = document.querySelectorAll('nav a, .nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                this.handleNavigation(e, link);
            });
        });
    }

    setupFormHandlers() {
        // Обработчики для форм
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.handleFormSubmit(e, form);
            });
        });
    }

    setupModalHandlers() {
        // Обработчики для модальных окон
        const modalTriggers = document.querySelectorAll('[data-modal]');
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                this.handleModalTrigger(e, trigger);
            });
        });
    }

    handleNavigation(e, link) {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
            e.preventDefault();
            this.scrollToSection(href.substring(1));
        }
    }

    handleFormSubmit(e, form) {
        // Дополнительная обработка отправки форм
        const formData = new FormData(form);
        // Отправка формы
    }

    handleModalTrigger(e, trigger) {
        const modalId = trigger.getAttribute('data-modal');
        if (modalId && this.modules.has('modalManager')) {
            e.preventDefault();
            this.modules.get('modalManager').openModal(modalId);
        }
    }

    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.scrollIntoView({ behavior: 'smooth' });
        }
    }

    // Методы для работы с модулями
    getModule(name) {
        return this.modules.get(name);
    }

    hasModule(name) {
        return this.modules.has(name);
    }

    // Методы для работы с уведомлениями
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Стили для уведомления
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        // Цвета для разных типов уведомлений
        const colors = {
            info: '#2563eb',
            success: '#059669',
            warning: '#d97706',
            error: '#dc2626'
        };
        
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // Анимация появления
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Автоматическое скрытие
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, duration);
    }

    // Методы для работы с загрузкой
    showLoading(message = 'Загрузка...') {
        if (this.modules.has('modalManager')) {
            return this.modules.get('modalManager').showLoading(message);
        }
        return null;
    }

    hideLoading(modalId) {
        if (this.modules.has('modalManager') && modalId) {
            this.modules.get('modalManager').hideLoading(modalId);
        }
    }

    // Методы для работы с формами
    validateForm(formId) {
        if (this.modules.has('formManager')) {
            return this.modules.get('formManager').validateForm(formId);
        }
        return false;
    }

    getFormData(formId) {
        if (this.modules.has('formManager')) {
            return this.modules.get('formManager').getFormData(formId);
        }
        return {};
    }

    setFormData(formId, data) {
        if (this.modules.has('formManager')) {
            this.modules.get('formManager').setFormData(formId, data);
        }
    }

    // Методы для работы с модальными окнами
    showModal(modalId) {
        if (this.modules.has('modalManager')) {
            this.modules.get('modalManager').openModal(modalId);
        }
    }

    hideModal(modalId) {
        if (this.modules.has('modalManager')) {
            this.modules.get('modalManager').closeModal(modalId);
        }
    }

    // Методы для работы с мастером заполнения
    openWizard() {
        // Используем встроенную функцию мастера из шаблона
        if (typeof window.openWizardModal === 'function') {
            window.openWizardModal();
        } else {
            console.error('openWizardModal function not found');
            this.showNotification('Мастер заполнения недоступен', 'error');
        }
    }

    // Методы для работы с блоками контента
    createContentBlock(type, content, isEditable = false) {
        if (this.modules.has('contentBlockManager')) {
            return this.modules.get('contentBlockManager').createBlock(type, content, isEditable);
        }
        return null;
    }

    // Методы для работы с HTML редактором
    initializeHtmlEditors() {
        if (this.modules.has('htmlEditor')) {
            this.modules.get('htmlEditor').initializeHtmlEditors();
        }
    }

    // Методы для очистки
    cleanup() {
        // Очистка всех модулей
        this.modules.forEach((module, name) => {
            if (module.cleanup) {
                try {
                    module.cleanup();
                    // Модуль очищен
                } catch (error) {
                    console.error(`App: Ошибка очистки модуля ${name}:`, error);
                }
            }
        });
        
        this.modules.clear();
        // Очистка завершена
    }

    // Методы для отладки
    debug() {
        return {
            wizard: this.hasModule('wizard'),
            htmlEditor: this.hasModule('htmlEditor'),
            formManager: this.hasModule('formManager'),
            modalManager: this.hasModule('modalManager'),
            contentBlockManager: this.hasModule('contentBlockManager')
        };
    }
}

// Инициализация приложения
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new App();
    // Экспорт для глобального доступа после инициализации
    window.app = app;
});

// App functions exported

// Дополнительная проверка готовности
setTimeout(() => {
    // Проверка доступности функций выполнена
}, 1000);

// Утилиты для глобального доступа
window.showNotification = (message, type, duration) => {
    if (app) {
        app.showNotification(message, type, duration);
    }
};

window.showLoading = (message) => {
    if (app) {
        return app.showLoading(message);
    }
    return null;
};

window.hideLoading = (modalId) => {
    if (app) {
        app.hideLoading(modalId);
    }
};

window.openWizard = () => {
    // openWizard вызван
    
    // Проверяем авторизацию пользователя
    // Раньше проверяли по .user-box, но этот блок может отсутствовать в текущем шаблоне.
    // Надёжнее ориентироваться на элементы шапки, которые рендерятся только для авторизованных.
    const isAuthenticated =
        document.body.querySelector('.nav-auth-user') !== null ||
        document.body.querySelector('form[action="/users/logout"]') !== null;
    if (!isAuthenticated) {
        // Пользователь не авторизован
        alert('Для доступа к мастеру заполнения необходимо войти в систему');
        // Открываем модальное окно входа
        const loginBtn = document.getElementById('openLoginModalBtn');
        if (loginBtn) {
            loginBtn.click();
        }
        return;
    }
    
    // Для обычного мастера явно выключаем режим sidebar мастера
    window.IS_SIDEBAR_WIZARD = false;
    
    // Новый мастер для основных сведений реализован в static/wizard.js (WizardManager).
    if (window.wizardManager && typeof window.wizardManager.open === 'function') {
        window.wizardManager.open();
    } else if (typeof window.openWizardModal === 'function') {
        // Фолбэк на старый мастер, если по какой-то причине WizardManager не инициализировался
        window.openWizardModal();
    } else if (app && app.openWizard) {
        app.openWizard();
    } else {
        console.error('openWizard function not available');
        alert('Мастер заполнения недоступен');
    }
};

// Инициализация при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Инициализация приложения
    });
} else {
    // Инициализация приложения (DOM уже готов)
}
