// Модуль для работы с модальными окнами
class ModalManager {
    constructor() {
        this.modals = new Map();
        this.activeModal = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeModals();
        });
        
        // Закрытие по Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.closeModal(this.activeModal);
            }
        });
    }

    initializeModals() {
        const modalElements = document.querySelectorAll('.modal');
        modalElements.forEach(modal => {
            this.registerModal(modal);
        });
    }

    registerModal(modal) {
        const modalId = modal.id || 'modal_' + Date.now();
        modal.id = modalId;
        
        const modalData = {
            element: modal,
            id: modalId,
            backdrop: modal.querySelector('.modal-backdrop'),
            content: modal.querySelector('.modal-content'),
            closeButtons: modal.querySelectorAll('.modal-close, .close-btn'),
            isOpen: false,
            onOpen: null,
            onClose: null,
            onConfirm: null,
            onCancel: null
        };
        
        this.modals.set(modalId, modalData);
        this.setupModalEvents(modalData);
    }

    setupModalEvents(modalData) {
        // Обработчики для кнопок закрытия
        modalData.closeButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.closeModal(modalData.id);
            });
        });
        
        // Обработчик для клика по backdrop
        if (modalData.backdrop) {
            modalData.backdrop.addEventListener('click', (e) => {
                if (e.target === modalData.backdrop) {
                    this.closeModal(modalData.id);
                }
            });
        }
        
        // Обработчик для клика по content
        if (modalData.content) {
            modalData.content.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }

    createModal(options = {}) {
        const {
            id = 'modal_' + Date.now(),
            title = 'Модальное окно',
            content = '',
            size = 'medium',
            closable = true,
            backdrop = true,
            keyboard = true,
            onOpen = null,
            onClose = null,
            onConfirm = null,
            onCancel = null
        } = options;
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = id;
        
        const backdropElement = backdrop ? '<div class="modal-backdrop"></div>' : '';
        
        modal.innerHTML = `
            ${backdropElement}
            <div class="modal-content modal-${size}">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    ${closable ? '<button class="modal-close close-btn">&times;</button>' : ''}
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${onCancel ? '<button class="btn btn-secondary modal-cancel">Отмена</button>' : ''}
                    ${onConfirm ? '<button class="btn btn-primary modal-confirm">Подтвердить</button>' : ''}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const modalData = {
            element: modal,
            id: id,
            backdrop: modal.querySelector('.modal-backdrop'),
            content: modal.querySelector('.modal-content'),
            closeButtons: modal.querySelectorAll('.modal-close, .close-btn'),
            isOpen: false,
            onOpen: onOpen,
            onClose: onClose,
            onConfirm: onConfirm,
            onCancel: onCancel
        };
        
        this.modals.set(id, modalData);
        this.setupModalEvents(modalData);
        
        return id;
    }

    openModal(modalId) {
        const modalData = this.modals.get(modalId);
        if (!modalData || modalData.isOpen) return;
        
        // Закрываем активное модальное окно, если есть
        if (this.activeModal) {
            this.closeModal(this.activeModal);
        }
        
        modalData.isOpen = true;
        this.activeModal = modalId;
        
        modalData.element.style.display = 'block';
        document.body.classList.add('modal-open');
        
        // Анимация появления
        setTimeout(() => {
            modalData.element.classList.add('show');
        }, 10);
        
        // Вызов обработчика открытия
        if (modalData.onOpen) {
            modalData.onOpen(modalData);
        }
        
        // Фокус на модальном окне
        const focusableElement = modalData.element.querySelector('input, button, textarea, select, [tabindex]:not([tabindex="-1"])');
        if (focusableElement) {
            focusableElement.focus();
        }
    }

    closeModal(modalId) {
        const modalData = this.modals.get(modalId);
        if (!modalData || !modalData.isOpen) return;
        
        modalData.isOpen = false;
        this.activeModal = null;
        
        // Анимация исчезновения
        modalData.element.classList.remove('show');
        
        setTimeout(() => {
            modalData.element.style.display = 'none';
            document.body.classList.remove('modal-open');
        }, 300);
        
        // Вызов обработчика закрытия
        if (modalData.onClose) {
            modalData.onClose(modalData);
        }
    }

    toggleModal(modalId) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;
        
        if (modalData.isOpen) {
            this.closeModal(modalId);
        } else {
            this.openModal(modalId);
        }
    }

    destroyModal(modalId) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;
        
        if (modalData.isOpen) {
            this.closeModal(modalId);
        }
        
        modalData.element.remove();
        this.modals.delete(modalId);
    }

    // Специальные методы для различных типов модальных окон
    showAlert(message, title = 'Уведомление', type = 'info') {
        const modalId = this.createModal({
            title: title,
            content: `
                <div class="alert alert-${type}">
                    <p>${message}</p>
                </div>
            `,
            size: 'small',
            onConfirm: () => this.closeModal(modalId)
        });
        
        this.openModal(modalId);
        return modalId;
    }

    showConfirm(message, title = 'Подтверждение', confirmText = 'Да', cancelText = 'Нет') {
        return new Promise((resolve) => {
            const modalId = this.createModal({
                title: title,
                content: `
                    <div class="alert alert-warning">
                        <p>${message}</p>
                    </div>
                `,
                size: 'small',
                onConfirm: () => {
                    this.closeModal(modalId);
                    resolve(true);
                },
                onCancel: () => {
                    this.closeModal(modalId);
                    resolve(false);
                }
            });
            
            // Обновляем текст кнопок
            const modalData = this.modals.get(modalId);
            if (modalData) {
                const confirmBtn = modalData.element.querySelector('.modal-confirm');
                const cancelBtn = modalData.element.querySelector('.modal-cancel');
                
                if (confirmBtn) confirmBtn.textContent = confirmText;
                if (cancelBtn) cancelBtn.textContent = cancelText;
            }
            
            this.openModal(modalId);
        });
    }

    showPrompt(message, title = 'Ввод данных', defaultValue = '') {
        return new Promise((resolve) => {
            const inputId = 'prompt_input_' + Date.now();
            const modalId = this.createModal({
                title: title,
                content: `
                    <div class="form-group">
                        <label for="${inputId}">${message}</label>
                        <input type="text" id="${inputId}" class="form-control" value="${defaultValue}" placeholder="Введите значение">
                    </div>
                `,
                size: 'small',
                onConfirm: () => {
                    const input = document.getElementById(inputId);
                    const value = input ? input.value : '';
                    this.closeModal(modalId);
                    resolve(value);
                },
                onCancel: () => {
                    this.closeModal(modalId);
                    resolve(null);
                }
            });
            
            this.openModal(modalId);
            
            // Фокус на поле ввода
            setTimeout(() => {
                const input = document.getElementById(inputId);
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 100);
        });
    }

    showLoading(message = 'Загрузка...', title = 'Пожалуйста, подождите') {
        const modalId = this.createModal({
            title: title,
            content: `
                <div class="loading-container">
                    <div class="spinner"></div>
                    <p>${message}</p>
                </div>
            `,
            size: 'small',
            closable: false,
            backdrop: true
        });
        
        this.openModal(modalId);
        return modalId;
    }

    hideLoading(modalId) {
        if (modalId) {
            this.closeModal(modalId);
        }
    }

    // Методы для работы с содержимым модального окна
    setContent(modalId, content) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;
        
        const body = modalData.element.querySelector('.modal-body');
        if (body) {
            body.innerHTML = content;
        }
    }

    setTitle(modalId, title) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;
        
        const titleElement = modalData.element.querySelector('.modal-title');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    // Методы для работы с кнопками
    setButtonText(modalId, buttonType, text) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;
        
        const button = modalData.element.querySelector(`.modal-${buttonType}`);
        if (button) {
            button.textContent = text;
        }
    }

    setButtonHandler(modalId, buttonType, handler) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;
        
        const button = modalData.element.querySelector(`.modal-${buttonType}`);
        if (button) {
            button.onclick = handler;
        }
    }

    // Методы для работы с размерами
    setSize(modalId, size) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;
        
        const content = modalData.element.querySelector('.modal-content');
        if (content) {
            content.className = content.className.replace(/modal-\w+/, '');
            content.classList.add(`modal-${size}`);
        }
    }

    // Методы для работы с видимостью
    isOpen(modalId) {
        const modalData = this.modals.get(modalId);
        return modalData ? modalData.isOpen : false;
    }

    getActiveModal() {
        return this.activeModal;
    }

    getAllModals() {
        return Array.from(this.modals.keys());
    }
}

// Инициализация менеджера модальных окон
let modalManager;
document.addEventListener('DOMContentLoaded', () => {
    modalManager = new ModalManager();
});

// Экспорт для глобального доступа
window.modalManager = modalManager;
