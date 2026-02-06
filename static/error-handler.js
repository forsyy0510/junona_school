// Глобальный обработчик ошибок с инструкциями по устранению
class ErrorHandler {
    constructor() {
        this.errorMap = {
            // Сетевые ошибки
            'Failed to fetch': {
                title: 'Ошибка сети',
                message: 'Не удалось подключиться к серверу',
                instructions: [
                    'Проверьте подключение к интернету',
                    'Убедитесь, что сервер запущен и доступен',
                    'Попробуйте обновить страницу (Ctrl+F5)',
                    'Если проблема сохраняется, обратитесь к администратору'
                ]
            },
            'NetworkError': {
                title: 'Ошибка сети',
                message: 'Проблема с сетевым соединением',
                instructions: [
                    'Проверьте подключение к интернету',
                    'Попробуйте перезагрузить страницу',
                    'Проверьте настройки брандмауэра или антивируса'
                ]
            },
            
            // Ошибки авторизации
            'Unauthorized': {
                title: 'Доступ запрещен',
                message: 'Недостаточно прав для выполнения действия',
                instructions: [
                    'Убедитесь, что вы вошли в систему',
                    'Проверьте, что у вас есть права администратора',
                    'Попробуйте выйти и войти снова'
                ]
            },
            '401': {
                title: 'Требуется авторизация',
                message: 'Необходимо войти в систему',
                instructions: [
                    'Нажмите на кнопку "Войти" в верхнем меню',
                    'Введите логин и пароль',
                    'Если забыли пароль, обратитесь к администратору'
                ]
            },
            
            // Ошибки сервера
            '500': {
                title: 'Ошибка сервера',
                message: 'На сервере произошла ошибка',
                instructions: [
                    'Попробуйте повторить действие через несколько минут',
                    'Обновите страницу (Ctrl+F5)',
                    'Если ошибка повторяется, сообщите администратору',
                    'Укажите, какое действие вы пытались выполнить'
                ]
            },
            'Internal Server Error': {
                title: 'Внутренняя ошибка сервера',
                message: 'На сервере произошла непредвиденная ошибка',
                instructions: [
                    'Сохраните информацию об ошибке (нажмите "Скопировать детали")',
                    'Попробуйте повторить действие позже',
                    'Сообщите об ошибке администратору с копией деталей'
                ]
            },
            
            // Ошибки валидации
            'ValidationError': {
                title: 'Ошибка валидации',
                message: 'Проверьте введенные данные',
                instructions: [
                    'Заполните все обязательные поля (отмечены *)',
                    'Проверьте правильность формата данных',
                    'Убедитесь, что размер файла не превышает допустимый',
                    'Проверьте, что файл имеет правильный тип'
                ]
            },
            'File too large': {
                title: 'Файл слишком большой',
                message: 'Размер файла превышает допустимый лимит',
                instructions: [
                    'Максимальный размер файла: 10 МБ',
                    'Попробуйте уменьшить размер файла',
                    'Используйте формат с меньшим размером (например, сжатие изображений)'
                ]
            },
            
            // Ошибки файлов
            'File not found': {
                title: 'Файл не найден',
                message: 'Запрошенный файл не существует',
                instructions: [
                    'Проверьте, что файл не был удален',
                    'Попробуйте загрузить файл снова',
                    'Если файл был удален, восстановите его из резервной копии'
                ]
            },
            
            // Общие ошибки
            'SyntaxError': {
                title: 'Ошибка синтаксиса',
                message: 'Обнаружена ошибка в коде',
                instructions: [
                    'Обновите страницу (Ctrl+F5)',
                    'Очистите кэш браузера',
                    'Если ошибка сохраняется, сообщите администратору'
                ]
            },
            'TypeError': {
                title: 'Ошибка типа данных',
                message: 'Некорректные данные',
                instructions: [
                    'Обновите страницу',
                    'Проверьте, что все поля заполнены корректно',
                    'Попробуйте выполнить действие снова'
                ]
            }
        };
        
        this.init();
    }
    
    init() {
        // Обработка глобальных ошибок JavaScript
        window.addEventListener('error', (event) => {
            this.handleError(event.error || event.message, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });
        
        // Обработка необработанных промисов
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason, {
                type: 'Promise rejection',
                stack: event.reason?.stack
            });
        });
    }
    
    getErrorInfo(error) {
        let errorMessage = '';
        let errorDetails = {};
        
        if (typeof error === 'string') {
            errorMessage = error;
        } else if (error instanceof Error) {
            errorMessage = error.message;
            errorDetails = {
                name: error.name,
                stack: error.stack
            };
        } else if (error && typeof error === 'object') {
            errorMessage = error.message || error.error || JSON.stringify(error);
            errorDetails = error;
        } else {
            errorMessage = 'Неизвестная ошибка';
        }
        
        // Ищем соответствие в errorMap
        for (const [key, value] of Object.entries(this.errorMap)) {
            if (errorMessage.includes(key) || errorDetails.name === key) {
                return {
                    title: value.title,
                    message: value.message,
                    instructions: value.instructions,
                    details: errorDetails,
                    rawError: error
                };
            }
        }
        
        // Если не найдено соответствие, используем общие инструкции
        return {
            title: 'Произошла ошибка',
            message: errorMessage || 'Неизвестная ошибка',
            instructions: [
                'Попробуйте обновить страницу (Ctrl+F5)',
                'Очистите кэш браузера',
                'Проверьте консоль браузера (F12) для дополнительной информации',
                'Если проблема сохраняется, сообщите администратору с деталями ошибки'
            ],
            details: errorDetails,
            rawError: error
        };
    }
    
    showError(errorInfo, context = '') {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.id = `error-${Date.now()}`;
        
        const instructionsHtml = errorInfo.instructions
            .map((instruction, index) => `<li>${instruction}</li>`)
            .join('');
        
        const contextHtml = context ? `<div class="error-context"><strong>Контекст:</strong> ${context}</div>` : '';
        
        errorDiv.innerHTML = `
            <div class="error-notification-content">
                <div class="error-header">
                    <div class="error-icon">⚠️</div>
                    <div class="error-title-section">
                        <h3 class="error-title">${errorInfo.title}</h3>
                        <p class="error-message">${errorInfo.message}</p>
                    </div>
                    <button class="error-close" onclick="this.closest('.error-notification').remove()">✕</button>
                </div>
                ${contextHtml}
                <div class="error-instructions">
                    <strong>Что делать:</strong>
                    <ol>${instructionsHtml}</ol>
                </div>
                <div class="error-actions">
                    <button class="error-action-btn" onclick="window.errorHandler.copyErrorDetails('${errorDiv.id}', event && event.target)">
                        📋 Скопировать детали ошибки
                    </button>
                    <button class="error-action-btn" onclick="window.errorHandler.reloadPage()">
                        🔄 Обновить страницу
                    </button>
                    <button class="error-action-btn secondary" onclick="this.closest('.error-notification').classList.toggle('expanded')">
                        🔍 ${errorInfo.details.stack ? 'Показать детали' : 'Скрыть детали'}
                    </button>
                </div>
                ${errorInfo.details.stack ? `
                    <div class="error-details">
                        <pre>${this.escapeHtml(errorInfo.details.stack)}</pre>
                    </div>
                ` : ''}
            </div>
        `;
        
        // Добавляем стили если их еще нет
        this.addStyles();
        
        // Вставляем в начало body или в специальный контейнер
        const container = document.getElementById('error-container') || document.body;
        container.insertBefore(errorDiv, container.firstChild);
        
        // Автоматически скрываем через 30 секунд, если пользователь не взаимодействует
        setTimeout(() => {
            if (errorDiv && errorDiv.parentNode) {
                errorDiv.style.opacity = '0.7';
            }
        }, 30000);
        
        // Скроллим к ошибке
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    handleError(error, context = '') {
        const errorInfo = this.getErrorInfo(error);
        this.showError(errorInfo, context);
    }
    
    async handleApiError(response, context = '') {
        let errorData = {};
        try {
            const text = await response.text();
            errorData = text ? JSON.parse(text) : {};
        } catch (e) {
            // Если не удалось распарсить JSON, используем текст
            errorData = { error: await response.text() };
        }
        
        const statusCode = response.status;
        const statusText = response.statusText;
        
        let errorInfo = {};
        
        // Проверяем стандартные коды ошибок
        switch (statusCode) {
            case 400:
                errorInfo = {
                    title: 'Неверный запрос',
                    message: errorData.error || 'Проверьте введенные данные',
                    instructions: [
                        'Проверьте все обязательные поля',
                        'Убедитесь, что данные введены корректно',
                        'Проверьте формат файлов, если загружаете файлы'
                    ]
                };
                break;
            case 401:
                errorInfo = {
                    title: 'Требуется авторизация',
                    message: 'Необходимо войти в систему',
                    instructions: [
                        'Нажмите на кнопку "Войти"',
                        'Введите логин и пароль',
                        'Если забыли пароль, обратитесь к администратору'
                    ]
                };
                break;
            case 403:
                errorInfo = {
                    title: 'Доступ запрещен',
                    message: 'У вас нет прав для выполнения этого действия',
                    instructions: [
                        'Убедитесь, что вы вошли в систему',
                        'Проверьте права доступа',
                        'Обратитесь к администратору для получения доступа'
                    ]
                };
                break;
            case 404:
                errorInfo = {
                    title: 'Не найдено',
                    message: errorData.error || 'Запрашиваемый ресурс не найден',
                    instructions: [
                        'Проверьте правильность URL',
                        'Возможно, страница была удалена',
                        'Попробуйте вернуться на главную страницу'
                    ]
                };
                break;
            case 413:
                errorInfo = {
                    title: 'Файл слишком большой',
                    message: 'Размер загружаемого файла превышает лимит',
                    instructions: [
                        'Максимальный размер файла: 10 МБ',
                        'Уменьшите размер файла',
                        'Используйте сжатие для изображений'
                    ]
                };
                break;
            case 500:
            case 502:
            case 503:
            case 504:
                errorInfo = {
                    title: 'Ошибка сервера',
                    message: errorData.error || `Ошибка ${statusCode}: ${statusText}`,
                    instructions: [
                        'Попробуйте повторить действие через несколько минут',
                        'Обновите страницу (Ctrl+F5)',
                        'Если ошибка повторяется, сообщите администратору',
                        `Код ошибки: ${statusCode}`
                    ]
                };
                break;
            default:
                errorInfo = {
                    title: 'Ошибка запроса',
                    message: errorData.error || `Ошибка ${statusCode}: ${statusText}`,
                    instructions: [
                        'Попробуйте обновить страницу',
                        'Проверьте подключение к интернету',
                        'Если проблема сохраняется, сообщите администратору',
                        `Код ошибки: ${statusCode}`
                    ]
                };
        }
        
        errorInfo.details = {
            status: statusCode,
            statusText: statusText,
            ...errorData
        };
        
        this.showError(errorInfo, context);
        
        return errorInfo;
    }
    
    copyErrorDetails(errorId, triggerBtn) {
        const errorDiv = document.getElementById(errorId);
        if (!errorDiv) return;

        const title = errorDiv.querySelector('.error-title')?.textContent || '';
        const message = errorDiv.querySelector('.error-message')?.textContent || '';
        const details = errorDiv.querySelector('.error-details pre')?.textContent || '';

        const errorText = `Ошибка: ${title}\nСообщение: ${message}\n\nДетали:\n${details}\n\nВремя: ${new Date().toLocaleString('ru-RU')}\nURL: ${window.location.href}`;

        const showSuccess = () => {
            const btn = triggerBtn || (typeof event !== 'undefined' && event.target);
            if (btn) {
                const originalText = btn.textContent;
                btn.textContent = '✓ Скопировано!';
                btn.style.background = '#10b981';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '';
                }, 2000);
            }
        };

        const showFail = () => {
            alert('Не удалось скопировать. Выделите текст вручную.');
        };

        if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
            navigator.clipboard.writeText(errorText).then(showSuccess).catch(showFail);
            return;
        }

        try {
            const textarea = document.createElement('textarea');
            textarea.value = errorText;
            textarea.style.position = 'fixed';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            textarea.select();
            const ok = document.execCommand('copy');
            document.body.removeChild(textarea);
            if (ok) showSuccess(); else showFail();
        } catch (e) {
            showFail();
        }
    }
    
    reloadPage() {
        window.location.reload();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    addStyles() {
        if (document.getElementById('error-handler-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'error-handler-styles';
        style.textContent = `
            .error-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                max-width: 500px;
                background: #fff;
                border-left: 4px solid #ef4444;
                border-radius: 8px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            .error-notification-content {
                padding: 20px;
            }
            
            .error-header {
                display: flex;
                align-items: flex-start;
                gap: 12px;
                margin-bottom: 16px;
            }
            
            .error-icon {
                font-size: 24px;
                flex-shrink: 0;
            }
            
            .error-title-section {
                flex: 1;
            }
            
            .error-title {
                margin: 0 0 4px 0;
                font-size: 18px;
                font-weight: 600;
                color: #1f2937;
            }
            
            .error-message {
                margin: 0;
                font-size: 14px;
                color: #6b7280;
            }
            
            .error-close {
                background: none;
                border: none;
                font-size: 20px;
                color: #9ca3af;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .error-close:hover {
                color: #ef4444;
            }
            
            .error-context {
                padding: 8px 12px;
                background: #f3f4f6;
                border-radius: 6px;
                margin-bottom: 12px;
                font-size: 13px;
                color: #4b5563;
            }
            
            .error-instructions {
                margin-bottom: 16px;
            }
            
            .error-instructions strong {
                display: block;
                margin-bottom: 8px;
                color: #1f2937;
                font-size: 14px;
            }
            
            .error-instructions ol {
                margin: 0;
                padding-left: 20px;
                color: #374151;
                font-size: 13px;
                line-height: 1.6;
            }
            
            .error-instructions li {
                margin-bottom: 4px;
            }
            
            .error-actions {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                margin-bottom: 12px;
            }
            
            .error-action-btn {
                padding: 8px 16px;
                background: #3b82f6;
                color: #fff;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                transition: background 0.2s;
            }
            
            .error-action-btn:hover {
                background: #2563eb;
            }
            
            .error-action-btn.secondary {
                background: #6b7280;
            }
            
            .error-action-btn.secondary:hover {
                background: #4b5563;
            }
            
            .error-details {
                display: none;
                margin-top: 12px;
                padding: 12px;
                background: #f9fafb;
                border-radius: 6px;
                border: 1px solid #e5e7eb;
            }
            
            .error-notification.expanded .error-details {
                display: block;
            }
            
            .error-details pre {
                margin: 0;
                font-size: 11px;
                color: #374151;
                white-space: pre-wrap;
                word-break: break-all;
                max-height: 200px;
                overflow-y: auto;
            }
            
            #error-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            @media (max-width: 768px) {
                .error-notification {
                    max-width: calc(100% - 40px);
                    right: 20px;
                    left: 20px;
                }
                
                .error-actions {
                    flex-direction: column;
                }
                
                .error-action-btn {
                    width: 100%;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
}

// Инициализация глобального обработчика ошибок
window.errorHandler = new ErrorHandler();

// Обертка для fetch с автоматической обработкой ошибок
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    try {
        const response = await originalFetch(...args);
        
        // Если ответ не успешен, пытаемся получить JSON с инструкциями
        if (!response.ok) {
            try {
                const errorData = await response.clone().json();
                // Если в ответе есть инструкции, используем их
                if (errorData.instructions) {
                    const errorInfo = {
                        title: errorData.error || `Ошибка ${response.status}`,
                        message: errorData.error || response.statusText,
                        instructions: errorData.instructions,
                        details: {
                            status: response.status,
                            statusText: response.statusText,
                            context: errorData.context
                        }
                    };
                    window.errorHandler.showError(errorInfo, errorData.context || `Запрос к ${args[0]}`);
                } else {
                    // Иначе используем стандартную обработку
                    await window.errorHandler.handleApiError(response, `Запрос к ${args[0]}`);
                }
            } catch (e) {
                // Если не удалось распарсить JSON, используем стандартную обработку
                await window.errorHandler.handleApiError(response, `Запрос к ${args[0]}`);
            }
            return response;
        }
        
        // Проверяем, есть ли в успешном ответе предупреждения
        try {
            const data = await response.clone().json();
            if (data.success === false && data.error) {
                const errorInfo = {
                    title: 'Ошибка операции',
                    message: data.error || 'Операция не выполнена',
                    instructions: data.instructions || [
                        'Попробуйте выполнить действие снова',
                        'Если проблема сохраняется, сообщите администратору'
                    ],
                    details: {
                        context: data.context
                    }
                };
                window.errorHandler.showError(errorInfo, data.context || `Запрос к ${args[0]}`);
            }
        } catch (e) {
            // Не JSON ответ, игнорируем
        }
        
        return response;
    } catch (error) {
        window.errorHandler.handleError(error, `Запрос к ${args[0]}`);
        throw error;
    }
};

// Экспорт для использования в других модулях
window.showError = (error, context) => {
    window.errorHandler.handleError(error, context);
};

window.handleApiError = async (response, context) => {
    return await window.errorHandler.handleApiError(response, context);
};

