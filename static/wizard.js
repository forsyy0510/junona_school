// Мастер заполнения - основной модуль
class WizardManager {
    constructor() {
        this.currentStep = 0;
        this.wizardData = {};
        this.wizardSteps = [];
        this.mode = 'normal'; // normal | tags
        this.modalElement = null;
        this.init();
    }

    init() {
        this.loadWizardSteps();
        this.loadWizardData();
        this.setupEventListeners();
    }

    loadWizardSteps() {
        // Если активен мастер бокового меню — не перезаписываем шаги
        if (typeof window !== 'undefined' && window.IS_SIDEBAR_WIZARD === true) {
            return;
        }
        // Загружаем шаги мастера для основных разделов сведений (/sveden/*).
        // Здесь работаем только с InfoSection endpoint'ами (main, structure, documents, ...),
        // раздел ПИТАНИЕ (food/catering) умышленно не включаем.
        this.wizardSteps = [
            {
                id: 'main',
                title: 'Основные сведения',
                icon: '🏢',
                endpoint: 'main',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'structure',
                title: 'Структура и органы управления',
                icon: '🏛️',
                endpoint: 'structure',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'documents',
                title: 'Документы',
                icon: '📄',
                endpoint: 'documents',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'education',
                title: 'Образование',
                icon: '🎓',
                endpoint: 'education',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'standards',
                title: 'Образовательные стандарты и требования',
                icon: '📚',
                endpoint: 'standards',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'management',
                title: 'Руководство',
                icon: '👩‍💼',
                endpoint: 'management',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'teachers',
                title: 'Педагогический состав',
                icon: '👨‍🏫',
                endpoint: 'teachers',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'facilities',
                title: 'Материально-техническое обеспечение и доступная среда',
                icon: '🏫',
                endpoint: 'facilities',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'scholarships',
                title: 'Стипендии и меры поддержки обучающихся',
                icon: '💰',
                endpoint: 'scholarships',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'paid-services',
                title: 'Платные образовательные услуги',
                icon: '💳',
                endpoint: 'paid-services',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'finance',
                title: 'Финансово-хозяйственная деятельность',
                icon: '📊',
                endpoint: 'finance',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'vacancies',
                title: 'Вакантные места',
                icon: '📌',
                endpoint: 'vacancies',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            },
            {
                id: 'international',
                title: 'Международное сотрудничество',
                icon: '🌍',
                endpoint: 'international',
                module: 'info',
                type: 'sveden-table-blocks',
                fields: []
            }
        ];
    }

    async loadWizardData() {
        const loadPromises = this.wizardSteps.map(step => {
            const module = step.module || 'info';
            const url = module === 'sidebar' ? `/sidebar/section/${step.endpoint}` : `/info/section/${step.endpoint}`;
            const emptyData = () => {
                this.wizardData[step.id] = {
                    title: '',
                    text: '',
                    content_blocks: []
                };
            };
            return (async () => {
                try {
                    const response = await fetch(url);
                    const data = await response.json();
                    if (data.success && data.section) {
                        this.wizardData[step.id] = {
                            title: data.section.title || '',
                            text: data.section.text || '',
                            content_blocks: data.section.content_blocks || []
                        };
                        if (data.section.form_data) {
                            Object.assign(this.wizardData[step.id], data.section.form_data);
                        }
                    } else {
                        emptyData();
                    }
                } catch (error) {
                    console.error('Error loading step data for', step.endpoint, error);
                    emptyData();
                }
            })();
        });

        await Promise.allSettled(loadPromises);
    }

    setupEventListeners() {
        // Обработчик изменения типа персоны
        document.addEventListener('change', (e) => {
            if (e.target && e.target.classList.contains('sveden-person-type-select')) {
                const select = e.target;
                const blockIndex = parseInt(select.getAttribute('data-block-index'), 10);
                if (Number.isNaN(blockIndex)) return;
                const blockEl = select.closest('.wizard-block-item');
                if (!blockEl) return;
                const branchNameField = blockEl.querySelector('.sveden-branch-name-field');
                if (branchNameField) {
                    if (select.value === 'rucovodstvoFil') {
                        branchNameField.style.display = 'block';
                    } else {
                        branchNameField.style.display = 'none';
                    }
                }
            }
        });
        
        // Инициализация видимости поля названия филиала при загрузке
        setTimeout(() => {
            document.querySelectorAll('.sveden-person-type-select').forEach(select => {
                const blockEl = select.closest('.wizard-block-item');
                if (!blockEl) return;
                const branchNameField = blockEl.querySelector('.sveden-branch-name-field');
                if (branchNameField) {
                    if (select.value === 'rucovodstvoFil') {
                        branchNameField.style.display = 'block';
                    } else {
                        branchNameField.style.display = 'none';
                    }
                }
            });
        }, 100);
        // Пока что дополнительных глобальных обработчиков не требуется.
        // Мастер открывается по явному вызову wizardManager.open().
    }

    createWizardModal() {
        // Создание модального окна мастера (по умолчанию скрытого)
        const modal = document.createElement('div');
        modal.className = 'wizard-modal';
        modal.id = 'wizardModal';
        modal.style.display = 'none';
        modal.innerHTML = `
            <div class="wizard-backdrop" onclick="wizardManager.closeWizard()"></div>
            <div class="wizard-container">
                <div class="wizard-header">
                    <div class="wizard-title">
                        <h2>🎯 Мастер заполнения</h2>
                        <p>Заполните все необходимые разделы сайта</p>
                    </div>
                    <div class="wizard-mode-toggle" id="wizardModeToggle">
                        <button type="button"
                                id="wizardModeNormal"
                                class="wizard-mode-btn wizard-mode-btn-active"
                                onclick="wizardManager.setMode('normal')">
                            Данные
                        </button>
                        <button type="button"
                                id="wizardModeTags"
                                class="wizard-mode-btn"
                                onclick="wizardManager.setMode('tags')">
                            Режим тегов
                        </button>
                    </div>
                    <button class="wizard-close" onclick="wizardManager.closeWizard()">×</button>
                </div>
                <div class="wizard-content">
                    <div class="wizard-sidebar">
                        <div class="wizard-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" id="progressFill"></div>
                            </div>
                            <div class="progress-text" id="progressText">Шаг 1 из ${this.wizardSteps.length}</div>
                        </div>
                        <div class="wizard-steps" id="wizardSteps"></div>
                    </div>
                    <div class="wizard-main">
                        <div class="wizard-step-content" id="wizardStepContent"></div>
                        <div class="wizard-actions">
                            <button class="btn btn-secondary" onclick="wizardManager.previousStep()" id="prevBtn" disabled>← Назад</button>
                            <div class="wizard-actions-center">
                                <button class="btn btn-success" onclick="wizardManager.saveCurrentStep()" id="wizardSaveCurrentBtn" type="button">💾 Сохранить изменения</button>
                                <div class="wizard-save-status" id="wizard-save-status"></div>
                                <button class="btn btn-warning" onclick="wizardManager.cleanMissingFiles()" id="cleanBtn">🧹 Очистить несуществующие файлы</button>
                            </div>
                            <button class="btn" onclick="wizardManager.nextStep()" id="nextBtn">Далее →</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.modalElement = modal;
    }

    /**
     * Открыть мастер заполнения (основные разделы сведений).
     */
    open() {
        // Создаем модал, если он ещё не создан
        if (!this.modalElement || !document.body.contains(this.modalElement)) {
            this.createWizardModal();
        }

        // Убеждаемся, что шаги загружены
        if (!this.wizardSteps || this.wizardSteps.length === 0) {
            this.loadWizardSteps();
        }

        // Определяем, какой шаг нужно открыть
        let targetStepIndex = 0;
        
        // Проверяем, установлен ли целевой endpoint
        if (typeof window !== 'undefined' && window.WIZARD_TARGET_ENDPOINT) {
            const targetEndpoint = window.WIZARD_TARGET_ENDPOINT;
            const stepIndex = this.wizardSteps.findIndex(step => step.endpoint === targetEndpoint);
            if (stepIndex >= 0) {
                targetStepIndex = stepIndex;
            }
            // Очищаем после использования
            window.WIZARD_TARGET_ENDPOINT = null;
        } else {
            // Пытаемся определить endpoint из URL
            const pathname = window.location && window.location.pathname || '';
            if (pathname) {
                // Проверяем паттерны /sveden/{endpoint} или /info/{endpoint}
                const svedenMatch = pathname.match(/\/sveden\/([^\/]+)/);
                const infoMatch = pathname.match(/\/info\/([^\/]+)/);
                const endpoint = svedenMatch ? svedenMatch[1] : (infoMatch ? infoMatch[1] : null);
                
                if (endpoint) {
                    const stepIndex = this.wizardSteps.findIndex(step => step.endpoint === endpoint);
                    if (stepIndex >= 0) {
                        targetStepIndex = stepIndex;
                    }
                }
            }
        }

        // Обновляем шаги и содержимое
        this.currentStep = targetStepIndex;
        this.renderWizardSteps();
        if (this.wizardSteps.length > 0 && this.wizardSteps[targetStepIndex]) {
            this.loadStepContent(this.wizardSteps[targetStepIndex]);
            this.updateWizardUI();
        }

        if (this.modalElement) {
            this.modalElement.style.display = 'flex';
        }
    }

    renderWizardSteps() {
        const stepsContainer = document.getElementById('wizardSteps');
        if (!stepsContainer) return;

        stepsContainer.innerHTML = '';

        this.wizardSteps.forEach((step, index) => {
            const stepElement = document.createElement('div');
            stepElement.className = 'wizard-step';
            stepElement.setAttribute('data-step', index);
            stepElement.onclick = () => this.goToStep(index);
            
            stepElement.innerHTML = `
                <div class="wizard-step-icon">${index + 1}</div>
                <div class="wizard-step-text">${step.title}</div>
            `;
            
            stepsContainer.appendChild(stepElement);
        });
    }

    goToStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.wizardSteps.length) return;
        
        this.currentStep = stepIndex;
        this.updateWizardUI();
        this.loadStepContent(this.wizardSteps[stepIndex]);
    }

    updateWizardUI() {
        // Обновление UI мастера
        const steps = document.querySelectorAll('.wizard-step');
        steps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            if (index === this.currentStep) {
                step.classList.add('active');
            } else if (index < this.currentStep) {
                step.classList.add('completed');
            }
        });

        // Обновление кнопок навигации
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        
        if (prevBtn) prevBtn.disabled = this.currentStep === 0;
        if (nextBtn) {
            nextBtn.textContent = this.currentStep === this.wizardSteps.length - 1 ? 'Сохранить' : 'Далее →';
        }

        // Обновление прогресса
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressFill) {
            const progress = ((this.currentStep + 1) / this.wizardSteps.length) * 100;
            progressFill.style.width = `${progress}%`;
        }
        
        if (progressText) {
            progressText.textContent = `Шаг ${this.currentStep + 1} из ${this.wizardSteps.length}`;
        }
    }

    loadStepContent(step) {
        const contentContainer = document.getElementById('wizardStepContent');
        if (!contentContainer) return;

        // Режим тегов для шагов основных сведений (табличные блоки)
        if (this.mode === 'tags' && step.type === 'sveden-table-blocks') {
            contentContainer.innerHTML = this.generateSvedenTagsHTML(step);
            return;
        }

        contentContainer.innerHTML = this.generateStepHTML(step);
        this.initializeStepFields(step);

        if (step.type === 'sveden-table-blocks') {
            setTimeout(() => {
                const rows = contentContainer.querySelectorAll('.wizard-block-row');
                rows.forEach(rowEl => {
                    const valueInput = rowEl.querySelector('.wizard-block-row-value');
                    if (valueInput) {
                        valueInput.style.height = '60px';
                        const filesList = this.parseSvedenFilesValue(valueInput.value);
                        if (filesList.length > 0) {
                            this.updateSvedenCellFilesDisplay(rowEl);
                        }
                        valueInput.addEventListener('input', () => {
                            const filesList = this.parseSvedenFilesValue(valueInput.value);
                            this.updateSvedenCellFilesDisplay(rowEl);
                        });
                    }
                    const subRows = rowEl.querySelectorAll('.sveden-subrow');
                    subRows.forEach(subRowEl => {
                        const subValueInput = subRowEl.querySelector('.wizard-block-subrow-value');
                        if (subValueInput) {
                            subValueInput.style.height = '60px';
                            const subFilesList = this.parseSvedenFilesValue(subValueInput.value);
                            if (subFilesList.length > 0) {
                                this.updateSvedenSubRowFilesDisplay(subRowEl);
                            }
                            subValueInput.addEventListener('input', () => {
                                const subFilesList = this.parseSvedenFilesValue(subValueInput.value);
                                this.updateSvedenSubRowFilesDisplay(subRowEl);
                            });
                        }
                    });
                });
            }, 100);
        }

        // Дополнительная инициализация для файловых полей
        setTimeout(() => {
            if (Array.isArray(step.fields)) {
                step.fields.forEach(field => {
                    if (field.type === 'file_or_text') {
                        this.toggleInputType(field.name, 'file');
                    }
                });
            }
        }, 200);
    }

    generateStepHTML(step) {
        // Специальный режим для основных разделов сведений (/sveden/*):
        // редактирование блоков-таблиц (как на новом макете).
        if (step.type === 'sveden-table-blocks') {
            return this.generateSvedenBlocksHTML(step);
        }

        let html = `<h2>${step.title}</h2>`;

        if (Array.isArray(step.fields)) {
            step.fields.forEach(field => {
                html += this.generateFieldHTML(field, step.id);
            });
        }

        return html;
    }

    /**
     * Простой экранирующий хелпер для вставки значений в HTML.
     */
    escapeHtml(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * HTML для шага с блоками-таблицами и персонами основных сведений.
     */
    generateSvedenBlocksHTML(step) {
        const data = this.wizardData[step.id] || {};
        const rawBlocks = Array.isArray(data.content_blocks)
            ? data.content_blocks.filter(b => b && (b.type === 'table' || b.type === 'person'))
            : [];

        const blocks = rawBlocks.length > 0 ? rawBlocks : [this.createEmptySvedenBlock(0)];

        let html = `
            <div class="wizard-step-header">
                <h3>${step.title}</h3>
                <p>Добавляйте блоки: таблица (название + текст/файл) или персона (ФИО, должность, фото и др.).</p>
            </div>
            <div class="wizard-content-blocks">
                <div class="wizard-blocks-header">
                    <h4>Блоки раздела</h4>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="wizardManager.addSvedenBlock('${step.id}')">Добавить блок (таблица)</button>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="wizardManager.addSvedenPersonBlock('${step.id}')">Добавить блок (персона)</button>
                </div>
                <div class="wizard-blocks-list" data-step-id="${step.id}">
        `;

        blocks.forEach((block, index) => {
            if (block.type === 'person') {
                html += this.generateSvedenPersonBlockHTML(step, block, index);
            } else {
                html += this.generateSvedenBlockItemHTML(step, block, index);
            }
        });

        html += `
                </div>
            </div>
        `;

        if (step.id === 'education') {
            html += this.generateEducationProgramsHTML(step);
        }

        return html;
    }

    normalizeProgramsList(value) {
        if (Array.isArray(value)) {
            return value.map(p => {
                if (p && typeof p === 'object') {
                    const name = (p.name !== undefined ? String(p.name) : (p.url ? '' : '')).trim();
                    const url = (p.url !== undefined ? String(p.url) : '').trim();
                    return { name, url };
                }
                return { name: String(p || ''), url: '' };
            }).filter(p => p.name || p.url);
        }
        if (typeof value === 'string' && value.trim()) {
            return value.split('\n').map(line => {
                const lineTrim = line.trim();
                if (!lineTrim) return null;
                const idx = lineTrim.indexOf('|');
                if (idx >= 0) {
                    return { name: lineTrim.slice(0, idx).trim(), url: lineTrim.slice(idx + 1).trim() };
                }
                return { name: lineTrim, url: '' };
            }).filter(Boolean);
        }
        return [];
    }

    generateEducationProgramsHTML(step) {
        const data = this.wizardData[step.id] || {};
        const implemented = this.normalizeProgramsList(data.implemented_programs);
        const adapted = this.normalizeProgramsList(data.adapted_programs);
        const implList = implemented.length > 0 ? implemented : [{ name: '', url: '' }];
        const adptList = adapted.length > 0 ? adapted : [{ name: '', url: '' }];

        const renderProgramRow = (name, url, listKind, index) => {
            const nameEsc = this.escapeHtml(name);
            const urlEsc = this.escapeHtml(url);
            return `
                <div class="education-program-row" data-list="${listKind}" data-index="${index}">
                    <input type="text" class="wizard-input program-name" placeholder="Название программы" value="${nameEsc}">
                    <input type="text" class="wizard-input program-url" placeholder="Ссылка или путь к файлу" value="${urlEsc}">
                    <button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeEducationProgram(this)">×</button>
                </div>`;
        };

        let implHtml = implList.map((p, i) => renderProgramRow(p.name, p.url, 'implemented', i)).join('');
        let adptHtml = adptList.map((p, i) => renderProgramRow(p.name, p.url, 'adapted', i)).join('');

        return `
            <div class="education-programs-editor" data-step-id="${step.id}">
                <h4 class="wizard-blocks-header" style="margin-top: 20px;">Образовательные программы</h4>
                <p class="wizard-tags-description" style="margin-bottom: 10px;">Список реализуемых программ (название и ссылка на документ).</p>
                <div class="education-programs-list" data-list="implemented">
                    ${implHtml}
                </div>
                <button type="button" class="btn btn-sm btn-secondary" onclick="wizardManager.addEducationProgram('${step.id}', 'implemented')">+ Добавить программу</button>

                <h4 class="wizard-blocks-header" style="margin-top: 24px;">Адаптированные образовательные программы</h4>
                <p class="wizard-tags-description" style="margin-bottom: 10px;">Список адаптированных программ (название и ссылка на документ).</p>
                <div class="education-programs-list" data-list="adapted">
                    ${adptHtml}
                </div>
                <button type="button" class="btn btn-sm btn-secondary" onclick="wizardManager.addEducationProgram('${step.id}', 'adapted')">+ Добавить программу</button>
            </div>`;
    }

    addEducationProgram(stepId, listKind) {
        const container = document.querySelector(`.education-programs-editor[data-step-id="${stepId}"] .education-programs-list[data-list="${listKind}"]`);
        if (!container) return;
        const index = container.querySelectorAll('.education-program-row').length;
        const row = document.createElement('div');
        row.className = 'education-program-row';
        row.setAttribute('data-list', listKind);
        row.setAttribute('data-index', String(index));
        row.innerHTML = `
            <input type="text" class="wizard-input program-name" placeholder="Название программы" value="">
            <input type="text" class="wizard-input program-url" placeholder="Ссылка или путь к файлу" value="">
            <button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeEducationProgram(this)">×</button>`;
        container.appendChild(row);
    }

    removeEducationProgram(btn) {
        const row = btn && btn.closest && btn.closest('.education-program-row');
        if (row) row.remove();
    }

    createEmptySvedenBlock(index) {
        return {
            type: 'table',
            title: `Блок ${index + 1}`,
            headers: ['Название', 'Текст/файл'],
            rows: [['', '']],
            itemprop: '',
            row_itemprops: []
        };
    }

    createEmptySvedenPersonBlock(index) {
        return {
            type: 'person',
            title: `Блок ${index + 1}`,
            person_type: 'rucovodstvo', // По умолчанию - руководитель обр. орг.
            branch_name: '', // Название филиала (только для руководителя филиала)
            persons: [{ name: '', position: '', photo: '', education: '', experience: '', description: '' }],
            person_itemprop_mapping: {}
        };
    }

    defaultPersonItemprop(field) {
        const map = {
            name: 'name', position: 'jobTitle', photo: 'image', email: 'email', phone: 'telephone',
            education: 'education', experience: 'experience', description: 'description',
            professional_retraining: 'hasCredential', awards: 'award', courses: 'knowsAbout'
        };
        return map[field] || field;
    }

    generateSvedenPersonItemHTML(stepId, blockIndex, personIndex, p, mapping) {
        const getVal = (key) => (p && p[key]) ? String(p[key]) : '';
        const nameVal = getVal('name');
        const positionVal = getVal('position');
        const photoVal = getVal('photo');
        const emailVal = getVal('email');
        const phoneVal = getVal('phone');
        const educationVal = getVal('education');
        const experienceVal = getVal('experience');
        const descriptionVal = getVal('description');
        const retrainingVal = getVal('professional_retraining');
        const awardsVal = getVal('awards');
        const coursesVal = getVal('courses');
        const getIp = (f) => (mapping[f] !== undefined ? String(mapping[f]) : this.defaultPersonItemprop(f));
        const photoFileInfo = this.parseSvedenFileValue(photoVal);
        const photoFileBlockHtml = photoFileInfo.isFile
            ? `<div class="sveden-person-photo-file"><span class="sveden-file-name">${this.escapeHtml(photoFileInfo.displayName)}</span><button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeSvedenPersonPhoto(this)">Удалить фото</button></div>`
            : '';
        const photoUploadBtnStyle = photoFileInfo.isFile ? ' display:none;' : '';
        return `
                <div class="sveden-person-item person-item" data-person-index="${personIndex}">
                    <div class="sveden-person-fields">
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>ФИО</label>
                            <div class="sveden-person-field-row">
                                <input type="text" class="wizard-input person-name" value="${this.escapeHtml(nameVal)}" placeholder="Иванов Иван Иванович">
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="name" value="${this.escapeHtml(getIp('name'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Должность</label>
                            <div class="sveden-person-field-row">
                                <input type="text" class="wizard-input person-position" value="${this.escapeHtml(positionVal)}" placeholder="Директор">
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="position" value="${this.escapeHtml(getIp('position'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Фото</label>
                            <div class="sveden-person-field-row">
                                <div class="sveden-person-photo-wrap">
                                    ${photoFileBlockHtml}
                                    <input type="hidden" class="wizard-input person-photo" value="${this.escapeHtml(photoVal)}">
                                    <button type="button" class="btn btn-sm btn-secondary sveden-person-photo-upload-btn" style="${photoUploadBtnStyle}" onclick="wizardManager.uploadSvedenPersonPhoto('${stepId}', ${blockIndex}, ${personIndex})">Загрузить фото</button>
                                </div>
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="photo" value="${this.escapeHtml(getIp('photo'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>E-mail</label>
                            <div class="sveden-person-field-row">
                                <input type="text" class="wizard-input person-email" value="${this.escapeHtml(emailVal)}" placeholder="email@example.ru">
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="email" value="${this.escapeHtml(getIp('email'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Телефон</label>
                            <div class="sveden-person-field-row">
                                <input type="text" class="wizard-input person-phone" value="${this.escapeHtml(phoneVal)}" placeholder="8(863)-...">
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="phone" value="${this.escapeHtml(getIp('phone'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Краткое описание</label>
                            <div class="sveden-person-field-row">
                                <textarea class="wizard-input person-description" rows="2" placeholder="Краткая информация">${this.escapeHtml(descriptionVal)}</textarea>
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="description" value="${this.escapeHtml(getIp('description'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Педагогический стаж</label>
                            <div class="sveden-person-field-row">
                                <input type="text" class="wizard-input person-experience" value="${this.escapeHtml(experienceVal)}" placeholder="29 лет">
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="experience" value="${this.escapeHtml(getIp('experience'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Образование</label>
                            <div class="sveden-person-field-row">
                                <textarea class="wizard-input person-education" rows="2" placeholder="Высшее, вуз, специальность">${this.escapeHtml(educationVal)}</textarea>
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="education" value="${this.escapeHtml(getIp('education'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Профессиональная переподготовка</label>
                            <div class="sveden-person-field-row">
                                <textarea class="wizard-input person-professional-retraining" rows="2" placeholder="Курс, квалификация">${this.escapeHtml(retrainingVal)}</textarea>
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="professional_retraining" value="${this.escapeHtml(getIp('professional_retraining'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Награды и звания</label>
                            <div class="sveden-person-field-row">
                                <textarea class="wizard-input person-awards" rows="4" placeholder="Список наград (каждая с новой строки)">${this.escapeHtml(awardsVal)}</textarea>
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="awards" value="${this.escapeHtml(getIp('awards'))}" placeholder="itemprop">
                            </div>
                        </div>
                        <div class="wizard-block-edit-field sveden-person-field">
                            <label>Курсы повышения квалификации</label>
                            <div class="sveden-person-field-row">
                                <textarea class="wizard-input person-courses" rows="4" placeholder="Нумерованный список курсов">${this.escapeHtml(coursesVal)}</textarea>
                                <input type="text" class="wizard-input sveden-itemprop-input" data-person-field="courses" value="${this.escapeHtml(getIp('courses'))}" placeholder="itemprop">
                            </div>
                        </div>
                    </div>
                    <button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeSvedenPerson(this)">Удалить</button>
                </div>`;
    }

    generateSvedenPersonBlockHTML(step, block, blockIndex) {
        const title = (block && block.title) ? String(block.title).trim() : '';
        const persons = Array.isArray(block && block.persons) && block.persons.length > 0 ? block.persons : [{}];
        const mapping = (block && block.person_itemprop_mapping) && typeof block.person_itemprop_mapping === 'object' ? block.person_itemprop_mapping : {};
        const personType = (block && block.person_type) ? String(block.person_type) : 'rucovodstvo';
        const branchName = (block && block.branch_name) ? String(block.branch_name) : '';

        const listId = `person-list-${step.id}-${blockIndex}`;
        let personsHtml = '';
        persons.forEach((p, idx) => {
            personsHtml += this.generateSvedenPersonItemHTML(step.id, blockIndex, idx, p, mapping);
        });

        const blockItemprop = (block && block.itemprop) ? String(block.itemprop) : '';
        const showBranchName = personType === 'rucovodstvoFil';
        
        let html = `
            <div class="wizard-block-item sveden-block-card sveden-person-block-card" data-step-id="${step.id}" data-block-index="${blockIndex}" data-block-type="person">
                <div class="wizard-block-header">
                    <div class="wizard-block-type wizard-block-title-row">
                        <span class="wizard-block-num">Блок ${blockIndex + 1}</span>
                        <input type="text" class="wizard-input wizard-block-title-input wizard-block-title-inline" value="${this.escapeHtml(title)}" placeholder="Название блока (необязательно)">
                    </div>
                    <div class="wizard-block-actions">
                        <button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeSvedenBlock('${step.id}', ${blockIndex})">Удалить блок</button>
                    </div>
                </div>
                <div class="wizard-block-body">
                    <div class="sveden-person-block-wrap">
                        <div class="sveden-person-type-selector" style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 6px; font-weight: 500;">Тип персоны:</label>
                            <select class="wizard-input sveden-person-type-select" data-block-index="${blockIndex}" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #e5e7eb;">
                                <option value="rucovodstvo" ${personType === 'rucovodstvo' ? 'selected' : ''}>Руководитель образовательной организации</option>
                                <option value="rucovodstvoZam" ${personType === 'rucovodstvoZam' ? 'selected' : ''}>Заместитель руководителя образовательной организации</option>
                                <option value="rucovodstvoFil" ${personType === 'rucovodstvoFil' ? 'selected' : ''}>Руководитель филиала</option>
                            </select>
                        </div>
                        ${showBranchName ? `
                        <div class="sveden-branch-name-field" style="margin-bottom: 12px;">
                            <label style="display: block; margin-bottom: 6px; font-weight: 500;">Название филиала:</label>
                            <input type="text" class="wizard-input sveden-branch-name-input" data-block-index="${blockIndex}" value="${this.escapeHtml(branchName)}" placeholder="Название филиала" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #e5e7eb;">
                        </div>
                        ` : ''}
                        <div class="sveden-person-itemprop-block">
                            <span class="sveden-itemprop-label">itemprop блока</span>
                            <input type="text" class="wizard-input sveden-person-block-itemprop" value="${this.escapeHtml(blockItemprop)}" placeholder="itemprop блока">
                        </div>
                        <div class="sveden-person-list" id="${listId}">${personsHtml}</div>
                        <button type="button" class="btn btn-sm btn-secondary" onclick="wizardManager.addSvedenPerson(this)">+ персона</button>
                    </div>
                </div>
            </div>
        `;
        return html;
    }

    generateSvedenBlockItemHTML(step, block, blockIndex) {
        const title = (block && block.title) ? String(block.title).trim() : '';
        const rows = Array.isArray(block && block.rows) && block.rows.length > 0 ? block.rows : [['', '']];

        let html = `
            <div class="wizard-block-item sveden-block-card" data-step-id="${step.id}" data-block-index="${blockIndex}" data-block-type="table">
                <div class="wizard-block-header">
                    <div class="wizard-block-type wizard-block-title-row">
                        <span class="wizard-block-num">Блок ${blockIndex + 1}</span>
                        <input type="text" class="wizard-input wizard-block-title-input wizard-block-title-inline" value="${this.escapeHtml(title)}" placeholder="Название (необязательно)">
                    </div>
                    <div class="wizard-block-actions">
                        <button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeSvedenBlock('${step.id}', ${blockIndex})">Удалить блок</button>
                    </div>
                </div>
                <div class="wizard-block-body">
                    <div class="sveden-block-table-wrap">
                        <table class="sveden-block-table-inner">
                            <thead>
                                <tr>
                                    <th class="cell-name">Название</th>
                                    <th class="cell-value">Текст/файл</th>
                                    <th class="cell-actions"></th>
                                </tr>
                            </thead>
                            <tbody>
        `;

        rows.forEach((row, rowIndex) => {
            const left = Array.isArray(row) ? (row[0] || '') : '';
            const right = Array.isArray(row) ? (row[1] || '') : '';
            const subRows = Array.isArray(row) && row.length > 2 && Array.isArray(row[2]) ? row[2] : [];
            html += this.generateSvedenRowHTML(step.id, blockIndex, rowIndex, left, right, subRows);
        });

        html += `
                            </tbody>
                        </table>
                        <button type="button" class="btn btn-sm btn-secondary sveden-add-row-btn" onclick="wizardManager.addSvedenRow('${step.id}', ${blockIndex})">+ строка</button>
                    </div>
                </div>
            </div>
        `;

        return html;
    }

    parseSvedenFileValue(value) {
        if (!value || typeof value !== 'string') return { isFile: false, displayName: '', fullValue: '' };
        const v = value.trim();
        if (v.includes('|')) {
            const idx = v.lastIndexOf('|');
            const partAfter = v.slice(idx + 1).trim();
            const partBefore = v.slice(0, idx).trim();
            const looksLikePath = /^(\/|https?:)/.test(partBefore) || partBefore.indexOf('/') >= 0;
            if (looksLikePath && partAfter) return { isFile: true, displayName: partAfter, fullValue: v };
        }
        if (/^\/?(info\/)?download_file\//.test(v)) {
            const name = v.replace(/^.*\//, '').trim() || v;
            let displayName = name;
            try {
                displayName = decodeURIComponent(name);
            } catch (_) {}
            return { isFile: true, displayName: displayName, fullValue: v };
        }
        return { isFile: false, displayName: '', fullValue: v };
    }

    parseSvedenFilesValue(value) {
        if (!value || typeof value !== 'string') return [];
        const files = [];
        const parts = value.split(',').map(p => p.trim()).filter(p => p);
        parts.forEach(part => {
            const fileInfo = this.parseSvedenFileValue(part);
            if (fileInfo.isFile) {
                files.push(fileInfo);
            }
        });
        return files;
    }

    generateSvedenRowHTML(stepId, blockIndex, rowIndex, leftValue, rightValue, subRows = []) {
        const filesList = this.parseSvedenFilesValue(rightValue);
        const hasFiles = filesList.length > 0;
        const filesDisplayHtml = hasFiles
            ? `<div class="sveden-files-list" data-step-id="${stepId}" data-block-index="${blockIndex}" data-row-index="${rowIndex}" style="margin-bottom: 8px;">
                ${filesList.map((fileInfo, fileIndex) => `
                    <div class="sveden-file-item" data-file-index="${fileIndex}" style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; margin-bottom: 5px; background: #f8fafc; border-radius: 6px; border: 1px solid #e5e7eb;">
                        <span class="sveden-file-name" style="flex: 1;">${this.escapeHtml(fileInfo.displayName)}</span>
                        <button type="button" class="btn btn-xs btn-danger sveden-file-remove-btn" onclick="wizardManager.removeSvedenCellFile('${stepId}', ${blockIndex}, ${rowIndex}, ${fileIndex})">×</button>
                    </div>
                `).join('')}
               </div>`
            : '';
        
        const subRowsHtml = Array.isArray(subRows) && subRows.length > 0 
            ? subRows.map((subRow, subIndex) => this.generateSvedenSubRowHTML(stepId, blockIndex, rowIndex, subIndex, subRow.name || '', subRow.text || '')).join('')
            : '';
        
        return `
            <tr class="wizard-block-row" data-step-id="${stepId}" data-block-index="${blockIndex}" data-row-index="${rowIndex}">
                <td class="cell-name">
                    <input type="text" class="wizard-input wizard-block-row-label" value="${this.escapeHtml(leftValue || '')}" placeholder="Название пункта" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #e5e7eb;">
                </td>
                <td class="cell-value">
                    <div class="sveden-cell-value-wrap">
                        ${filesDisplayHtml}
                        <textarea class="wizard-input wizard-block-row-value" rows="2" placeholder="Текст пункта или ссылка/путь к файлу" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #e5e7eb; resize: vertical; height: 60px; font-family: inherit; line-height: 1.5;">${this.escapeHtml((rightValue || '').trim())}</textarea>
                        <div class="sveden-cell-actions" style="margin-top: 8px;">
                            <button type="button" class="btn btn-xs btn-secondary sveden-upload-btn" onclick="wizardManager.uploadSvedenCellFiles('${stepId}', ${blockIndex}, ${rowIndex})">Загрузить файлы</button>
                        </div>
                    </div>
                    <div class="sveden-subrows-container" data-step-id="${stepId}" data-block-index="${blockIndex}" data-row-index="${rowIndex}" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #e5e7eb; display: flex; flex-direction: column;">
                        ${subRowsHtml}
                        <button type="button" class="btn btn-xs btn-secondary sveden-add-subrow-btn" onclick="wizardManager.addSvedenSubRow('${stepId}', ${blockIndex}, ${rowIndex})" style="margin-top: 5px; align-self: flex-start;">+ подстрока</button>
                    </div>
                </td>
                <td class="cell-actions">
                    <button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeSvedenRow('${stepId}', ${blockIndex}, ${rowIndex})">×</button>
                </td>
            </tr>
        `;
    }

    generateSvedenSubRowHTML(stepId, blockIndex, rowIndex, subRowIndex, nameValue, textValue) {
        const filesList = this.parseSvedenFilesValue(textValue);
        const hasFiles = filesList.length > 0;
        const filesDisplayHtml = hasFiles
            ? `<div class="sveden-files-list" data-step-id="${stepId}" data-block-index="${blockIndex}" data-row-index="${rowIndex}" data-subrow-index="${subRowIndex}" style="margin-bottom: 8px;">
                ${filesList.map((fileInfo, fileIndex) => `
                    <div class="sveden-file-item" data-file-index="${fileIndex}" style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; margin-bottom: 5px; background: #f8fafc; border-radius: 6px; border: 1px solid #e5e7eb;">
                        <span class="sveden-file-name" style="flex: 1;">${this.escapeHtml(fileInfo.displayName)}</span>
                        <button type="button" class="btn btn-xs btn-danger sveden-file-remove-btn" onclick="wizardManager.removeSvedenSubRowFile('${stepId}', ${blockIndex}, ${rowIndex}, ${subRowIndex}, ${fileIndex})">×</button>
                    </div>
                `).join('')}
               </div>`
            : '';
        
        return `
            <div class="sveden-subrow" data-step-id="${stepId}" data-block-index="${blockIndex}" data-row-index="${rowIndex}" data-subrow-index="${subRowIndex}" style="display: flex; gap: 10px; margin-bottom: 10px; align-items: flex-start; padding: 10px; background: #f8fafc; border-radius: 6px; border: 1px solid #e5e7eb;">
                <div style="flex: 1;">
                    <input type="text" class="wizard-input wizard-block-subrow-name" value="${this.escapeHtml(nameValue || '')}" placeholder="Название подстроки" style="width: 100%; padding: 8px; margin-bottom: 8px; border-radius: 6px; border: 1px solid #e5e7eb;">
                    <div class="sveden-cell-value-wrap">
                        ${filesDisplayHtml}
                        <textarea class="wizard-input wizard-block-subrow-value" rows="2" placeholder="Текст подстроки или ссылка/путь к файлу" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #e5e7eb; resize: vertical; height: 60px; font-family: inherit; line-height: 1.5;">${this.escapeHtml((textValue || '').trim())}</textarea>
                        <div class="sveden-cell-actions" style="margin-top: 8px;">
                            <button type="button" class="btn btn-xs btn-secondary sveden-upload-btn" onclick="wizardManager.uploadSvedenSubRowFiles('${stepId}', ${blockIndex}, ${rowIndex}, ${subRowIndex})">Загрузить файлы</button>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeSvedenSubRow('${stepId}', ${blockIndex}, ${rowIndex}, ${subRowIndex})">×</button>
            </div>
        `;
    }


    generateFieldHTML(field, stepId) {
        const value = this.wizardData[stepId] && this.wizardData[stepId][field.name] ? this.wizardData[stepId][field.name] : '';
        const required = field.required ? 'required' : '';
        
        let html = `
            <div class="wizard-field">
                <label class="wizard-label">
                    <i class="icon">${this.getFieldIcon(field.type)}</i> ${field.label}
                    ${field.required ? '<span class="required">*</span>' : ''}
                </label>
        `;

        switch (field.type) {
            case 'textarea':
                // Увеличиваем размер textarea для полей вакансий
                const isVacancyField = field.name && (field.name.includes('vacancies') || field.name.includes('vacancy'));
                const rows = isVacancyField ? '8' : '4';
                html += `<textarea name="${field.name}" class="wizard-input" rows="${rows}" ${required}>${value}</textarea>`;
                break;
            case 'file_or_text':
                html += this.generateFileOrTextHTML(field, value, stepId);
                break;
            case 'images':
                html += this.generateImageFieldHTML(field, value, stepId);
                break;
            case 'documents':
                html += this.generateDocumentFieldHTML(field, value, stepId);
                break;
            default:
                html += `<input type="${field.type}" name="${field.name}" class="wizard-input" value="${value}" ${required}>`;
        }

        html += '</div>';
        return html;
    }

    generateFileOrTextHTML(field, value, stepId) {
        const isFile = value && value.startsWith('/download_file/');
        const isUrl = value && value.startsWith('http');
        
        // По умолчанию показываем режим "Файл" для файловых полей
        const defaultMode = isFile || isUrl ? (isFile ? 'file' : 'url') : 'file';
        
        return `
            <div class="file-or-text-container">
                <div class="input-type-toggle">
                    <button type="button" class="btn btn-sm ${defaultMode === 'url' ? 'active' : ''}" onclick="toggleInputType('${field.name}', 'url')">🔗 Ссылка</button>
                    <button type="button" class="btn btn-sm ${defaultMode === 'file' ? 'active' : ''}" onclick="toggleInputType('${field.name}', 'file')">📎 Файл</button>
                </div>
                <div id="${field.name}_url_container" style="display: ${defaultMode === 'url' ? 'block' : 'none'};">
                    <input type="url" name="${field.name}_url" class="wizard-input" placeholder="Введите URL ссылку" value="${isUrl ? value : ''}">
                </div>
                <div id="${field.name}_file_container" style="display: ${defaultMode === 'file' ? 'block' : 'none'};">
                    <div class="file-upload-container" id="${field.name}_upload_container">
                        <div class="file-drop-zone" id="${field.name}_drop_zone" ondrop="wizardManager.handleFileDrop(event, '${field.name}')" ondragover="wizardManager.handleDragOver(event)" ondragleave="wizardManager.handleDragLeave(event)">
                            <div class="drop-zone-content">
                                <i class="icon">📁</i>
                                <p>Перетащите файлы сюда или <span class="file-select-link" onclick="document.getElementById('${field.name}_file_input').click()">выберите файлы</span></p>
                                <p class="file-types">Поддерживаются: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF</p>
                            </div>
                        </div>
                        <input type="file" id="${field.name}_file_input" name="${field.name}" style="display: none;" onchange="wizardManager.handleFileSelect(event, '${field.name}')" multiple>
                        <div id="${field.name}_file_list" class="file-list"></div>
                    </div>
                </div>
            </div>
        `;
    }

    generateImageFieldHTML(field, value, stepId) {
        return `
            <div class="file-upload-container" id="${field.name}_upload_container">
                <div class="file-drop-zone" id="${field.name}_drop_zone" ondrop="wizardManager.handleImageDrop(event, '${field.name}')" ondragover="wizardManager.handleDragOver(event)" ondragleave="wizardManager.handleDragLeave(event)">
                    <div class="drop-zone-content">
                        <i class="icon">🖼️</i>
                        <p>Перетащите изображения сюда или <span class="file-select-link" onclick="document.getElementById('${field.name}_image_input').click()">выберите изображения</span></p>
                        <p class="file-types">Поддерживаются: JPG, JPEG, PNG, GIF</p>
                    </div>
                </div>
                <input type="file" id="${field.name}_image_input" name="${field.name}" accept="image/*" style="display: none;" onchange="wizardManager.handleImageSelect(event, '${field.name}')" multiple>
                <div id="${field.name}_image_list" class="image-list"></div>
            </div>
        `;
    }

    generateDocumentFieldHTML(field, value, stepId) {
        return `
            <div class="file-upload-container" id="${field.name}_upload_container">
                <div class="file-drop-zone" id="${field.name}_drop_zone" ondrop="wizardManager.handleDocumentDrop(event, '${field.name}')" ondragover="wizardManager.handleDragOver(event)" ondragleave="wizardManager.handleDragLeave(event)">
                    <div class="drop-zone-content">
                        <i class="icon">📄</i>
                        <p>Перетащите документы сюда или <span class="file-select-link" onclick="document.getElementById('${field.name}_document_input').click()">выберите документы</span></p>
                        <p class="file-types">Поддерживаются: PDF, DOC, DOCX, TXT</p>
                    </div>
                </div>
                <input type="file" id="${field.name}_document_input" name="${field.name}" accept=".pdf,.doc,.docx,.txt" style="display: none;" onchange="wizardManager.handleDocumentSelect(event, '${field.name}')" multiple>
                <div id="${field.name}_document_list" class="document-list"></div>
            </div>
        `;
    }

    getFieldIcon(type) {
        const icons = {
            'text': '📝',
            'textarea': '📄',
            'email': '📧',
            'url': '🔗',
            'date': '📅',
            'file': '📎',
            'file_or_text': '📎',
            'images': '🖼️',
            'documents': '📄'
        };
        return icons[type] || '📝';
    }

    initializeStepFields(step) {
        // Инициализация полей шага
        if (Array.isArray(step.fields)) {
            step.fields.forEach(field => {
                if (field.type === 'file_or_text') {
                    // Устанавливаем режим "Файл" по умолчанию для файловых полей
                    setTimeout(() => {
                        this.toggleInputType(field.name, 'file');
                        this.loadExistingFiles(field.name, step.id);
                    }, 100);
                } else if (field.type === 'images') {
                    // Загружаем существующие изображения
                    setTimeout(() => {
                        this.loadExistingImages(field.name, step.id);
                    }, 100);
                } else if (field.type === 'documents') {
                    // Загружаем существующие документы
                    setTimeout(() => {
                        this.loadExistingDocuments(field.name, step.id);
                    }, 100);
                }
            });
        }
    }

    async loadExistingFiles(fieldName, stepId) {
        const fileList = document.getElementById(`${fieldName}_file_list`);
        if (!fileList) return;

        try {
            // Получаем файлы из базы данных
            const step = this.wizardSteps.find(s => s.id === stepId);
            const section = step ? step.endpoint : 'main';
            const module = step && step.module ? step.module : 'info';
            
            const response = await fetch(`/${module}/get_section_files/${section}?field_name=${fieldName}`);
            const result = await response.json();
            
            if (result.success && result.files) {
                // Очищаем список перед загрузкой новых файлов
                fileList.innerHTML = '';

                // Дедуп по базовому имени файла (без суффиксов _2, _3) и расширению
                const seen = new Set();
                const normalize = (name) => {
                    if (!name) return '';
                    const parts = name.split('.');
                    const ext = parts.length > 1 ? '.' + parts.pop().toLowerCase() : '';
                    let base = parts.join('.');
                    const baseParts = base.split('_');
                    if (baseParts.length > 1 && /^\d+$/.test(baseParts[baseParts.length - 1])) {
                        baseParts.pop();
                        base = baseParts.join('_');
                    }
                    return (base + ext).toLowerCase();
                };

                result.files.forEach(fileInfo => {
                    const fname = fileInfo.filename || (fileInfo.url ? fileInfo.url.split('/').pop() : '');
                    const key = normalize(fname);
                    if (seen.has(key)) return;
                    seen.add(key);
                    const displayName = fileInfo.display_name || fileInfo.original_filename || fileInfo.filename || fname;
                    this.addFileToList(fieldName, displayName, fileInfo.url, fileInfo.is_image, fileInfo.id);
                });
            } else {
                // Если файлов нет в БД, очищаем список
                fileList.innerHTML = '';
            }
        } catch (error) {
            console.error('Error loading existing files:', error);
            // НЕ используем fallback к form_data, так как там могут быть удаленные файлы
            // Вместо этого просто очищаем список
            const fileList = document.getElementById(`${fieldName}_file_list`);
            if (fileList) {
                fileList.innerHTML = '';
            }
        }
    }

    addFileToList(fieldName, displayName, url, isImage = false, fileId = null) {
        const fileList = document.getElementById(`${fieldName}_file_list`);
        if (!fileList) return;
        
        // Проверяем, что url существует и является строкой
        if (!url || typeof url !== 'string') {
            console.error('addFileToList: url is undefined or not a string', { fieldName, displayName, url });
            return;
        }
        
        // Извлекаем имя файла из URL для проверки дубликатов
        const urlFilename = url.split('/').pop().split('|')[0].trim();
        const normalizeFilename = (name) => {
            if (!name) return '';
            // Убираем суффиксы _2, _3 и т.д. для сравнения
            const parts = name.split('.');
            const ext = parts.length > 1 ? '.' + parts.pop().toLowerCase() : '';
            let base = parts.join('.');
            const baseParts = base.split('_');
            if (baseParts.length > 1 && /^\d+$/.test(baseParts[baseParts.length - 1])) {
                baseParts.pop();
                base = baseParts.join('_');
            }
            return (base + ext).toLowerCase();
        };
        const normalizedUrlFilename = normalizeFilename(urlFilename);
        
        // Проверяем, нет ли уже этого файла в списке (по URL и по имени файла)
        const existingItems = fileList.querySelectorAll('.file-url');
        for (let item of existingItems) {
            const existingUrl = item.textContent.trim();
            const existingFilename = existingUrl.split('/').pop().split('|')[0].trim();
            const normalizedExistingFilename = normalizeFilename(existingFilename);
            
            // Проверяем по точному совпадению URL или по нормализованному имени файла
            if (existingUrl === url || normalizedExistingFilename === normalizedUrlFilename) {
                // Файл уже есть в списке, не добавляем дубликат
                console.log(`Файл уже есть в списке, пропускаем: ${url} (существующий: ${existingUrl})`);
                return;
            }
        }
        
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; margin: 4px 0; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;';
        
        const fileInfo = document.createElement('div');
        fileInfo.style.cssText = 'display: flex; align-items: center; flex: 1;';
        
        const fileIcon = document.createElement('span');
        fileIcon.style.cssText = 'margin-right: 8px; font-size: 16px;';
        fileIcon.textContent = isImage ? '🖼️' : '📄';
        
        // Поле для отображения имени файла
        const displayNameInput = document.createElement('input');
        displayNameInput.type = 'text';
        displayNameInput.value = displayName;
        displayNameInput.className = 'file-display-name';
        displayNameInput.style.cssText = 'flex: 1; margin-right: 8px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;';
        displayNameInput.placeholder = 'Имя файла для отображения';
        
        // Обработчик изменения имени файла
        displayNameInput.addEventListener('change', async () => {
            if (fileId) {
                await this.updateFileDisplayName(fileId, displayNameInput.value);
            }
        });
        
        const fileLink = document.createElement('a');
        fileLink.href = url;
        fileLink.textContent = 'Скачать';
        fileLink.style.cssText = 'color: #2563eb; text-decoration: none; font-weight: 500; margin-right: 8px;';
        fileLink.target = '_blank';
        
        const urlSpan = document.createElement('span');
        urlSpan.className = 'file-url';
        urlSpan.textContent = url;
        urlSpan.style.display = 'none';
        
        // Скрытое поле ID файла (для будущих обновлений имени)
        const fileIdSpan = document.createElement('span');
        fileIdSpan.className = 'file-file-id';
        fileIdSpan.textContent = fileId || '';
        fileIdSpan.style.display = 'none';

        const removeBtn = document.createElement('button');
        removeBtn.textContent = '×';
        removeBtn.className = 'file-remove';
        removeBtn.style.cssText = 'background: #dc3545; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 14px; margin-left: 8px;';
        removeBtn.onclick = () => this.removeFile(fieldName, url);
        
        fileInfo.appendChild(fileIcon);
        fileInfo.appendChild(displayNameInput);
        fileInfo.appendChild(fileLink);
        fileInfo.appendChild(urlSpan);
        fileInfo.appendChild(fileIdSpan);
        fileItem.appendChild(fileInfo);
        fileItem.appendChild(removeBtn);
        
        fileList.appendChild(fileItem);
    }

    addImageToList(fieldName, displayName, url, fileId = null) {
        const imageList = document.getElementById(`${fieldName}_image_list`);
        if (!imageList) return;
        
        // Проверяем, что url существует и является строкой
        if (!url || typeof url !== 'string') {
            console.error('addImageToList: url is undefined or not a string', { fieldName, displayName, url });
            return;
        }
        
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';
        imageItem.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; margin: 4px 0; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;';
        
        const imageInfo = document.createElement('div');
        imageInfo.style.cssText = 'display: flex; align-items: center; flex: 1;';
        
        const imageIcon = document.createElement('span');
        imageIcon.style.cssText = 'margin-right: 8px; font-size: 16px;';
        imageIcon.textContent = '🖼️';
        
        // Превью изображения
        const imagePreview = document.createElement('img');
        imagePreview.src = url;
        imagePreview.style.cssText = 'width: 40px; height: 40px; object-fit: cover; border-radius: 4px; margin-right: 8px;';
        imagePreview.alt = displayName;
        
        // Поле для отображения имени файла
        const displayNameInput = document.createElement('input');
        displayNameInput.type = 'text';
        displayNameInput.value = displayName;
        displayNameInput.className = 'image-display-name';
        displayNameInput.style.cssText = 'flex: 1; margin-right: 8px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;';
        displayNameInput.placeholder = 'Имя файла для отображения';
        
        // Обработчик изменения имени файла
        displayNameInput.addEventListener('change', async () => {
            if (fileId) {
                await this.updateFileDisplayName(fileId, displayNameInput.value);
            }
        });
        
        const imageLink = document.createElement('a');
        imageLink.href = url;
        imageLink.textContent = 'Открыть';
        imageLink.style.cssText = 'color: #2563eb; text-decoration: none; font-weight: 500; margin-right: 8px;';
        imageLink.target = '_blank';
        
        const urlSpan = document.createElement('span');
        urlSpan.className = 'image-url';
        urlSpan.textContent = url;
        urlSpan.style.display = 'none';
        
        const fileIdSpan = document.createElement('span');
        fileIdSpan.className = 'image-file-id';
        fileIdSpan.textContent = fileId || '';
        fileIdSpan.style.display = 'none';
        
        const removeBtn = document.createElement('button');
        removeBtn.textContent = '×';
        removeBtn.className = 'image-remove';
        removeBtn.style.cssText = 'background: #dc3545; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 14px; margin-left: 8px;';
        removeBtn.onclick = () => this.removeImage(fieldName, url, fileId);
        
        imageInfo.appendChild(imageIcon);
        imageInfo.appendChild(imagePreview);
        imageInfo.appendChild(displayNameInput);
        imageInfo.appendChild(imageLink);
        imageInfo.appendChild(urlSpan);
        imageInfo.appendChild(fileIdSpan);
        imageItem.appendChild(imageInfo);
        imageItem.appendChild(removeBtn);
        
        imageList.appendChild(imageItem);
    }

    addDocumentToList(fieldName, displayName, url, fileId = null) {
        const documentList = document.getElementById(`${fieldName}_document_list`);
        if (!documentList) return;
        
        // Проверяем, что url существует и является строкой
        if (!url || typeof url !== 'string') {
            console.error('addDocumentToList: url is undefined or not a string', { fieldName, displayName, url });
            return;
        }
        
        // Извлекаем имя файла из URL для проверки дубликатов
        const urlFilename = url.split('/').pop().split('|')[0].trim();
        const normalizeFilename = (name) => {
            if (!name) return '';
            // Убираем суффиксы _2, _3 и т.д. для сравнения
            const parts = name.split('.');
            const ext = parts.length > 1 ? '.' + parts.pop().toLowerCase() : '';
            let base = parts.join('.');
            const baseParts = base.split('_');
            if (baseParts.length > 1 && /^\d+$/.test(baseParts[baseParts.length - 1])) {
                baseParts.pop();
                base = baseParts.join('_');
            }
            return (base + ext).toLowerCase();
        };
        const normalizedUrlFilename = normalizeFilename(urlFilename);
        
        // Проверяем, нет ли уже этого файла в списке (по URL и по имени файла)
        const existingItems = documentList.querySelectorAll('.document-url');
        for (let item of existingItems) {
            const existingUrl = item.textContent.trim();
            const existingFilename = existingUrl.split('/').pop().split('|')[0].trim();
            const normalizedExistingFilename = normalizeFilename(existingFilename);
            
            // Проверяем по точному совпадению URL или по нормализованному имени файла
            if (existingUrl === url || normalizedExistingFilename === normalizedUrlFilename) {
                // Файл уже есть в списке, не добавляем дубликат
                console.log(`Документ уже есть в списке, пропускаем: ${url} (существующий: ${existingUrl})`);
                return;
            }
        }
        
        const documentItem = document.createElement('div');
        documentItem.className = 'document-item';
        documentItem.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; margin: 4px 0; background: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;';
        
        const documentInfo = document.createElement('div');
        documentInfo.style.cssText = 'display: flex; align-items: center; flex: 1;';
        
        const documentIcon = document.createElement('span');
        documentIcon.style.cssText = 'margin-right: 8px; font-size: 16px;';
        documentIcon.textContent = '📄';
        
        // Поле для отображения имени файла
        const displayNameInput = document.createElement('input');
        displayNameInput.type = 'text';
        displayNameInput.value = displayName;
        displayNameInput.className = 'document-display-name';
        displayNameInput.style.cssText = 'flex: 1; margin-right: 8px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;';
        displayNameInput.placeholder = 'Имя файла для отображения';
        
        // Обработчик изменения имени файла
        displayNameInput.addEventListener('change', async () => {
            if (fileId) {
                await this.updateFileDisplayName(fileId, displayNameInput.value);
            }
        });
        
        const documentLink = document.createElement('a');
        documentLink.href = url;
        documentLink.textContent = 'Скачать';
        documentLink.style.cssText = 'color: #2563eb; text-decoration: none; font-weight: 500; margin-right: 8px;';
        documentLink.target = '_blank';
        
        const urlSpan = document.createElement('span');
        urlSpan.className = 'document-url';
        urlSpan.textContent = url;
        urlSpan.style.display = 'none';
        
        const fileIdSpan = document.createElement('span');
        fileIdSpan.className = 'document-file-id';
        fileIdSpan.textContent = fileId || '';
        fileIdSpan.style.display = 'none';
        
        const removeBtn = document.createElement('button');
        removeBtn.textContent = '×';
        removeBtn.className = 'document-remove';
        removeBtn.style.cssText = 'background: #dc3545; color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-size: 14px; margin-left: 8px;';
        removeBtn.onclick = () => this.removeDocument(fieldName, url, fileId);
        
        documentInfo.appendChild(documentIcon);
        documentInfo.appendChild(displayNameInput);
        documentInfo.appendChild(documentLink);
        documentInfo.appendChild(urlSpan);
        documentInfo.appendChild(fileIdSpan);
        documentItem.appendChild(documentInfo);
        documentItem.appendChild(removeBtn);
        
        documentList.appendChild(documentItem);
    }

    async removeFile(fieldName, fileUrl) {
        try {
            // Получаем правильный раздел из текущего шага
            const step = this.wizardSteps[this.currentStep];
            const section = step ? step.endpoint : 'main';
            const module = step && step.module ? step.module : 'info';
            
            // Извлекаем имя файла из URL (убираем возможные параметры после |)
            const filename = fileUrl.split('/').pop().split('|')[0].trim();
            
            const response = await fetch(`/${module}/delete_file`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    section: section,
                    field_name: fieldName
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', 'Файл удален');
                // Перезагружаем список файлов из БД
                await this.loadExistingFiles(fieldName, step.id);
            } else {
                this.showSaveStatus('error', 'Ошибка при удалении файла');
            }
        } catch (error) {
            console.error('Error removing file:', error);
            this.showSaveStatus('error', 'Ошибка при удалении файла');
        }
    }

    removeFileFromUI(fieldName, fileUrl) {
        // Находим и удаляем элемент файла из интерфейса
        const fileList = document.getElementById(`${fieldName}_file_list`);
        if (fileList) {
            const fileItems = fileList.querySelectorAll('.file-item');
            fileItems.forEach(item => {
                const urlSpan = item.querySelector('.file-url');
                if (urlSpan && urlSpan.textContent === fileUrl) {
                    item.remove();
                }
            });
        }
    }

    async updateFileDisplayName(fileId, displayName) {
        try {
            const response = await fetch('/info/update_file_display_name', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_id: fileId,
                    display_name: displayName
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', 'Имя файла обновлено');
            } else {
                this.showSaveStatus('error', 'Ошибка при обновлении имени файла');
            }
        } catch (error) {
            console.error('Error updating file display name:', error);
            this.showSaveStatus('error', 'Ошибка при обновлении имени файла');
        }
    }

    async removeImage(fieldName, imageUrl) {
        try {
            const step = this.wizardSteps[this.currentStep];
            const section = step ? step.endpoint : 'main';
            const module = step && step.module ? step.module : 'info';
            
            // Извлекаем имя файла из URL (убираем возможные параметры после |)
            const filename = imageUrl.split('/').pop().split('|')[0].trim();
            
            const response = await fetch(`/${module}/delete_file`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    section: section,
                    field_name: fieldName
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', 'Изображение удалено');
                // Перезагружаем список изображений из БД
                await this.loadExistingImages(fieldName, step.id);
            } else {
                this.showSaveStatus('error', 'Ошибка при удалении изображения');
            }
        } catch (error) {
            console.error('Error removing image:', error);
            this.showSaveStatus('error', 'Ошибка при удалении изображения');
        }
    }

    removeImageFromUI(fieldName, imageUrl) {
        // Находим и удаляем элемент изображения из интерфейса
        const imageList = document.getElementById(`${fieldName}_image_list`);
        if (imageList) {
            const imageItems = imageList.querySelectorAll('.image-item');
            imageItems.forEach(item => {
                const urlSpan = item.querySelector('.image-url');
                if (urlSpan && urlSpan.textContent === imageUrl) {
                    item.remove();
                }
            });
        }
    }

    async removeDocument(fieldName, documentUrl) {
        try {
            const step = this.wizardSteps[this.currentStep];
            const section = step ? step.endpoint : 'main';
            const module = step && step.module ? step.module : 'info';
            
            // Извлекаем имя файла из URL (убираем возможные параметры после |)
            const filename = documentUrl.split('/').pop().split('|')[0].trim();
            
            const response = await fetch(`/${module}/delete_file`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    section: section,
                    field_name: fieldName
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', 'Документ удален');
                // Перезагружаем список документов из БД
                await this.loadExistingDocuments(fieldName, step.id);
            } else {
                this.showSaveStatus('error', 'Ошибка при удалении документа');
            }
        } catch (error) {
            console.error('Error removing document:', error);
            this.showSaveStatus('error', 'Ошибка при удалении документа');
        }
    }

    removeDocumentFromUI(fieldName, documentUrl) {
        // Находим и удаляем элемент документа из интерфейса
        const documentList = document.getElementById(`${fieldName}_document_list`);
        if (documentList) {
            const documentItems = documentList.querySelectorAll('.document-item');
            documentItems.forEach(item => {
                const urlSpan = item.querySelector('.document-url');
                if (urlSpan && urlSpan.textContent === documentUrl) {
                    item.remove();
                }
            });
        }
    }

    async loadExistingImages(fieldName, stepId) {
        const imageList = document.getElementById(`${fieldName}_image_list`);
        if (!imageList) return;

        try {
            // Получаем изображения из базы данных
            const step = this.wizardSteps.find(s => s.id === stepId);
            const section = step ? step.endpoint : 'main';
            const module = step && step.module ? step.module : 'info';
            
            const response = await fetch(`/${module}/get_section_files/${section}?field_name=${fieldName}`);
            const result = await response.json();
            
            if (result.success && result.files) {
                // Очищаем список перед загрузкой новых изображений
                imageList.innerHTML = '';
                result.files.forEach(fileInfo => {
                    if (fileInfo.is_image) {
                        // Используем display_name или original_filename
                        const displayName = fileInfo.display_name || fileInfo.original_filename || fileInfo.filename;
                        this.addImageToList(fieldName, displayName, fileInfo.url, fileInfo.id);
                    }
                });
            } else {
                // Если изображений нет в БД, очищаем список
                imageList.innerHTML = '';
            }
        } catch (error) {
            console.error('Error loading existing images:', error);
            // НЕ используем fallback к form_data
            const imageList = document.getElementById(`${fieldName}_image_list`);
            if (imageList) {
                imageList.innerHTML = '';
            }
        }
    }

    async loadExistingDocuments(fieldName, stepId) {
        const documentList = document.getElementById(`${fieldName}_document_list`);
        if (!documentList) return;

        try {
            // Получаем документы из базы данных
            const step = this.wizardSteps.find(s => s.id === stepId);
            const section = step ? step.endpoint : 'main';
            const module = step && step.module ? step.module : 'info';
            
            const response = await fetch(`/${module}/get_section_files/${section}?field_name=${fieldName}`);
            const result = await response.json();
            
            if (result.success && result.files) {
                // Очищаем список перед загрузкой новых документов
                documentList.innerHTML = '';

                // Дедуп по базовому имени файла (без суффиксов _2, _3) и расширению
                const seen = new Set();
                const normalize = (name) => {
                    if (!name) return '';
                    const parts = name.split('.');
                    const ext = parts.length > 1 ? '.' + parts.pop().toLowerCase() : '';
                    let base = parts.join('.');
                    const baseParts = base.split('_');
                    if (baseParts.length > 1 && /^\d+$/.test(baseParts[baseParts.length - 1])) {
                        baseParts.pop();
                        base = baseParts.join('_');
                    }
                    return (base + ext).toLowerCase();
                };

                result.files.forEach(fileInfo => {
                    if (!fileInfo.is_image) {
                        const fname = fileInfo.filename || (fileInfo.url ? fileInfo.url.split('/').pop() : '');
                        const key = normalize(fname);
                        if (seen.has(key)) return;
                        seen.add(key);
                        const displayName = fileInfo.display_name || fileInfo.original_filename || fileInfo.filename || fname;
                        this.addDocumentToList(fieldName, displayName, fileInfo.url, fileInfo.id);
                    }
                });
            } else {
                // Если документов нет в БД, очищаем список
                documentList.innerHTML = '';
            }
        } catch (error) {
            console.error('Error loading existing documents:', error);
            // НЕ используем fallback к form_data
            const documentList = document.getElementById(`${fieldName}_document_list`);
            if (documentList) {
                documentList.innerHTML = '';
            }
        }
    }

    toggleInputType(fieldName, type) {
        console.log(`Переключение поля ${fieldName} на режим: ${type}`);
        const urlContainer = document.getElementById(`${fieldName}_url_container`);
        const fileContainer = document.getElementById(`${fieldName}_file_container`);
        
        // Скрыть все контейнеры
        if (urlContainer) urlContainer.style.display = 'none';
        if (fileContainer) fileContainer.style.display = 'none';
        
        // Показать нужный контейнер
        switch (type) {
            case 'url':
                if (urlContainer) urlContainer.style.display = 'block';
                break;
            case 'file':
                if (fileContainer) fileContainer.style.display = 'block';
                break;
        }
        console.log(`Поле ${fieldName} переключено на режим: ${type}`);
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.currentTarget.classList.remove('drag-over');
    }

    handleFileDrop(e, fieldName) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        this.handleFiles(files, fieldName);
    }

    handleFileSelect(e, fieldName) {
        const files = e.target.files;
        this.handleFiles(files, fieldName);
    }

    async handleFiles(files, fieldName) {
        if (files.length === 0) return;
        
        const step = this.wizardSteps[this.currentStep];
        await this.uploadFiles(files, fieldName, step.id);
        // Не перезагружаем весь контент, чтобы не сбрасывать режим "Файл"
        // this.loadStepContent(step);
    }

    async uploadFiles(files, fieldName, stepId) {
        const step = this.wizardSteps.find(s => s.id === stepId);
        const section = step ? step.endpoint : 'general';
        const module = step && step.module ? step.module : 'info';
        
        const uploadPromises = Array.from(files).map(async (file) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('section', section);
            formData.append('field_name', fieldName);
            
            try {
                const response = await fetch(`/${module}/upload_file`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    return result;
                } else {
                    console.error('Upload failed:', result.error);
                    this.showSaveStatus('error', 'Ошибка загрузки: ' + result.error);
                    return null;
                }
            } catch (error) {
                console.error('Upload error:', error);
                this.showSaveStatus('error', 'Ошибка загрузки файла');
                return null;
            }
        });
        
        try {
            const uploadResults = await Promise.all(uploadPromises);
            const successfulUploads = uploadResults.filter(result => result !== null);
            
            if (successfulUploads.length > 0) {
                // Добавляем файлы с информацией из базы данных
                successfulUploads.forEach(fileInfo => {
                    // Используем display_name, если есть, иначе original_name
                    const displayName = fileInfo.display_name || fileInfo.original_name || fileInfo.filename;
                    this.addFileToList(fieldName, displayName, fileInfo.url, fileInfo.is_image, fileInfo.id);
                });
                this.showSaveStatus('success', `Загружено ${successfulUploads.length} файлов`);
            }
        } catch (error) {
            console.error('Error uploading files:', error);
            this.showSaveStatus('error', 'Ошибка при загрузке файлов');
        }
    }

    // Новые методы для обработки изображений
    handleImageDrop(e, fieldName) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files).filter(file => file.type.startsWith('image/'));
        this.handleImages(files, fieldName);
    }

    handleImageSelect(e, fieldName) {
        const files = Array.from(e.target.files).filter(file => file.type.startsWith('image/'));
        this.handleImages(files, fieldName);
    }

    async handleImages(files, fieldName) {
        if (files.length === 0) return;
        
        const step = this.wizardSteps[this.currentStep];
        await this.uploadImages(files, fieldName, step.id);
    }

    async uploadImages(files, fieldName, stepId) {
        const step = this.wizardSteps.find(s => s.id === stepId);
        const section = step ? step.endpoint : 'general';
        const module = step && step.module ? step.module : 'info';
        
        const uploadPromises = Array.from(files).map(async (file) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('section', section);
            formData.append('field_name', fieldName);
            formData.append('type', 'image');
            
            try {
                const response = await fetch(`/${module}/upload_file`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    return result;
                } else {
                    console.error('Image upload failed:', result.error);
                    this.showSaveStatus('error', 'Ошибка загрузки изображения: ' + result.error);
                    return null;
                }
            } catch (error) {
                console.error('Image upload error:', error);
                this.showSaveStatus('error', 'Ошибка загрузки изображения');
                return null;
            }
        });
        
        try {
            const uploadResults = await Promise.all(uploadPromises);
            const successfulUploads = uploadResults.filter(result => result !== null);
            
            if (successfulUploads.length > 0) {
                successfulUploads.forEach(fileInfo => {
                    // Используем display_name, если есть, иначе original_name
                    const displayName = fileInfo.display_name || fileInfo.original_name || fileInfo.filename;
                    this.addImageToList(fieldName, displayName, fileInfo.url, fileInfo.id);
                });
                this.showSaveStatus('success', `Загружено ${successfulUploads.length} изображений`);
            }
        } catch (error) {
            console.error('Error uploading images:', error);
            this.showSaveStatus('error', 'Ошибка при загрузке изображений');
        }
    }

    // Новые методы для обработки документов
    handleDocumentDrop(e, fieldName) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files).filter(file => 
            file.type === 'application/pdf' || 
            file.type === 'application/msword' || 
            file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
            file.type === 'text/plain'
        );
        this.handleDocuments(files, fieldName);
    }

    handleDocumentSelect(e, fieldName) {
        const files = Array.from(e.target.files).filter(file => 
            file.type === 'application/pdf' || 
            file.type === 'application/msword' || 
            file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
            file.type === 'text/plain'
        );
        this.handleDocuments(files, fieldName);
    }

    async handleDocuments(files, fieldName) {
        if (files.length === 0) return;
        
        const step = this.wizardSteps[this.currentStep];
        await this.uploadDocuments(files, fieldName, step.id);
    }

    async uploadDocuments(files, fieldName, stepId) {
        const step = this.wizardSteps.find(s => s.id === stepId);
        const section = step ? step.endpoint : 'general';
        const module = step && step.module ? step.module : 'info';
        
        const uploadPromises = Array.from(files).map(async (file) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('section', section);
            formData.append('field_name', fieldName);
            formData.append('type', 'document');
            
            try {
                const response = await fetch(`/${module}/upload_file`, {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    return result;
                } else {
                    console.error('Document upload failed:', result.error);
                    this.showSaveStatus('error', 'Ошибка загрузки документа: ' + result.error);
                    return null;
                }
            } catch (error) {
                console.error('Document upload error:', error);
                this.showSaveStatus('error', 'Ошибка загрузки документа');
                return null;
            }
        });
        
        try {
            const uploadResults = await Promise.all(uploadPromises);
            const successfulUploads = uploadResults.filter(result => result !== null);
            
            if (successfulUploads.length > 0) {
                successfulUploads.forEach(fileInfo => {
                    // Используем display_name, если есть, иначе original_name
                    const displayName = fileInfo.display_name || fileInfo.original_name || fileInfo.filename;
                    this.addDocumentToList(fieldName, displayName, fileInfo.url, fileInfo.id);
                });
                this.showSaveStatus('success', `Загружено ${successfulUploads.length} документов`);
            }
        } catch (error) {
            console.error('Error uploading documents:', error);
            this.showSaveStatus('error', 'Ошибка при загрузке документов');
        }
    }

    async cleanMissingFiles() {
        try {
            const response = await fetch('/info/clean_missing_files', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', result.message);
                this.loadWizardData();
                this.loadStepContent(this.wizardSteps[this.currentStep]);
            } else {
                this.showSaveStatus('error', 'Ошибка при очистке файлов');
            }
        } catch (error) {
            console.error('Error cleaning files:', error);
            this.showSaveStatus('error', 'Ошибка при очистке файлов');
        }
    }

    showSaveStatus(type, message) {
        const statusElement = document.getElementById('wizard-save-status');
        if (!statusElement) return;
        
        statusElement.className = 'wizard-save-status';
        statusElement.classList.add(type);
        statusElement.textContent = message;
        
        if (type !== 'error') {
            setTimeout(() => {
                statusElement.className = 'wizard-save-status';
                statusElement.textContent = '';
            }, 3000);
        }
    }

    nextStep() {
        if (this.currentStep < this.wizardSteps.length - 1) {
            this.saveCurrentStep();
            this.goToStep(this.currentStep + 1);
        } else {
            this.saveAllData();
        }
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.goToStep(this.currentStep - 1);
        }
    }

    async saveCurrentStep() {
        const step = this.wizardSteps[this.currentStep];
        if (!step) return;

        // Специальное сохранение для шагов основных сведений с блоками-таблицами.
        if (step.type === 'sveden-table-blocks') {
            if (this.mode === 'tags') {
                await this.saveSvedenTags(step);
            } else {
                await this.saveSvedenStep(step);
            }
            return;
        }
        
        // Собираем данные текущего шага
        const stepData = { ...this.wizardData[step.id] };
        
        (Array.isArray(step.fields) ? step.fields : []).forEach(field => {
            const inputElement = document.querySelector(`[name="${field.name}"]`);
            if (inputElement) {
                stepData[field.name] = inputElement.value || '';
            }
            
            // Обработка файловых полей с отображаемыми именами
            if (field.type === 'file_or_text') {
                const fileList = document.getElementById(`${field.name}_file_list`);
                if (fileList) {
                    const fileItems = fileList.querySelectorAll('.file-item');
                    const files = [];
                    fileItems.forEach(item => {
                        const urlSpan = item.querySelector('.file-url');
                        const displayNameInput = item.querySelector('.file-display-name');
                        if (urlSpan && displayNameInput) {
                            const url = urlSpan.textContent;
                            const displayName = displayNameInput.value;
                            files.push(`${url}|${displayName}`);
                        }
                    });
                    // Явно устанавливаем значение (пустое, если файлов нет)
                    stepData[field.name] = files.length > 0 ? files.join(',') : '';
                } else {
                    // Если список не найден, устанавливаем пустое значение
                    stepData[field.name] = '';
                }
            }
            
            // Обработка полей изображений
            if (field.type === 'images') {
                const imageList = document.getElementById(`${field.name}_image_list`);
                if (imageList) {
                    const imageItems = imageList.querySelectorAll('.image-item');
                    const images = [];
                    imageItems.forEach(item => {
                        const urlSpan = item.querySelector('.image-url');
                        const displayNameInput = item.querySelector('.image-display-name');
                        if (urlSpan && displayNameInput) {
                            const url = urlSpan.textContent;
                            const displayName = displayNameInput.value;
                            images.push(`${url}|${displayName}`);
                        }
                    });
                    // Явно устанавливаем значение (пустое, если изображений нет)
                    stepData[field.name] = images.length > 0 ? images.join(',') : '';
                } else {
                    // Если список не найден, устанавливаем пустое значение
                    stepData[field.name] = '';
                }
            }
            
            // Обработка полей документов
            if (field.type === 'documents') {
                const documentList = document.getElementById(`${field.name}_document_list`);
                if (documentList) {
                    const documentItems = documentList.querySelectorAll('.document-item');
                    const documents = [];
                    documentItems.forEach(item => {
                        const urlSpan = item.querySelector('.document-url');
                        const displayNameInput = item.querySelector('.document-display-name');
                        if (urlSpan && displayNameInput) {
                            const url = urlSpan.textContent;
                            const displayName = displayNameInput.value;
                            documents.push(`${url}|${displayName}`);
                        }
                    });
                    // Явно устанавливаем значение (пустое, если документов нет)
                    stepData[field.name] = documents.length > 0 ? documents.join(',') : '';
                } else {
                    // Если список не найден, устанавливаем пустое значение
                    stepData[field.name] = '';
                }
            }
            
            // Обработка полей file_with_name
            if (field.type === 'file_with_name') {
                const fileList = document.getElementById(`${field.name}_file_list`);
                if (fileList) {
                    const fileItems = fileList.querySelectorAll('.file-item');
                    if (fileItems.length > 0) {
                        const fileItem = fileItems[0];
                        const urlSpan = fileItem.querySelector('.file-url');
                        const displayNameInput = fileItem.querySelector('.file-display-name');
                        if (urlSpan && displayNameInput) {
                            const url = urlSpan.textContent;
                            const displayName = displayNameInput.value;
                            stepData[field.name] = {
                                url: url,
                                displayName: displayName,
                                filename: url.split('/').pop()
                            };
                        } else {
                            stepData[field.name] = '';
                        }
                    } else {
                        stepData[field.name] = '';
                    }
                } else {
                    stepData[field.name] = '';
                }
            }
        });
        
        this.wizardData[step.id] = stepData;
        
        // Отправляем данные на сервер
        try {
            const formData = new FormData();
            formData.append('wizard_data', JSON.stringify({[step.id]: stepData}));
            formData.append('save_single', 'true');
            
            const module = step.module || 'info';
            const response = await fetch(`/${module}/wizard_save`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', 'Шаг сохранен');
            } else {
                this.showSaveStatus('error', 'Ошибка сохранения');
            }
        } catch (error) {
            console.error('Error saving step:', error);
            this.showSaveStatus('error', 'Ошибка сохранения');
        }
    }

    /**
     * Сохранение шага основных сведений (табличные блоки).
     */
    async saveSvedenStep(step) {
        try {
            const blocksContainer = document.querySelector(`.wizard-blocks-list[data-step-id="${step.id}"]`);
            if (!blocksContainer) {
                return;
            }

            const blockElements = Array.from(blocksContainer.querySelectorAll('.wizard-block-item'));
            const blocks = [];
            const existingBlocks = (this.wizardData[step.id] && this.wizardData[step.id].content_blocks) || [];

            blockElements.forEach((blockEl, blockIndex) => {
                const blockType = blockEl.getAttribute('data-block-type') || 'table';
                const titleInput = blockEl.querySelector('.wizard-block-title-input');
                const title = titleInput ? (titleInput.value || '').trim() : '';
                const existingBlock = existingBlocks[blockIndex];

                if (blockType === 'person') {
                    const blockItempropInput = blockEl.querySelector('.sveden-person-block-itemprop');
                    const blockItemprop = blockItempropInput ? (blockItempropInput.value || '').trim() : '';
                    const personTypeSelect = blockEl.querySelector('.sveden-person-type-select');
                    const personType = personTypeSelect ? (personTypeSelect.value || 'rucovodstvo') : 'rucovodstvo';
                    const branchNameInput = blockEl.querySelector('.sveden-branch-name-input');
                    const branchName = branchNameInput ? (branchNameInput.value || '').trim() : '';
                    const personItems = Array.from(blockEl.querySelectorAll('.sveden-person-item'));
                    const persons = [];
                    let person_itemprop_mapping = {};
                    personItems.forEach((item, idx) => {
                        const getVal = (sel) => { const el = item.querySelector(sel); return el ? (el.value || '').trim() : ''; };
                        persons.push({
                            name: getVal('.person-name'),
                            position: getVal('.person-position'),
                            photo: getVal('.person-photo'),
                            email: getVal('.person-email'),
                            phone: getVal('.person-phone'),
                            description: getVal('.person-description'),
                            experience: getVal('.person-experience'),
                            education: getVal('.person-education'),
                            professional_retraining: getVal('.person-professional-retraining'),
                            awards: getVal('.person-awards'),
                            courses: getVal('.person-courses')
                        });
                        if (idx === 0) {
                            item.querySelectorAll('.sveden-itemprop-input').forEach(input => {
                                const field = input.getAttribute('data-person-field');
                                if (field) person_itemprop_mapping[field] = (input.value || '').trim();
                            });
                        }
                    });
                    const hasPersonContent = persons.some(p => [p.name, p.position, p.photo, p.email, p.phone, p.education, p.experience, p.description, p.professional_retraining, p.awards, p.courses].some(v => (v || '').trim()));
                    if (title || hasPersonContent || blockItemprop || Object.keys(person_itemprop_mapping).some(k => person_itemprop_mapping[k])) {
                        const blockData = { type: 'person', title: (title || '').trim(), person_type: personType, persons, person_itemprop_mapping };
                        if (blockItemprop) blockData.itemprop = blockItemprop;
                        if (personType === 'rucovodstvoFil' && branchName) {
                            blockData.branch_name = branchName;
                        }
                        blocks.push(blockData);
                    }
                    return;
                }

                const blockItemprop = (existingBlock && existingBlock.itemprop) ? String(existingBlock.itemprop).trim() : '';
                const existingRowItemprops = Array.isArray(existingBlock && existingBlock.row_itemprops) ? existingBlock.row_itemprops : [];

                const rowElements = Array.from(blockEl.querySelectorAll('.wizard-block-row'));
                const rows = [];
                const row_itemprops = [];

                rowElements.forEach((rowEl, rowIndex) => {
                    const labelInput = rowEl.querySelector('.wizard-block-row-label');
                    const valueInput = rowEl.querySelector('.wizard-block-row-value');
                    const left = labelInput ? (labelInput.value || '').trim() : '';
                    let right = valueInput ? (valueInput.value || '') : '';
                    
                    const filesList = this.parseSvedenFilesValue(right);
                    if (filesList.length > 0) {
                        right = filesList.map(f => f.fullValue).join(',');
                    } else {
                        right = right.trim();
                    }
                    
                    const rowItemprop = (existingRowItemprops[rowIndex] !== undefined) ? String(existingRowItemprops[rowIndex]).trim() : '';

                    const subRows = [];
                    const subRowElements = rowEl.querySelectorAll('.sveden-subrow');
                    subRowElements.forEach((subRowEl) => {
                        const nameInput = subRowEl.querySelector('.wizard-block-subrow-name');
                        const textInput = subRowEl.querySelector('.wizard-block-subrow-value');
                        const subName = nameInput ? (nameInput.value || '').trim() : '';
                        let subText = textInput ? (textInput.value || '') : '';
                        
                        const subFilesList = this.parseSvedenFilesValue(subText);
                        if (subFilesList.length > 0) {
                            subText = subFilesList.map(f => f.fullValue).join(',');
                        } else {
                            subText = subText.trim();
                        }
                        
                        if (subName || subText) {
                            subRows.push({ name: subName, text: subText });
                        }
                    });

                    if (left || right || subRows.length > 0) {
                        if (subRows.length > 0) {
                            rows.push([left, right, subRows]);
                        } else {
                            rows.push([left, right]);
                        }
                        row_itemprops.push(rowItemprop);
                    }
                });

                if (title || rows.length > 0 || blockItemprop) {
                    const blockData = {
                        type: 'table',
                        title: (title || '').trim(),
                        headers: ['Название', 'Текст/файл'],
                        rows: rows,
                        row_itemprops: row_itemprops
                    };
                    if (blockItemprop) blockData.itemprop = blockItemprop;
                    blocks.push(blockData);
                }
            });

            const existing = this.wizardData[step.id] || {};

            const sectionData = {
                title: existing.title || step.title,
                text: existing.text || '',
                content_blocks: blocks
            };

            if (step.id === 'education') {
                const programsEditor = document.querySelector('.education-programs-editor[data-step-id="' + step.id + '"]');
                if (programsEditor) {
                    const collectList = (listKind) => {
                        const listEl = programsEditor.querySelector('.education-programs-list[data-list="' + listKind + '"]');
                        if (!listEl) return [];
                        const rows = listEl.querySelectorAll('.education-program-row');
                        const arr = [];
                        rows.forEach(r => {
                            const name = (r.querySelector('.program-name') && r.querySelector('.program-name').value || '').trim();
                            const url = (r.querySelector('.program-url') && r.querySelector('.program-url').value || '').trim();
                            if (name || url) arr.push({ name: name || '', url: url || '' });
                        });
                        return arr;
                    };
                    sectionData.implemented_programs = collectList('implemented');
                    sectionData.adapted_programs = collectList('adapted');
                }
            }

            this.wizardData[step.id] = Object.assign({}, existing, { content_blocks: blocks });
            if (sectionData.implemented_programs) this.wizardData[step.id].implemented_programs = sectionData.implemented_programs;
            if (sectionData.adapted_programs) this.wizardData[step.id].adapted_programs = sectionData.adapted_programs;

            const formData = new FormData();
            formData.append('wizard_data', JSON.stringify({ [step.id]: sectionData }));
            formData.append('save_single', 'true');

            const module = step.module || 'info';
            const response = await fetch(`/${module}/wizard_save`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', 'Шаг сохранен');
            } else {
                this.showSaveStatus('error', 'Ошибка сохранения');
            }
        } catch (error) {
            console.error('Error saving sveden step:', error);
            this.showSaveStatus('error', 'Ошибка сохранения');
        }
    }

    /**
     * Генерация представления «Режим тегов» для табличных блоков.
     * Для каждого блока: один itemprop блока + по одному полю itemprop на каждую строку таблицы.
     */
    generateSvedenTagsHTML(step) {
        const data = this.wizardData[step.id] || {};
        const blocks = Array.isArray(data.content_blocks) ? data.content_blocks : [];

        let html = `
            <h2>${step.title} — режим тегов</h2>
            <p class="wizard-tags-description">
                Укажите значение атрибута <code>itemprop</code> для каждого блока и для каждой строки в таблице. Допускаются только латинские буквы, цифры и подчёркивание.
            </p>
        `;

        if (!blocks.length) {
            html += `
                <p class="wizard-tags-empty">
                    Сначала создайте и сохраните блоки в обычном режиме, затем настройте теги.
                </p>
            `;
            return html;
        }

        html += '<div class="wizard-tags-list">';

        blocks.forEach((block, blockIndex) => {
            const blockTitle = (block && block.title) ? String(block.title).trim() : '';
            const blockItemprop = (block && block.itemprop) ? String(block.itemprop) : '';
            const blockType = (block && block.type) || 'table';

            // Для блоков персон определяем главный тег автоматически
            let displayBlockItemprop = blockItemprop;
            if (blockType === 'person') {
                const personType = (block && block.person_type) ? String(block.person_type) : 'rucovodstvo';
                const mainItempropMap = {
                    'rucovodstvo': 'rucovodstvo',
                    'rucovodstvoZam': 'rucovodstvoZam',
                    'rucovodstvoFil': 'rucovodstvoFil'
                };
                const defaultMainItemprop = mainItempropMap[personType] || 'rucovodstvo';
                // Если тег не установлен, используем значение по умолчанию
                if (!blockItemprop) {
                    displayBlockItemprop = defaultMainItemprop;
                }
            }

            html += `
                <div class="wizard-tags-block-group" data-block-type="${blockType}">
                    <div class="wizard-tags-block-group-title">Блок ${blockIndex + 1}${blockTitle ? ': ' + this.escapeHtml(blockTitle) : ''}${blockType === 'person' ? ' (персона)' : ''}</div>
                    <div class="wizard-tags-row wizard-tags-row-block">
                        <div class="wizard-tags-block-info">
                            <span class="wizard-tags-block-title">itemprop блока</span>
                        </div>
                        <div class="wizard-tags-input-wrapper">
                            <input type="text"
                                   class="wizard-input sveden-tag-input sveden-tag-input-block"
                                   data-block-index="${blockIndex}"
                                   data-row-index="-1"
                                   value="${this.escapeHtml(displayBlockItemprop)}"
                                   placeholder="itemprop блока">
                        </div>
                    </div>
            `;

            if (blockType === 'person') {
                const personType = (block && block.person_type) ? String(block.person_type) : 'rucovodstvo';
                const branchName = (block && block.branch_name) ? String(block.branch_name) : '';
                
                const mapping = (block && block.person_itemprop_mapping) && typeof block.person_itemprop_mapping === 'object' ? block.person_itemprop_mapping : {};
                const fields = ['name', 'position', 'photo', 'email', 'phone', 'description', 'experience', 'education', 'professional_retraining', 'awards', 'courses'];
                const labels = { name: 'ФИО', position: 'Должность', photo: 'Фото', email: 'E-mail', phone: 'Телефон', description: 'Краткое описание', experience: 'Пед. стаж', education: 'Образование', professional_retraining: 'Переподготовка', awards: 'Награды и звания', courses: 'Курсы повышения квалификации' };
                
                // Если тип - руководитель филиала, добавляем поле для названия филиала
                if (personType === 'rucovodstvoFil') {
                    html += `
                    <div class="wizard-tags-row wizard-tags-row-person-field">
                        <div class="wizard-tags-block-info">
                            <span class="wizard-tags-block-title">Название филиала</span>
                        </div>
                        <div class="wizard-tags-input-wrapper">
                            <input type="text"
                                   class="wizard-input sveden-tag-input sveden-tag-input-branch-name"
                                   data-block-index="${blockIndex}"
                                   value="${this.escapeHtml(branchName)}"
                                   placeholder="Название филиала">
                        </div>
                    </div>
                `;
                }
                
                fields.forEach(field => {
                    const val = mapping[field] !== undefined ? String(mapping[field]) : '';
                    html += `
                    <div class="wizard-tags-row wizard-tags-row-person-field">
                        <div class="wizard-tags-block-info">
                            <span class="wizard-tags-block-title">${labels[field] || field}</span>
                        </div>
                        <div class="wizard-tags-input-wrapper">
                            <input type="text"
                                   class="wizard-input sveden-tag-input sveden-tag-input-person-field"
                                   data-block-index="${blockIndex}"
                                   data-person-field="${field}"
                                   value="${this.escapeHtml(val)}"
                                   placeholder="itemprop">
                        </div>
                    </div>
                `;
                });
            } else {
                const rows = Array.isArray(block && block.rows) ? block.rows : [];
                const rowItemprops = Array.isArray(block && block.row_itemprops) ? block.row_itemprops : [];
                rows.forEach((row, rowIndex) => {
                    const left = Array.isArray(row) ? (row[0] || '') : '';
                    const right = Array.isArray(row) ? (row[1] || '') : '';
                    
                    // Определяем, что показывать для leftFull
                    let leftFull = '';
                    if (left) {
                        const leftFileInfo = this.parseSvedenFileValue(String(left));
                        leftFull = leftFileInfo.isFile ? this.escapeHtml(leftFileInfo.displayName) : this.escapeHtml(String(left));
                    } else if (right) {
                        // Проверяем, есть ли файлы в right
                        const rightFiles = this.parseSvedenFilesValue(String(right));
                        if (rightFiles.length > 0) {
                            // Если есть файлы, показываем названия всех файлов через запятую
                            const fileNames = rightFiles.map(f => f.displayName).join(', ');
                            leftFull = this.escapeHtml(fileNames);
                        } else {
                            // Если это не файлы, показываем как есть
                            leftFull = this.escapeHtml(String(right));
                        }
                    } else {
                        leftFull = `Строка ${rowIndex + 1}`;
                    }
                    
                    // Определяем, что показывать для preview
                    let preview = '—';
                    const previewValue = left || right;
                    if (previewValue) {
                        // Проверяем, есть ли файлы
                        const files = this.parseSvedenFilesValue(String(previewValue));
                        let displayText = '';
                        if (files.length > 0) {
                            // Если есть файлы, показываем названия файлов
                            displayText = files.map(f => f.displayName).join(', ');
                        } else {
                            // Если это не файлы, показываем как есть
                            displayText = String(previewValue);
                        }
                        preview = this.escapeHtml(displayText.substring(0, 40)) + (displayText.length > 40 ? '…' : '');
                    }
                    
                    const rowItemprop = (rowItemprops[rowIndex] !== undefined) ? String(rowItemprops[rowIndex]) : '';

                    html += `
                    <div class="wizard-tags-row wizard-tags-row-row" data-block-index="${blockIndex}" data-row-index="${rowIndex}">
                        <div class="wizard-tags-block-info">
                            <span class="wizard-tags-block-title">${leftFull}</span>
                            <div class="wizard-tags-block-subtitle">${preview}</div>
                        </div>
                        <div class="wizard-tags-input-wrapper">
                            <input type="text"
                                   class="wizard-input sveden-tag-input sveden-tag-input-row"
                                   data-block-index="${blockIndex}"
                                   data-row-index="${rowIndex}"
                                   value="${this.escapeHtml(rowItemprop)}"
                                   placeholder="itemprop строки">
                        </div>
                        <div class="wizard-tags-row-controls">
                            <button type="button" 
                                    class="wizard-tags-row-move-btn" 
                                    onclick="wizardManager.moveSvedenRow(${blockIndex}, ${rowIndex}, -1)"
                                    ${rowIndex === 0 ? 'disabled' : ''}
                                    title="Вверх">↑</button>
                            <button type="button" 
                                    class="wizard-tags-row-move-btn" 
                                    onclick="wizardManager.moveSvedenRow(${blockIndex}, ${rowIndex}, 1)"
                                    ${rowIndex === rows.length - 1 ? 'disabled' : ''}
                                    title="Вниз">↓</button>
                        </div>
                    </div>
                `;
                });
            }

            html += '</div>';
        });

        html += '</div>';
        return html;
    }

    /**
     * Переключение режима мастера (обычный / режим тегов).
     */
    setMode(mode) {
        this.mode = mode === 'tags' ? 'tags' : 'normal';

        const normalBtn = document.getElementById('wizardModeNormal');
        const tagsBtn = document.getElementById('wizardModeTags');
        if (normalBtn && tagsBtn) {
            normalBtn.classList.toggle('wizard-mode-btn-active', this.mode === 'normal');
            tagsBtn.classList.toggle('wizard-mode-btn-active', this.mode === 'tags');
        }

        const step = this.wizardSteps[this.currentStep];
        if (step) {
            this.loadStepContent(step);
        }
    }

    /**
     * Сохранение только тегов (itemprop) для табличных блоков в режиме «Режим тегов».
     * Сохраняет itemprop блока и row_itemprops для каждой строки.
     */
    async saveSvedenTags(step) {
        try {
            const contentContainer = document.getElementById('wizardStepContent');
            if (!contentContainer) return;

            const existing = this.wizardData[step.id] || {};
            const blocks = Array.isArray(existing.content_blocks) ? existing.content_blocks.slice() : [];
            const tagRegex = /^[A-Za-z0-9_]+$/;
            let hasInvalid = false;

            const allInputs = contentContainer.querySelectorAll('.sveden-tag-input');
            allInputs.forEach(input => {
                const raw = (input.value || '').trim();
                if (raw && !tagRegex.test(raw)) {
                    hasInvalid = true;
                    input.classList.add('wizard-input-error');
                } else {
                    input.classList.remove('wizard-input-error');
                }
            });

            if (hasInvalid) {
                this.showSaveStatus('error', 'itemprop: только латиница, цифры и _');
                return;
            }

            contentContainer.querySelectorAll('.sveden-tag-input-block').forEach(input => {
                const blockIndex = parseInt(input.getAttribute('data-block-index'), 10);
                if (Number.isNaN(blockIndex) || !blocks[blockIndex]) return;
                const raw = (input.value || '').trim();
                if (raw) {
                    blocks[blockIndex].itemprop = raw;
                } else {
                    delete blocks[blockIndex].itemprop;
                }
            });

            blocks.forEach((block, blockIndex) => {
                if (block.type === 'person') return;
                
                const blockRows = contentContainer.querySelectorAll(`.wizard-tags-row-row[data-block-index="${blockIndex}"]`);
                const reorderedRows = [];
                const reorderedItemprops = [];
                
                blockRows.forEach((rowEl) => {
                    const rowIndex = parseInt(rowEl.getAttribute('data-row-index'), 10);
                    if (Number.isNaN(rowIndex) || rowIndex < 0) return;
                    
                    const input = rowEl.querySelector('.sveden-tag-input-row');
                    if (!input) return;
                    
                    const originalRow = Array.isArray(block.rows) && block.rows[rowIndex] ? block.rows[rowIndex] : null;
                    const raw = (input.value || '').trim();
                    
                    if (originalRow) {
                        reorderedRows.push(originalRow);
                        reorderedItemprops.push(raw);
                    }
                });
                
                if (reorderedRows.length > 0) {
                    blocks[blockIndex].rows = reorderedRows;
                    blocks[blockIndex].row_itemprops = reorderedItemprops;
                }
            });

            contentContainer.querySelectorAll('.sveden-tag-input-person-field').forEach(input => {
                const blockIndex = parseInt(input.getAttribute('data-block-index'), 10);
                const field = input.getAttribute('data-person-field');
                if (Number.isNaN(blockIndex) || !blocks[blockIndex] || !field) return;
                const block = blocks[blockIndex];
                if (block.type !== 'person') return;
                if (!block.person_itemprop_mapping || typeof block.person_itemprop_mapping !== 'object') {
                    block.person_itemprop_mapping = {};
                }
                const raw = (input.value || '').trim();
                block.person_itemprop_mapping[field] = raw;
            });

            // Сохраняем название филиала для блоков персон типа руководитель филиала
            contentContainer.querySelectorAll('.sveden-tag-input-branch-name').forEach(input => {
                const blockIndex = parseInt(input.getAttribute('data-block-index'), 10);
                if (Number.isNaN(blockIndex) || !blocks[blockIndex]) return;
                const block = blocks[blockIndex];
                if (block.type !== 'person' || block.person_type !== 'rucovodstvoFil') return;
                const raw = (input.value || '').trim();
                block.branch_name = raw;
            });

            // Автоматически устанавливаем правильный главный тег для блоков персон
            blocks.forEach((block, blockIndex) => {
                if (block.type === 'person' && block.person_type) {
                    const mainItempropMap = {
                        'rucovodstvo': 'rucovodstvo',
                        'rucovodstvoZam': 'rucovodstvoZam',
                        'rucovodstvoFil': 'rucovodstvoFil'
                    };
                    const defaultMainItemprop = mainItempropMap[block.person_type] || 'rucovodstvo';
                    const blockInput = contentContainer.querySelector(`.sveden-tag-input-block[data-block-index="${blockIndex}"]`);
                    if (blockInput) {
                        const currentValue = (blockInput.value || '').trim();
                        // Если тег не установлен или не соответствует типу, устанавливаем правильный
                        if (!currentValue || currentValue !== defaultMainItemprop) {
                            block.itemprop = defaultMainItemprop;
                            blockInput.value = defaultMainItemprop;
                        } else {
                            block.itemprop = currentValue;
                        }
                    } else {
                        // Если input не найден, просто устанавливаем значение
                        block.itemprop = defaultMainItemprop;
                    }
                }
            });

            const sectionData = {
                title: existing.title || step.title,
                text: existing.text || '',
                content_blocks: blocks
            };

            this.wizardData[step.id] = Object.assign({}, existing, { content_blocks: blocks });

            const formData = new FormData();
            formData.append('wizard_data', JSON.stringify({ [step.id]: sectionData }));
            formData.append('save_single', 'true');

            const module = step.module || 'info';
            const response = await fetch(`/${module}/wizard_save`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', 'Теги сохранены');
            } else {
                this.showSaveStatus('error', 'Ошибка сохранения тегов');
            }
        } catch (error) {
            console.error('Error saving sveden tags:', error);
            this.showSaveStatus('error', 'Ошибка сохранения тегов');
        }
    }

    /**
     * Перемещение строки вверх или вниз в режиме тегов.
     */
    moveSvedenRow(blockIndex, rowIndex, direction) {
        const step = this.wizardSteps[this.currentStep];
        if (!step) return;

        const data = this.wizardData[step.id] || {};
        const blocks = Array.isArray(data.content_blocks) ? data.content_blocks : [];
        const block = blocks[blockIndex];
        if (!block || block.type === 'person') return;

        const rows = Array.isArray(block.rows) ? block.rows : [];
        const rowItemprops = Array.isArray(block.row_itemprops) ? block.row_itemprops : [];

        const newIndex = rowIndex + direction;
        if (newIndex < 0 || newIndex >= rows.length) return;

        const tempRow = rows[rowIndex];
        const tempItemprop = rowItemprops[rowIndex] || '';

        rows[rowIndex] = rows[newIndex];
        rows[newIndex] = tempRow;

        if (rowItemprops.length > rowIndex) {
            rowItemprops[rowIndex] = rowItemprops[newIndex] || '';
        }
        if (rowItemprops.length > newIndex) {
            rowItemprops[newIndex] = tempItemprop;
        }

        block.rows = rows;
        block.row_itemprops = rowItemprops;

        this.wizardData[step.id] = Object.assign({}, data, { content_blocks: blocks });
        this.loadStepContent(step);
    }

    /**
     * Добавление/удаление строк и блоков для табличных разделов.
     */
    addSvedenBlock(stepId) {
        const container = document.querySelector(`.wizard-blocks-list[data-step-id="${stepId}"]`);
        if (!container) return;

        const step = this.wizardSteps.find(s => s.id === stepId);
        const index = container.querySelectorAll('.wizard-block-item').length;
        const block = this.createEmptySvedenBlock(index);
        const html = this.generateSvedenBlockItemHTML(step, block, index);
        container.insertAdjacentHTML('beforeend', html);
    }

    addSvedenPersonBlock(stepId) {
        const container = document.querySelector(`.wizard-blocks-list[data-step-id="${stepId}"]`);
        if (!container) return;

        const step = this.wizardSteps.find(s => s.id === stepId);
        const index = container.querySelectorAll('.wizard-block-item').length;
        const block = this.createEmptySvedenPersonBlock(index);
        const html = this.generateSvedenPersonBlockHTML(step, block, index);
        container.insertAdjacentHTML('beforeend', html);
    }

    addSvedenPerson(btn) {
        const card = btn && btn.closest && btn.closest('.wizard-block-item');
        if (!card) return;
        const stepId = card.getAttribute('data-step-id');
        const blockIndex = parseInt(card.getAttribute('data-block-index'), 10);
        if (Number.isNaN(blockIndex)) return;
        const step = this.wizardSteps.find(s => s.id === stepId);
        if (!step) return;
        const list = card.querySelector('.sveden-person-list');
        if (!list) return;
        const newIndex = list.querySelectorAll('.sveden-person-item').length;
        const mapping = this.getPersonItempropMappingFromCard(card);
        const itemHtml = this.generateSvedenPersonItemHTML(step.id, blockIndex, newIndex, {}, mapping);
        list.insertAdjacentHTML('beforeend', itemHtml);
    }

    getPersonItempropMappingFromCard(card) {
        const mapping = {};
        const firstItem = card && card.querySelector('.sveden-person-item');
        if (!firstItem) return mapping;
        firstItem.querySelectorAll('.sveden-itemprop-input').forEach(input => {
            const field = input.getAttribute('data-person-field');
            if (field) mapping[field] = (input.value || '').trim();
        });
        return mapping;
    }

    removeSvedenPerson(btn) {
        const item = btn && btn.closest && btn.closest('.sveden-person-item');
        if (item) item.remove();
    }

    removeSvedenBlock(stepId, blockIndex) {
        const container = document.querySelector(`.wizard-blocks-list[data-step-id="${stepId}"]`);
        if (!container) return;

        const blockEl = container.querySelector(`.wizard-block-item[data-block-index="${blockIndex}"]`);
        if (blockEl) {
            blockEl.remove();
        }

        const blocks = Array.from(container.querySelectorAll('.wizard-block-item'));
        blocks.forEach((el, idx) => {
            const oldIndex = parseInt(el.getAttribute('data-block-index'), 10);
            el.setAttribute('data-block-index', String(idx));
            const numEl = el.querySelector('.wizard-block-num');
            if (numEl) numEl.textContent = `Блок ${idx + 1}`;
            if (el.getAttribute('data-block-type') === 'table') {
                const addRowBtn = el.querySelector('.sveden-add-row-btn');
                if (addRowBtn) addRowBtn.setAttribute('onclick', `wizardManager.addSvedenRow('${stepId}', ${idx})`);
                const rows = Array.from(el.querySelectorAll('.wizard-block-row'));
                rows.forEach((rowEl, rowIdx) => {
                    rowEl.setAttribute('data-block-index', String(idx));
                    rowEl.setAttribute('data-row-index', String(rowIdx));
                    const removeBtn = rowEl.querySelector('td.cell-actions button.btn-danger');
                    if (removeBtn) removeBtn.setAttribute('onclick', `wizardManager.removeSvedenRow('${stepId}', ${idx}, ${rowIdx})`);
                    const uploadBtn = rowEl.querySelector('.sveden-upload-btn');
                    if (uploadBtn) uploadBtn.setAttribute('onclick', `wizardManager.uploadSvedenCellFiles('${stepId}', ${idx}, ${rowIdx})`);
                });
            } else if (el.getAttribute('data-block-type') === 'person') {
                if (oldIndex !== idx) this.updatePersonBlockIds(el, stepId, oldIndex, idx);
                const removeBtn = el.querySelector('.wizard-block-actions .btn-danger');
                if (removeBtn) removeBtn.setAttribute('onclick', `wizardManager.removeSvedenBlock('${stepId}', ${idx})`);
            }
        });
    }

    updatePersonBlockIds(card, stepId, oldIndex, newIndex) {
        const list = card.querySelector('.sveden-person-list');
        if (list) list.id = `person-list-${stepId}-${newIndex}`;
        card.querySelectorAll('[id]').forEach(el => {
            const id = el.getAttribute('id');
            if (!id) return;
            const re = new RegExp('-' + oldIndex + '(?=-|$)');
            if (re.test(id)) el.id = id.replace(re, '-' + newIndex);
        });
    }

    addSvedenRow(stepId, blockIndex) {
        const container = document.querySelector(`.wizard-blocks-list[data-step-id="${stepId}"]`);
        if (!container) return;

        const blockEl = container.querySelector(`.wizard-block-item[data-block-index="${blockIndex}"]`);
        if (!blockEl) return;

        const tbody = blockEl.querySelector('tbody');
        if (!tbody) return;

        const newIndex = tbody.querySelectorAll('.wizard-block-row').length;
        const rowHtml = this.generateSvedenRowHTML(stepId, blockIndex, newIndex, '', '', []);
        tbody.insertAdjacentHTML('beforeend', rowHtml);
        const newRow = tbody.querySelector(`.wizard-block-row[data-row-index="${newIndex}"]`);
        if (newRow) {
            const valueInput = newRow.querySelector('.wizard-block-row-value');
            if (valueInput) {
                valueInput.style.height = '60px';
                valueInput.addEventListener('input', () => {
                    this.updateSvedenCellFilesDisplay(newRow);
                });
            }
            const subRows = newRow.querySelectorAll('.sveden-subrow');
            subRows.forEach(subRowEl => {
                const subValueInput = subRowEl.querySelector('.wizard-block-subrow-value');
                if (subValueInput) {
                    subValueInput.style.height = '60px';
                    subValueInput.addEventListener('input', () => {
                        this.updateSvedenSubRowFilesDisplay(subRowEl);
                    });
                }
            });
        }
    }

    resizeSvedenTextarea(textarea) {
        if (!textarea || textarea.nodeName !== 'TEXTAREA') return;
        textarea.style.height = 'auto';
        const minHeight = 60;
        const maxHeight = 200;
        const h = Math.min(maxHeight, Math.max(minHeight, textarea.scrollHeight));
        textarea.style.height = h + 'px';
    }

    attachSvedenTextareaAutoResize(container) {
        if (!container) return;
        const list = container.classList && container.classList.contains('wizard-block-row-value')
            ? [container]
            : Array.from(container.querySelectorAll('.wizard-block-row-value'));
        list.forEach(ta => {
            if (ta.nodeName !== 'TEXTAREA') return;
            ta.removeEventListener('input', ta._svedenResizeHandler);
            ta._svedenResizeHandler = () => this.resizeSvedenTextarea(ta);
            ta.addEventListener('input', ta._svedenResizeHandler);
            this.resizeSvedenTextarea(ta);
        });
    }

    removeSvedenRow(stepId, blockIndex, rowIndex) {
        const container = document.querySelector(`.wizard-blocks-list[data-step-id="${stepId}"]`);
        if (!container) return;

        const blockEl = container.querySelector(`.wizard-block-item[data-block-index="${blockIndex}"]`);
        if (!blockEl) return;

        const rowEl = blockEl.querySelector(`.wizard-block-row[data-row-index="${rowIndex}"]`);
        if (rowEl) {
            rowEl.remove();
        }

        // Переиндексация строк блока
        const rows = Array.from(blockEl.querySelectorAll('.wizard-block-row'));
        rows.forEach((el, idx) => {
            el.setAttribute('data-row-index', String(idx));
            const removeBtn = el.querySelector('td.cell-actions button.btn-danger');
            if (removeBtn) removeBtn.setAttribute('onclick', `wizardManager.removeSvedenRow('${stepId}', ${blockIndex}, ${idx})`);
            const uploadBtn = el.querySelector('.sveden-upload-btn');
            if (uploadBtn) uploadBtn.setAttribute('onclick', `wizardManager.uploadSvedenCellFiles('${stepId}', ${blockIndex}, ${idx})`);
        });
    }

    /**
     * Загрузка файлов для ячейки "Текст/файл" в табличном блоке.
     * Поддерживает загрузку нескольких файлов.
     * Файлы сохраняются через стандартный /info/upload_file,
     * а в ячейку записываются URL с отображаемыми именами через запятую.
     */
    uploadSvedenCellFiles(stepId, blockIndex, rowIndex) {
        const step = this.wizardSteps.find(s => s.id === stepId);
        if (!step) return;

        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.style.display = 'none';

        input.addEventListener('change', async (event) => {
            try {
                const files = event.target.files;
                if (!files || files.length === 0) return;

                const rowSelector = `.wizard-block-row[data-step-id="${stepId}"][data-block-index="${blockIndex}"][data-row-index="${rowIndex}"]`;
                const rowEl = document.querySelector(rowSelector);
                if (!rowEl) return;

                const valueInput = rowEl.querySelector('.wizard-block-row-value');
                const existingFiles = valueInput ? this.parseSvedenFilesValue(valueInput.value) : [];
                const newFiles = [];

                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('section', step.endpoint || 'main');
                    formData.append('field_name', 'sveden_table_cell');

                    const response = await fetch('/info/upload_file', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    if (result && result.success) {
                        const displayName = result.display_name || result.original_name || result.filename || file.name;
                        const url = result.url || '';
                        newFiles.push({ displayName, fullValue: url ? `${url}|${displayName}` : displayName });
                    }
                }

                if (newFiles.length > 0) {
                    const allFiles = [...existingFiles, ...newFiles];
                    const filesString = allFiles.map(f => f.fullValue).join(',');
                    if (valueInput) {
                        valueInput.value = filesString;
                        this.updateSvedenCellFilesDisplay(rowEl);
                    }
                    this.showSaveStatus('success', `Загружено файлов: ${newFiles.length}`);
                } else {
                    this.showSaveStatus('error', 'Ошибка загрузки файлов');
                }
            } catch (error) {
                console.error('Error uploading sveden cell files:', error);
                this.showSaveStatus('error', 'Ошибка загрузки файлов');
            } finally {
                document.body.removeChild(input);
            }
        });

        document.body.appendChild(input);
        input.click();
    }

    addSvedenSubRow(stepId, blockIndex, rowIndex) {
        const rowEl = document.querySelector(`.wizard-block-row[data-step-id="${stepId}"][data-block-index="${blockIndex}"][data-row-index="${rowIndex}"]`);
        if (!rowEl) return;

        const subRowsContainer = rowEl.querySelector('.sveden-subrows-container');
        if (!subRowsContainer) return;

        const existingSubRows = Array.from(subRowsContainer.children).filter(child => child.classList.contains('sveden-subrow'));
        const subRowIndex = existingSubRows.length;
        const html = this.generateSvedenSubRowHTML(stepId, blockIndex, rowIndex, subRowIndex, '', '');
        
        const addBtn = subRowsContainer.querySelector('.sveden-add-subrow-btn');
        if (addBtn && addBtn.parentElement === subRowsContainer) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newSubRowElement = tempDiv.firstElementChild;
            if (newSubRowElement) {
                subRowsContainer.insertBefore(newSubRowElement, addBtn);
            }
        } else {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newSubRowElement = tempDiv.firstElementChild;
            if (newSubRowElement) {
                subRowsContainer.appendChild(newSubRowElement);
            }
        }
        
        const newSubRow = subRowsContainer.querySelector(`.sveden-subrow[data-subrow-index="${subRowIndex}"]`);
        if (newSubRow) {
            const subValueInput = newSubRow.querySelector('.wizard-block-subrow-value');
            if (subValueInput) {
                subValueInput.style.height = '60px';
                subValueInput.addEventListener('input', () => {
                    this.updateSvedenSubRowFilesDisplay(newSubRow);
                });
            }
        }
    }

    removeSvedenSubRow(stepId, blockIndex, rowIndex, subRowIndex) {
        const subRowEl = document.querySelector(`.sveden-subrow[data-step-id="${stepId}"][data-block-index="${blockIndex}"][data-row-index="${rowIndex}"][data-subrow-index="${subRowIndex}"]`);
        if (subRowEl) {
            subRowEl.remove();
        }
    }

    uploadSvedenSubRowFiles(stepId, blockIndex, rowIndex, subRowIndex) {
        const step = this.wizardSteps.find(s => s.id === stepId);
        if (!step) return;

        const input = document.createElement('input');
        input.type = 'file';
        input.multiple = true;
        input.style.display = 'none';

        input.addEventListener('change', async (event) => {
            try {
                const files = event.target.files;
                if (!files || files.length === 0) return;

                const subRowSelector = `.sveden-subrow[data-step-id="${stepId}"][data-block-index="${blockIndex}"][data-row-index="${rowIndex}"][data-subrow-index="${subRowIndex}"]`;
                const subRowEl = document.querySelector(subRowSelector);
                if (!subRowEl) return;

                const valueInput = subRowEl.querySelector('.wizard-block-subrow-value');
                const existingFiles = valueInput ? this.parseSvedenFilesValue(valueInput.value) : [];
                const newFiles = [];

                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('section', step.endpoint || 'main');
                    formData.append('field_name', 'sveden_table_cell');

                    const response = await fetch('/info/upload_file', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    if (result && result.success) {
                        const displayName = result.display_name || result.original_name || result.filename || file.name;
                        const url = result.url || '';
                        newFiles.push({ displayName, fullValue: url ? `${url}|${displayName}` : displayName });
                    }
                }

                if (newFiles.length > 0) {
                    const allFiles = [...existingFiles, ...newFiles];
                    const filesString = allFiles.map(f => f.fullValue).join(',');
                    if (valueInput) {
                        valueInput.value = filesString;
                        this.updateSvedenSubRowFilesDisplay(subRowEl);
                    }
                    this.showSaveStatus('success', `Загружено файлов: ${newFiles.length}`);
                } else {
                    this.showSaveStatus('error', 'Ошибка загрузки файлов');
                }
            } catch (error) {
                console.error('Error uploading sveden subrow files:', error);
                this.showSaveStatus('error', 'Ошибка загрузки файлов');
            } finally {
                document.body.removeChild(input);
            }
        });

        document.body.appendChild(input);
        input.click();
    }

    removeSvedenSubRowFile(stepId, blockIndex, rowIndex, subRowIndex, fileIndex) {
        const subRowEl = document.querySelector(`.sveden-subrow[data-step-id="${stepId}"][data-block-index="${blockIndex}"][data-row-index="${rowIndex}"][data-subrow-index="${subRowIndex}"]`);
        if (!subRowEl) return;

        const valueInput = subRowEl.querySelector('.wizard-block-subrow-value');
        if (!valueInput) return;
        
        const filesList = this.parseSvedenFilesValue(valueInput.value);
        if (fileIndex !== undefined && fileIndex >= 0 && fileIndex < filesList.length) {
            filesList.splice(fileIndex, 1);
            const filesString = filesList.map(f => f.fullValue).join(',');
            valueInput.value = filesString;
            this.updateSvedenSubRowFilesDisplay(subRowEl);
            this.showSaveStatus('success', 'Файл удалён из подстроки');
        }
    }

    updateSvedenSubRowFilesDisplay(subRowEl) {
        const wrap = subRowEl.querySelector('.sveden-cell-value-wrap');
        const valueInput = subRowEl.querySelector('.wizard-block-subrow-value');
        if (!wrap || !valueInput) return;
        const filesList = this.parseSvedenFilesValue(valueInput.value);
        let filesDisplay = wrap.querySelector('.sveden-files-list');
        
        if (filesList.length > 0) {
            if (!filesDisplay) {
                filesDisplay = document.createElement('div');
                filesDisplay.className = 'sveden-files-list';
                filesDisplay.setAttribute('data-step-id', subRowEl.getAttribute('data-step-id'));
                filesDisplay.setAttribute('data-block-index', subRowEl.getAttribute('data-block-index'));
                filesDisplay.setAttribute('data-row-index', subRowEl.getAttribute('data-row-index'));
                filesDisplay.setAttribute('data-subrow-index', subRowEl.getAttribute('data-subrow-index'));
                filesDisplay.style.marginBottom = '4px';
                wrap.insertBefore(filesDisplay, valueInput);
            }
            
            filesDisplay.innerHTML = filesList.map((fileInfo, fileIndex) => {
                const stepId = subRowEl.getAttribute('data-step-id');
                const blockIndex = subRowEl.getAttribute('data-block-index');
                const rowIndex = subRowEl.getAttribute('data-row-index');
                const subRowIndex = subRowEl.getAttribute('data-subrow-index');
                return `
                    <div class="sveden-file-item" data-file-index="${fileIndex}" style="display: flex; align-items: center; gap: 8px; padding: 4px 8px; margin-bottom: 2px; background: #f8fafc; border-radius: 6px; border: 1px solid #e5e7eb;">
                        <span class="sveden-file-name" style="flex: 1;">${this.escapeHtml(fileInfo.displayName)}</span>
                        <button type="button" class="btn btn-xs btn-danger sveden-file-remove-btn" onclick="wizardManager.removeSvedenSubRowFile('${stepId}', ${blockIndex}, ${rowIndex}, ${subRowIndex}, ${fileIndex})">×</button>
                    </div>
                `;
            }).join('');
            filesDisplay.style.display = '';
            valueInput.style.display = 'none';
            valueInput.classList.add('sveden-value-hidden');
        } else {
            if (filesDisplay) filesDisplay.style.display = 'none';
            valueInput.style.display = '';
            valueInput.classList.remove('sveden-value-hidden');
        }
    }

    updateSvedenCellFilesDisplay(rowEl) {
        const wrap = rowEl.querySelector('.sveden-cell-value-wrap');
        const valueInput = rowEl.querySelector('.wizard-block-row-value');
        if (!wrap || !valueInput) return;
        const filesList = this.parseSvedenFilesValue(valueInput.value);
        let filesDisplay = wrap.querySelector('.sveden-files-list');
        
        if (filesList.length > 0) {
            if (!filesDisplay) {
                filesDisplay = document.createElement('div');
                filesDisplay.className = 'sveden-files-list';
                filesDisplay.setAttribute('data-step-id', rowEl.getAttribute('data-step-id'));
                filesDisplay.setAttribute('data-block-index', rowEl.getAttribute('data-block-index'));
                filesDisplay.setAttribute('data-row-index', rowEl.getAttribute('data-row-index'));
                filesDisplay.style.marginBottom = '4px';
                wrap.insertBefore(filesDisplay, valueInput);
            }
            
            filesDisplay.innerHTML = filesList.map((fileInfo, fileIndex) => {
                const stepId = rowEl.getAttribute('data-step-id');
                const blockIndex = rowEl.getAttribute('data-block-index');
                const rowIndex = rowEl.getAttribute('data-row-index');
                return `
                    <div class="sveden-file-item" data-file-index="${fileIndex}" style="display: flex; align-items: center; gap: 8px; padding: 4px 8px; margin-bottom: 2px; background: #f8fafc; border-radius: 6px; border: 1px solid #e5e7eb;">
                        <span class="sveden-file-name" style="flex: 1;">${this.escapeHtml(fileInfo.displayName)}</span>
                        <button type="button" class="btn btn-xs btn-danger sveden-file-remove-btn" onclick="wizardManager.removeSvedenCellFile('${stepId}', ${blockIndex}, ${rowIndex}, ${fileIndex})">×</button>
                    </div>
                `;
            }).join('');
            filesDisplay.style.display = '';
            valueInput.style.display = 'none';
            valueInput.classList.add('sveden-value-hidden');
        } else {
            if (filesDisplay) filesDisplay.style.display = 'none';
            valueInput.style.display = '';
            valueInput.classList.remove('sveden-value-hidden');
        }
    }

    removeSvedenCellFile(stepId, blockIndex, rowIndex, fileIndex) {
        const rowSelector = `.wizard-block-row[data-step-id="${stepId}"][data-block-index="${blockIndex}"][data-row-index="${rowIndex}"]`;
        const rowEl = document.querySelector(rowSelector);
        if (!rowEl) return;
        const valueInput = rowEl.querySelector('.wizard-block-row-value');
        if (!valueInput) return;
        
        const filesList = this.parseSvedenFilesValue(valueInput.value);
        if (fileIndex !== undefined && fileIndex >= 0 && fileIndex < filesList.length) {
            filesList.splice(fileIndex, 1);
            const filesString = filesList.map(f => f.fullValue).join(',');
            valueInput.value = filesString;
            this.updateSvedenCellFilesDisplay(rowEl);
            this.showSaveStatus('success', 'Файл удалён из пункта');
        }
    }


    uploadSvedenPersonPhoto(stepId, blockIndex, personIndex) {
        const step = this.wizardSteps.find(s => s.id === stepId);
        if (!step) return;

        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.style.display = 'none';

        input.addEventListener('change', async (event) => {
            try {
                const file = event.target.files && event.target.files[0];
                if (!file) return;

                const formData = new FormData();
                formData.append('file', file);
                formData.append('section', step.endpoint || 'main');
                formData.append('field_name', 'person_photo');

                const response = await fetch('/info/upload_file', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (!result || !result.success) {
                    this.showSaveStatus('error', (result && result.error) || 'Ошибка загрузки файла');
                    return;
                }

                const displayName = result.display_name || result.original_name || result.filename || file.name;
                const url = result.url || '';
                const value = url ? `${url}|${displayName}` : displayName;

                const card = document.querySelector(`.wizard-block-item[data-step-id="${stepId}"][data-block-index="${blockIndex}"][data-block-type="person"]`);
                if (!card) return;
                const personItems = card.querySelectorAll('.sveden-person-item');
                const personEl = personItems[personIndex];
                if (!personEl) return;
                const photoInput = personEl.querySelector('.person-photo');
                if (photoInput) {
                    photoInput.value = value;
                    this.updateSvedenPersonPhotoDisplay(personEl);
                }
                this.showSaveStatus('success', 'Фото загружено');
            } catch (error) {
                console.error('Error uploading person photo:', error);
                this.showSaveStatus('error', 'Ошибка загрузки файла');
            } finally {
                document.body.removeChild(input);
            }
        });

        document.body.appendChild(input);
        input.click();
    }

    updateSvedenPersonPhotoDisplay(personItemEl) {
        const wrap = personItemEl.querySelector('.sveden-person-photo-wrap');
        const photoInput = personItemEl.querySelector('.person-photo');
        const uploadBtn = personItemEl.querySelector('.sveden-person-photo-upload-btn');
        if (!wrap || !photoInput) return;
        const fileInfo = this.parseSvedenFileValue(photoInput.value);
        let fileBlock = wrap.querySelector('.sveden-person-photo-file');
        if (fileInfo.isFile) {
            if (!fileBlock) {
                fileBlock = document.createElement('div');
                fileBlock.className = 'sveden-person-photo-file';
                fileBlock.innerHTML = '<span class="sveden-file-name"></span><button type="button" class="btn btn-xs btn-danger" onclick="wizardManager.removeSvedenPersonPhoto(this)">Удалить фото</button>';
                wrap.insertBefore(fileBlock, photoInput);
            }
            fileBlock.querySelector('.sveden-file-name').textContent = fileInfo.displayName;
            fileBlock.style.display = '';
            if (uploadBtn) uploadBtn.style.display = 'none';
        } else {
            if (fileBlock) fileBlock.style.display = 'none';
            if (uploadBtn) uploadBtn.style.display = '';
        }
    }

    removeSvedenPersonPhoto(btn) {
        const personItem = btn && btn.closest && btn.closest('.sveden-person-item');
        if (!personItem) return;
        const photoInput = personItem.querySelector('.person-photo');
        if (photoInput) {
            photoInput.value = '';
            this.updateSvedenPersonPhotoDisplay(personItem);
        }
        this.showSaveStatus('success', 'Фото удалено');
    }

    async saveAllData() {
        try {
            const formData = new FormData();
            formData.append('wizard_data', JSON.stringify(this.wizardData));
            formData.append('save_single', 'false');
            
            // Сохраняем через модуль info, который обрабатывает все разделы
            const response = await fetch('/info/wizard_save', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.success) {
                this.showSaveStatus('success', 'Все данные сохранены');
                setTimeout(() => {
                    this.closeWizard();
                }, 2000);
            } else {
                this.showSaveStatus('error', 'Ошибка сохранения');
            }
        } catch (error) {
            console.error('Error saving all data:', error);
            this.showSaveStatus('error', 'Ошибка сохранения');
        }
    }

    closeWizard() {
        const modal = this.modalElement || document.getElementById('wizardModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
}

// Экспортируем функцию toggleInputType для глобального доступа (до инициализации)
window.toggleInputType = (fieldName, type) => {
    if (window.wizardManager && typeof window.wizardManager.toggleInputType === 'function') {
        return window.wizardManager.toggleInputType(fieldName, type);
    } else {
        console.warn('toggleInputType: wizardManager не инициализирован');
    }
};

// Инициализация мастера заполнения
let wizardManager;
document.addEventListener('DOMContentLoaded', () => {
    wizardManager = new WizardManager();
    // Экспорт для глобального доступа
    window.wizardManager = wizardManager;
    
    console.log('WizardManager инициализирован');
});
