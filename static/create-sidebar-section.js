// Модальное окно для создания нового раздела бокового меню

function openCreateSidebarSectionModal(options) {
    // Создаем модальное окно если его нет
    let modal = document.getElementById('create-sidebar-section-modal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'create-sidebar-section-modal';
        modal.className = 'modal-backdrop';
        // Поверх мастера бокового меню
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.right = '0';
        modal.style.bottom = '0';
        modal.style.zIndex = '100000';
        modal.innerHTML = `
            <div class="modal" style="max-width: 600px;">
                <div class="modal-header">
                    <div>Создать новый раздел бокового меню</div>
                    <button class="close-btn" onclick="closeCreateSidebarSectionModal()">×</button>
                </div>
                <div class="modal-body">
                    <form id="create-sidebar-section-form">
                        <div class="field">
                            <label for="section-title">Название раздела *</label>
                            <input type="text" id="section-title" name="title" required 
                                   placeholder="Например: Новости школы" />
                        </div>
                        <div class="field">
                            <label for="section-content">Описание (необязательно)</label>
                            <textarea id="section-content" name="content" rows="4" 
                                      placeholder="Краткое описание раздела"></textarea>
                        </div>
                        <div id="create-section-status" style="margin-top: 12px;"></div>
                        <div style="display: flex; gap: 12px; margin-top: 20px;">
                            <button type="submit" class="btn" style="flex: 1; background: linear-gradient(135deg, #10b981, #059669);">
                                Создать раздел
                            </button>
                            <button type="button" class="btn btn-secondary" onclick="closeCreateSidebarSectionModal()" style="flex: 1;">
                                Отмена
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Обработка отправки формы
        const form = document.getElementById('create-sidebar-section-form');
        form.addEventListener('submit', handleCreateSidebarSection);
    }
    
    // Сохраняем переданные опции (например, parent)
    const opts = options || {};
    modal.dataset.parent = opts.parent || '';
    
    // Сбрасываем форму и состояния при открытии
    const form = document.getElementById('create-sidebar-section-form');
    if (form) {
        form.reset();
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Создать раздел';
        }
    }
    
    const statusDiv = document.getElementById('create-section-status');
    if (statusDiv) {
        statusDiv.innerHTML = '';
    }
    
    // Обновляем z-index на случай повторного открытия
    modal.style.zIndex = '100000';
    const wizard = document.getElementById('sidebarWizardModal');
    if (wizard) wizard.style.zIndex = '99990';
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
}

function closeCreateSidebarSectionModal() {
    const modal = document.getElementById('create-sidebar-section-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.classList.remove('modal-open');
        
        // Очищаем форму
        const form = document.getElementById('create-sidebar-section-form');
        if (form) {
            form.reset();
            // Разблокируем кнопку и восстанавливаем текст
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Создать раздел';
            }
        }
        
        const statusDiv = document.getElementById('create-section-status');
        if (statusDiv) {
            statusDiv.innerHTML = '';
        }
        
    }
}

async function handleCreateSidebarSection(e) {
    e.preventDefault();
    
    const form = e.target;
    const statusDiv = document.getElementById('create-section-status');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    const title = form.querySelector('#section-title').value.trim();
    const content = form.querySelector('#section-content').value.trim();
    
    if (!title) {
        statusDiv.innerHTML = '<div style="color: #ef4444; padding: 8px; background: #fee2e2; border-radius: 6px;">Название раздела обязательно</div>';
        return;
    }
    
    // Блокируем кнопку
    submitBtn.disabled = true;
    submitBtn.textContent = 'Создание...';
    statusDiv.innerHTML = '<div style="color: #3b82f6; padding: 8px;">Создание раздела...</div>';
    
    try {
        const response = await fetch('/sidebar/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                endpoint: null,
                content: content,
                parent: (document.getElementById('create-sidebar-section-modal')?.dataset?.parent) || null
            })
        });
        
        const result = await response.json();
        
        console.log('Response from create:', result);
        
        if (result.success && result.section) {
            const isWizardChildCreate = !!(document.getElementById('create-sidebar-section-modal')?.dataset?.parent);
            
            if (isWizardChildCreate && window.sidebarWizardManager) {
                // Добавляем шаг в текущий sidebar мастер без перезагрузки страницы
                const endpoint = result.section.endpoint;
                const parentEndpoint = document.getElementById('create-sidebar-section-modal')?.dataset?.parent || '';
                
                // Добавляем новый шаг в список шагов
                const newStep = {
                    id: endpoint,
                    title: title,
                    icon: '🧩',
                    endpoint: endpoint,
                    module: 'sidebar',
                    parent: parentEndpoint,
                    fields: [
                        { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                        { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: false },
                        { name: 'images', label: 'Изображения', type: 'images', required: false },
                        { name: 'documents', label: 'Документы', type: 'documents', required: false }
                    ]
                };
                
                // Проверяем, нет ли уже такого шага
                const existingIndex = window.sidebarWizardManager.wizardSteps.findIndex(s => s.endpoint === endpoint);
                if (existingIndex < 0) {
                    window.sidebarWizardManager.wizardSteps.push(newStep);
                }
                
                // Подготовим минимальные данные для нового шага
                window.sidebarWizardManager.wizardData[endpoint] = {
                    title: title,
                    text: JSON.stringify({
                        text: content,
                        form_data: {
                            parent: parentEndpoint
                        }
                    }),
                    content: content,
                    content_blocks: []
                };
                
                // Синхронизируем глобальные структуры
                window.wizardSteps = window.sidebarWizardManager.wizardSteps;
                window.wizardData = window.sidebarWizardManager.wizardData;
                
                // Находим индекс нового шага и переключаемся на него
                const idx = window.sidebarWizardManager.wizardSteps.findIndex(s => s.endpoint === endpoint);
                if (idx >= 0) {
                    window.sidebarWizardManager.currentStep = idx;
                }
                
                window.sidebarWizardManager.renderSteps();
                window.sidebarWizardManager.renderCurrentStep();
                
                // Разблокируем кнопку и восстанавливаем текст перед закрытием
                submitBtn.disabled = false;
                submitBtn.textContent = 'Создать раздел';
                
                // Очищаем форму и закрываем модальное окно
                form.reset();
                closeCreateSidebarSectionModal();
                
                // Показываем сообщение об успехе на короткое время
                setTimeout(() => {
                    if (statusDiv) {
                        statusDiv.innerHTML = '';
                    }
                }, 2000);
                
                return;
            }
            
            statusDiv.innerHTML = '<div style="color: #10b981; padding: 8px; background: #d1fae5; border-radius: 6px;">✓ Раздел успешно создан! Переход на страницу...</div>';
            
            // Переходим на страницу раздела через 1 секунду
            setTimeout(() => {
                const url = result.section.url || `/sidebar/${result.section.endpoint}`;
                console.log('Redirecting to:', url);
                window.location.href = url;
            }, 1000);
        } else {
            const errorMsg = result.error || 'Неизвестная ошибка';
            console.error('Error creating section:', errorMsg);
            statusDiv.innerHTML = `<div style="color: #ef4444; padding: 8px; background: #fee2e2; border-radius: 6px;">✗ Ошибка: ${errorMsg}</div>`;
            submitBtn.disabled = false;
            submitBtn.textContent = 'Создать раздел';
        }
    } catch (error) {
        statusDiv.innerHTML = `<div style="color: #ef4444; padding: 8px; background: #fee2e2; border-radius: 6px;">✗ Ошибка: ${error.message}</div>`;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Создать раздел';
    }
}

// Закрытие по клику на фон
document.addEventListener('click', function(e) {
    if (e.target.id === 'create-sidebar-section-modal') {
        closeCreateSidebarSectionModal();
    }
});

// Закрытие по Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const modal = document.getElementById('create-sidebar-section-modal');
        if (modal && modal.style.display === 'flex') {
            closeCreateSidebarSectionModal();
        }
    }
});

// Экспорт функций
window.openCreateSidebarSectionModal = openCreateSidebarSectionModal;
window.closeCreateSidebarSectionModal = closeCreateSidebarSectionModal;

// Открытие модала как создания подраздела, с указанием родителя
window.openCreateSidebarSubsectionModal = function(parentEndpoint){
    openCreateSidebarSectionModal({ parent: parentEndpoint || '' });
};

