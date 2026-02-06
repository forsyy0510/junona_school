// Мастер заполнения для бокового меню - только sidebar разделы
class SidebarWizardManager {
    constructor() {
        this.currentStep = 0;
        this.wizardData = {};
        this.wizardSteps = [];
        // Какие разделы раскрыты в списке шагов мастера (accordion)
        this.expandedStepEndpoints = new Set();
        this.init();
    }

    ensureDynamicStep(endpoint, title) {
        const existingIndex = this.wizardSteps.findIndex(s => s.endpoint === endpoint);
        if (existingIndex >= 0) return existingIndex;
        const dynamicStep = {
            id: endpoint,
            title: title || endpoint.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            icon: '🧩',
            endpoint: endpoint,
            module: 'sidebar',
            content_blocks: true,
            fields: [
                { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: false },
                { name: 'images', label: 'Изображения', type: 'images', required: false },
                { name: 'documents', label: 'Документы', type: 'documents', required: false }
            ]
        };
        this.wizardSteps.push(dynamicStep);
        return this.wizardSteps.length - 1;
    }

    async init() {
        await this.loadWizardSteps();
        await this.loadWizardData();
        this.setupEventListeners();
    }

    async loadWizardSteps() {
        // Загружаем только sidebar разделы
        this.wizardSteps = [
            {
                id: 'appeals',
                title: 'Обращения граждан',
                icon: '📝',
                endpoint: 'appeals',
                module: 'sidebar',
                content_blocks: true,
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false },
                    { name: 'images', label: 'Изображения', type: 'images', required: false }
                ]
            },
            {
                id: 'anti-corruption',
                title: 'Противодействие коррупции',
                icon: '🛡️',
                endpoint: 'anti-corruption',
                module: 'sidebar',
                content_blocks: true,
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false },
                    { name: 'images', label: 'Изображения', type: 'images', required: false }
                ]
            },
            {
                // Основной раздел "Питание" (официальный /sveden/food хранится как endpoint='food')
                id: 'food',
                title: 'Питание',
                icon: '🍽️',
                endpoint: 'food',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'menu_document', label: 'Меню (документ)', type: 'file_or_text', required: false },
                    { name: 'documents', label: 'Дополнительные документы', type: 'documents', required: false },
                    { name: 'images', label: 'Изображения', type: 'images', required: false }
                ]
            },
            {
                id: 'nutrition-dishes-archive',
                title: 'Ежедневное меню',
                icon: '📦',
                endpoint: 'nutrition-dishes-archive',
                module: 'sidebar',
                parent: 'food',
                static: true, // Статический подраздел, нельзя удалить
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: false },
                    { name: 'images', label: 'Изображения', type: 'images', required: false },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'admission-grade1',
                title: 'Прием в 1 класс',
                icon: '📚',
                endpoint: 'admission-grade1',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'rules_document', label: 'Правила приема (документ)', type: 'file_or_text', required: false },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'admission-grade10',
                title: 'Прием в 10 класс',
                icon: '📚',
                endpoint: 'admission-grade10',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'rules_document', label: 'Правила приема (документ)', type: 'file_or_text', required: false },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'history',
                title: 'История',
                icon: '📜',
                endpoint: 'history',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'images', label: 'Исторические фотографии', type: 'images', required: false }
                ]
            },
            {
                id: 'ushakov-festival',
                title: 'Ушаковский Фестиваль',
                icon: '🎭',
                endpoint: 'ushakov-festival',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'images', label: 'Фотографии фестиваля', type: 'images', required: false },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'schedule',
                title: 'Расписание',
                icon: '📅',
                endpoint: 'schedule',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'schedule_document', label: 'Расписание (документ)', type: 'file_or_text', required: false },
                    { name: 'documents', label: 'Дополнительные документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'for-parents',
                title: 'Родителям',
                icon: '👨‍👩‍👧',
                endpoint: 'for-parents',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'gia-ege-oge',
                title: 'ГИА (ЕГЭ и ОГЭ)',
                icon: '📊',
                endpoint: 'gia-ege-oge',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы по ГИА', type: 'documents', required: false }
                ]
            },
            {
                id: 'additional-info',
                title: 'Дополнительные сведения',
                icon: '📋',
                endpoint: 'additional-info',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false },
                    { name: 'images', label: 'Изображения', type: 'images', required: false }
                ]
            },
            {
                id: 'class-leadership-payment',
                title: 'Выплата денежного вознаграждения за классное руководство',
                icon: '💰',
                endpoint: 'class-leadership-payment',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'electronic-environment',
                title: 'Электронная образовательная среда',
                icon: '💻',
                endpoint: 'electronic-environment',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'useful-info',
                title: 'Полезная информация',
                icon: 'ℹ️',
                endpoint: 'useful-info',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'information-security',
                title: 'Информационная безопасность',
                icon: '🔒',
                endpoint: 'information-security',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'road-safety',
                title: 'Дорожная безопасность',
                icon: '🚦',
                endpoint: 'road-safety',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false },
                    { name: 'images', label: 'Изображения', type: 'images', required: false }
                ]
            },
            {
                id: 'targeted-training',
                title: 'Целевое обучение',
                icon: '🎯',
                endpoint: 'targeted-training',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'social-order-implementation',
                title: 'Реализация социального заказа по дополнительным образовательным программам',
                icon: '📚',
                endpoint: 'social-order-implementation',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'recreation-organization',
                title: 'Организация отдыха',
                icon: '🏕️',
                endpoint: 'recreation-organization',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'images', label: 'Фотографии', type: 'images', required: false },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'parent-education',
                title: 'Родительский всеобуч',
                icon: '👨‍🏫',
                endpoint: 'parent-education',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'memos',
                title: 'Памятки',
                icon: '📝',
                endpoint: 'memos',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'cbr-fraud-prevention',
                title: 'Материалы Центрального Банка Российской Федерации по противодействию мошенничеству',
                icon: '🏦',
                endpoint: 'cbr-fraud-prevention',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'financial-literacy',
                title: 'Финансовая грамотность',
                icon: '💳',
                endpoint: 'financial-literacy',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'parental-control',
                title: 'Родительский контроль',
                icon: '👨‍👩‍👧‍👦',
                endpoint: 'parental-control',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'inclusive-education',
                title: 'Инклюзивное образование',
                icon: '♿',
                endpoint: 'inclusive-education',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'anti-terrorism',
                title: 'Противодействие терроризму',
                icon: '🛡️',
                endpoint: 'anti-terrorism',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'orkse',
                title: 'ОРКСЭ',
                icon: '📿',
                endpoint: 'orkse',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            },
            {
                id: 'sanitary-shield',
                title: 'Санитарный щит страны - безопасность для здоровья',
                icon: '🏥',
                endpoint: 'sanitary-shield',
                module: 'sidebar',
                fields: [
                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: true },
                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                ]
            }
        ];
        
        // Загружаем подразделы из базы данных
        try {
            const response = await fetch('/sidebar/get_all_sections');
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.sections) {
                    // Проставляем метаданные из БД (parent/order/show_in_menu) и добавляем отсутствующие шаги
                    const metaByEndpoint = new Map();
                    result.sections.forEach(section => {
                        try {
                            metaByEndpoint.set(section.endpoint, {
                                parent: section.parent || null,
                                menu_parent: section.menu_parent || null,
                                order: section.order || 0,
                                show_in_menu: section.show_in_menu
                            });
                        } catch (e) { /* ignore */ }
                    });

                    // Проставляем parent/order на уже существующих (статических) шагах
                    this.wizardSteps.forEach(step => {
                        const meta = metaByEndpoint.get(step.endpoint);
                        if (!meta) return;
                        if (!step.parent && meta.parent) {
                            let p = meta.parent;
                            if (typeof p === 'string' && p.startsWith('/sidebar/')) p = p.replace('/sidebar/', '');
                            step.parent = p;
                        }
                        if (!step.menu_parent && meta.menu_parent) {
                            let mp = meta.menu_parent;
                            if (typeof mp === 'string' && mp.startsWith('/sidebar/')) mp = mp.replace('/sidebar/', '');
                            step.menu_parent = mp;
                        }
                        step._order = meta.order || 0;
                    });

                    // Добавляем подразделы, которых нет в статическом списке
                    result.sections.forEach(section => {
                        const exists = this.wizardSteps.some(step => step.endpoint === section.endpoint);
                        // Не добавляем, если шаг уже существует (включая статические)
                        if (!exists) {
                            // Нормализуем parent
                            let parent = section.parent;
                            if (parent && parent.startsWith('/sidebar/')) {
                                parent = parent.replace('/sidebar/', '');
                            }
                            
                            // Добавляем подраздел в список шагов
                            this.wizardSteps.push({
                                id: section.endpoint,
                                title: section.title || section.endpoint.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                                icon: '🧩',
                                endpoint: section.endpoint,
                                module: 'sidebar',
                                parent: parent,
                                _order: section.order || 0,
                                static: false, // Динамически добавленные подразделы не статические
                                fields: [
                                    { name: 'title', label: 'Заголовок страницы', type: 'text', required: true },
                                    { name: 'content', label: 'Содержимое страницы', type: 'textarea', required: false },
                                    { name: 'images', label: 'Изображения', type: 'images', required: false },
                                    { name: 'documents', label: 'Документы', type: 'documents', required: false }
                                ]
                            });
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error loading subsections:', error);
        }

        // Добавляем чекбокс "показывать в меню" для всех шагов, если его нет
        try {
            this.wizardSteps.forEach(step => {
                if (!step || !Array.isArray(step.fields)) return;
                const hasShow = step.fields.some(f => f && f.name === 'show_in_menu' && f.type === 'checkbox');
                if (hasShow) return;
                step.fields.unshift({ name: 'show_in_menu', label: 'Показывать в боковом меню', type: 'checkbox', required: false });
            });
        } catch (e) { /* ignore */ }

        // Добавляем селект "Где показывать" (menu_parent) — только для управления структурой меню
        try {
            this.wizardSteps.forEach(step => {
                if (!step || !Array.isArray(step.fields)) return;
                const hasMenuParent = step.fields.some(f => f && f.name === 'menu_parent' && f.type === 'select');
                if (hasMenuParent) return;
                step.fields.splice(1, 0, { name: 'menu_parent', label: 'Разместить в боковом меню', type: 'select', required: false });
            });
        } catch (e) { /* ignore */ }

        // Гарантируем, что у каждого шага есть поле загрузки изображений "в сам раздел"
        // (не в content_blocks). Если поле уже есть — не трогаем (сохраняем кастомные labels).
        try {
            this.wizardSteps.forEach(step => {
                if (!step || !Array.isArray(step.fields)) return;
                const hasImages = step.fields.some(f => f && f.type === 'images' && f.name === 'images');
                if (hasImages) return;

                // Вставляем после documents, если оно есть, иначе в конец.
                const idx = step.fields.findIndex(f => f && f.name === 'documents' && f.type === 'documents');
                const imagesField = { name: 'images', label: 'Изображения', type: 'images', required: false };
                if (idx >= 0) step.fields.splice(idx + 1, 0, imagesField);
                else step.fields.push(imagesField);
            });
        } catch (e) {
            // no-op
        }

        // Сортируем шаги по parent + order, чтобы порядок в мастере совпадал с меню
        try {
            const steps = this.wizardSteps.slice();
            const byParent = new Map();
            const getParent = (s) => {
                let p = (s && s.parent) ? s.parent : null;
                if (typeof p === 'string' && p.startsWith('/sidebar/')) p = p.replace('/sidebar/', '');
                p = (typeof p === 'string') ? p.trim() : p;
                return p || null;
            };
            steps.forEach(s => {
                byParent.set(getParent(s), (byParent.get(getParent(s)) || []).concat([s]));
            });
            const sortKey = (s) => {
                const raw = (s && s._order) ? s._order : 0;
                let o = 0;
                try { o = parseInt(raw, 10) || 0; } catch (e) { o = 0; }
                const title = (s && s.title ? s.title : '').toLowerCase();
                return [o === 0 ? 10 ** 9 : o, title, (s && s.endpoint) ? s.endpoint : ''];
            };
            const sortArr = (arr) => arr.sort((a, b) => {
                const ka = sortKey(a);
                const kb = sortKey(b);
                for (let i = 0; i < ka.length; i++) {
                    if (ka[i] < kb[i]) return -1;
                    if (ka[i] > kb[i]) return 1;
                }
                return 0;
            });
            const out = [];
            const walk = (parent = null, seen = new Set()) => {
                const kids = sortArr((byParent.get(parent) || []).slice());
                kids.forEach(k => {
                    if (!k || !k.endpoint || seen.has(k.endpoint)) return;
                    seen.add(k.endpoint);
                    out.push(k);
                    walk(k.endpoint, seen);
                });
            };
            walk(null);
            steps.forEach(s => {
                if (s && s.endpoint && !out.some(x => x.endpoint === s.endpoint)) out.push(s);
            });
            this.wizardSteps = out;
        } catch (e) { /* ignore */ }
    }

    async loadWizardData() {
        const loadPromises = this.wizardSteps.map(step => {
            const url = `/sidebar/section/${step.endpoint}`;
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
                        const normalizeBlocksRecursive = (blocksArray) => {
                            const normalizedBlocks = [];
                            for (const block of blocksArray) {
                                if (typeof block === 'object' && block !== null && !Array.isArray(block)) {
                                    if (block.content_blocks && Array.isArray(block.content_blocks)) {
                                        normalizedBlocks.push(...normalizeBlocksRecursive(block.content_blocks));
                                    } else {
                                        const normalized = {};
                                        for (const key in block) {
                                            if (key !== 'content_blocks') normalized[key] = block[key];
                                        }
                                        normalizedBlocks.push(normalized);
                                    }
                                } else if (Array.isArray(block)) {
                                    normalizedBlocks.push(...normalizeBlocksRecursive(block));
                                } else {
                                    normalizedBlocks.push(block);
                                }
                            }
                            return normalizedBlocks;
                        };
                        let content_blocks = data.section.content_blocks || [];
                        if (Array.isArray(content_blocks)) {
                            content_blocks = normalizeBlocksRecursive(content_blocks);
                        }
                        this.wizardData[step.id] = {
                            title: data.section.title || '',
                            text: data.section.text || '',
                            content_blocks: content_blocks
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
        const prevBtn = document.getElementById('sidebar-wizard-prev');
        const nextBtn = document.getElementById('sidebar-wizard-next');
        const saveBtn = document.getElementById('sidebar-wizard-save');
        const addBtn = document.getElementById('sidebar-wizard-add-subsection-main');
        if (prevBtn) prevBtn.onclick = () => this.go(-1);
        if (nextBtn) nextBtn.onclick = () => this.go(1);
        if (saveBtn) saveBtn.onclick = () => this.saveCurrent();
        if (addBtn) addBtn.onclick = () => this.createSubsection();
    }

    async open() {
        window.IS_SIDEBAR_WIZARD = true;
        // Перезагружаем шаги, чтобы получить актуальные подразделы
        await this.loadWizardSteps();
        if (Object.keys(this.wizardData).length === 0) {
            await this.loadWizardData();
        } else {
            // Обновляем данные для новых шагов
            await this.loadWizardData();
        }
        // Синхронизируем глобальные структуры, которые использует модуль блоков контента
        window.wizardSteps = this.wizardSteps;
        window.wizardData = this.wizardData;
        this.renderSteps();
        this.renderCurrentStep();
        // Обновляем обработчики кнопок внутри модала (на случай пересоздания DOM)
        this.setupEventListeners();
        const modal = document.getElementById('sidebarWizardModal');
        if (modal) {
            modal.style.display = 'flex';
            document.body.classList.add('modal-open');
        }
    }

    close() {
        const modal = document.getElementById('sidebarWizardModal');
        if (modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
        window.IS_SIDEBAR_WIZARD = false;
        // Возвращать глобальные wizardSteps/wizardData не обязательно, но чтобы не влиять на основной мастер — очищаем
        // Оставляем экспортированные функции доступными
        // window.wizardSteps = undefined; // не трогаем, чтобы основной мастер при открытии сам инициализировал свои шаги
        // window.wizardData = undefined;
    }

    renderSteps() {
        const stepsEl = document.getElementById('sidebar-wizard-steps');
        if (!stepsEl) return;
        stepsEl.innerHTML = '';
        
        // Группируем шаги по уровням вложенности
        const rootSteps = [];
        const stepParentMap = new Map(); // endpoint -> parent endpoint
        const childrenByParent = new Map(); // parent endpoint -> child steps
        
        const normalizeParent = (p) => {
            if (!p) return null;
            if (typeof p === 'string') {
                let v = p.trim();
                if (v.startsWith('/sidebar/')) v = v.replace('/sidebar/', '');
                return v || null;
            }
            return null;
        };

        // Определяем родительские связи (для списка шагов используем menu_parent, если задан)
        this.wizardSteps.forEach(step => {
            const data = this.wizardData[step.id] || {};
            let parent = normalizeParent(data.menu_parent || step.menu_parent);
            if (!parent) parent = normalizeParent(data.parent || step.parent);
            stepParentMap.set(step.endpoint, parent);
            if (!parent) {
                rootSteps.push(step);
            }
        });

        // Строим список детей для каждого parent
        this.wizardSteps.forEach(step => {
            const parent = stepParentMap.get(step.endpoint) || null;
            if (!parent) return;
            childrenByParent.set(parent, (childrenByParent.get(parent) || []).concat([step]));
        });
        
        // Счетчики для иерархической нумерации на каждом уровне
        const levelCounters = {};
        
        // Рекурсивная функция для отрисовки шага и его детей
        const renderStepRecursive = (step, level = 0, numberPath = []) => {
            // Определяем номер для текущего уровня
            const levelKey = numberPath.join('.');
            if (!levelCounters[levelKey]) {
                levelCounters[levelKey] = 0;
            }
            levelCounters[levelKey]++;
            
            // Формируем иерархический номер
            const currentNumber = [...numberPath, levelCounters[levelKey]];
            const numberString = currentNumber.join('.');
            
            const stepContainer = document.createElement('div');
            stepContainer.style.display = 'flex';
            stepContainer.style.alignItems = 'center';
            stepContainer.style.width = '100%';
            stepContainer.style.gap = '8px';

            // Кнопка раскрытия/сворачивания для шагов с детьми
            const childStepsForToggle = (childrenByParent.get(step.endpoint) || []).slice();
            const hasChildren = childStepsForToggle.length > 0;
            if (hasChildren) {
                const toggleBtn = document.createElement('button');
                const isExpanded = this.expandedStepEndpoints.has(step.endpoint);
                toggleBtn.innerHTML = isExpanded ? '▼' : '▶';
                toggleBtn.title = isExpanded ? 'Свернуть подразделы' : 'Показать подразделы';
                toggleBtn.style.cssText = 'background: transparent; color: #374151; border: 1px solid #e5e7eb; border-radius: 6px; padding: 2px 6px; cursor: pointer; font-size: 12px; flex-shrink: 0;';
                toggleBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (this.expandedStepEndpoints.has(step.endpoint)) {
                        this.expandedStepEndpoints.delete(step.endpoint);
                    } else {
                        this.expandedStepEndpoints.add(step.endpoint);
                    }
                    this.renderSteps();
                };
                stepContainer.appendChild(toggleBtn);
            } else {
                // spacer for alignment
                const spacer = document.createElement('div');
                spacer.style.width = '26px';
                spacer.style.flexShrink = '0';
                stepContainer.appendChild(spacer);
            }
            
            const btn = document.createElement('button');
            btn.className = 'wizard-step';
            btn.style.display = 'block';
            btn.style.flex = '1';
            btn.style.textAlign = 'left';
            btn.style.paddingLeft = `${12 + level * 20}px`;
            if (level > 0) {
                btn.style.fontSize = '0.9rem';
                btn.style.opacity = '0.9';
            }
            const stepIndex = this.wizardSteps.findIndex(s => s.endpoint === step.endpoint);
            btn.innerText = `${numberString}. ${step.title}`;
            btn.onclick = () => {
                this.currentStep = stepIndex >= 0 ? stepIndex : 0;
                // Если это подраздел, гарантируем, что его родитель раскрыт
                const p = stepParentMap.get(step.endpoint);
                if (p) this.expandedStepEndpoints.add(p);
                this.renderCurrentStep();
                this.renderSteps();
            };
            stepContainer.appendChild(btn);

            // Кнопки изменения порядка (в пределах одного parent)
            const orderUpBtn = document.createElement('button');
            orderUpBtn.innerHTML = '▲';
            orderUpBtn.title = 'Поднять выше';
            orderUpBtn.style.cssText = 'background: #eef2ff; color: #1f2937; border: 1px solid #c7d2fe; border-radius: 4px; padding: 2px 6px; cursor: pointer; font-size: 12px; flex-shrink: 0;';
            orderUpBtn.onclick = async (e) => { e.stopPropagation(); await this.moveStep(step.endpoint, -1); };
            stepContainer.appendChild(orderUpBtn);

            const orderDownBtn = document.createElement('button');
            orderDownBtn.innerHTML = '▼';
            orderDownBtn.title = 'Опустить ниже';
            orderDownBtn.style.cssText = 'background: #eef2ff; color: #1f2937; border: 1px solid #c7d2fe; border-radius: 4px; padding: 2px 6px; cursor: pointer; font-size: 12px; flex-shrink: 0;';
            orderDownBtn.onclick = async (e) => { e.stopPropagation(); await this.moveStep(step.endpoint, +1); };
            stepContainer.appendChild(orderDownBtn);
            
            // Добавляем кнопку удаления для подразделов (не статических и не корневых)
            if (level > 0 && !step.static) {
                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '🗑️';
                deleteBtn.style.cssText = 'background: #ef4444; color: white; border: none; border-radius: 4px; padding: 4px 8px; cursor: pointer; font-size: 12px; flex-shrink: 0;';
                deleteBtn.title = 'Удалить подраздел';
                deleteBtn.onclick = async (e) => {
                    e.stopPropagation();
                    if (confirm(`Вы уверены, что хотите удалить подраздел "${step.title}"?`)) {
                        await this.deleteSubsection(step.endpoint);
                    }
                };
                stepContainer.appendChild(deleteBtn);
            }
            
            stepsEl.appendChild(stepContainer);
            
            // Дочерние шаги (показываем только если раскрыт родитель)
            const isExpanded = this.expandedStepEndpoints.has(step.endpoint);
            if (!isExpanded) return;

            const childSteps = (childrenByParent.get(step.endpoint) || []).slice();
            
            // Сортируем дочерние шаги для консистентного отображения
            childSteps.sort((a, b) => {
                const indexA = this.wizardSteps.findIndex(s => s.endpoint === a.endpoint);
                const indexB = this.wizardSteps.findIndex(s => s.endpoint === b.endpoint);
                return indexA - indexB;
            });
            
            childSteps.forEach(childStep => {
                renderStepRecursive(childStep, level + 1, currentNumber);
            });
        };
        
        // Сортируем корневые шаги для консистентного отображения
        rootSteps.sort((a, b) => {
            const indexA = this.wizardSteps.findIndex(s => s.endpoint === a.endpoint);
            const indexB = this.wizardSteps.findIndex(s => s.endpoint === b.endpoint);
            return indexA - indexB;
        });
        
        // Отрисовываем корневые шаги
        rootSteps.forEach(step => {
            renderStepRecursive(step, 0, []);
        });
        
        // Отрисовываем шаги без родителя, которые не были добавлены
        this.wizardSteps.forEach(step => {
            if (!rootSteps.includes(step) && !stepParentMap.get(step.endpoint)) {
                const stepIndex = this.wizardSteps.indexOf(step);
                const btn = document.createElement('button');
                btn.className = 'wizard-step';
                btn.style.display = 'block';
                btn.style.width = '100%';
                btn.style.textAlign = 'left';
                // Используем простую нумерацию для шагов без родителя
                const numberString = (stepIndex + 1).toString();
                btn.innerText = `${numberString}. ${step.title}`;
                btn.onclick = () => { this.currentStep = stepIndex; this.renderCurrentStep(); };
                stepsEl.appendChild(btn);
            }
        });
    }

    _getStepParent(step) {
        if (!step) return null;
        const data = this.wizardData[step.id] || {};
        let parent = data.menu_parent || step.menu_parent || data.parent || step.parent || null;
        if (typeof parent === 'string' && parent.startsWith('/sidebar/')) parent = parent.replace('/sidebar/', '');
        parent = (typeof parent === 'string') ? parent.trim() : parent;
        return parent || null;
    }

    // Для построения списка корневых пунктов (меню/accordion)
    _getStepParentForList(step) {
        return this._getStepParent(step);
    }

    async moveStep(endpoint, direction) {
        try {
            const stepIndex = this.wizardSteps.findIndex(s => s && s.endpoint === endpoint);
            if (stepIndex < 0) return;
            const step = this.wizardSteps[stepIndex];
            const parent = this._getStepParent(step);

            const siblings = this.wizardSteps
                .map((s, idx) => ({ s, idx }))
                .filter(x => x.s && x.s.endpoint && this._getStepParent(x.s) === parent);

            const pos = siblings.findIndex(x => x.s.endpoint === endpoint);
            if (pos < 0) return;
            const targetPos = pos + (direction < 0 ? -1 : 1);
            if (targetPos < 0 || targetPos >= siblings.length) return;

            const a = siblings[pos].idx;
            const b = siblings[targetPos].idx;
            const tmp = this.wizardSteps[a];
            this.wizardSteps[a] = this.wizardSteps[b];
            this.wizardSteps[b] = tmp;

            const ordered = this.wizardSteps
                .filter(s => s && s.endpoint && this._getStepParent(s) === parent)
                .map(s => s.endpoint);

            await fetch('/sidebar/reorder_sections', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ parent: parent, ordered_endpoints: ordered })
            }).then(r => r.json()).catch(() => null);

            this.renderSteps();
        } catch (e) {
            // ignore
        }
    }

    renderCurrentStep() {
        const step = this.wizardSteps[this.currentStep];
        const content = document.getElementById('sidebar-wizard-step-content');
        const prog = document.getElementById('sidebar-wizard-progress');
        const progText = document.getElementById('sidebar-wizard-progress-text');
        if (!step || !content) return;
        if (prog) prog.style.width = `${(this.currentStep+1)/this.wizardSteps.length*100}%`;
        if (progText) progText.textContent = `Шаг ${this.currentStep+1} из ${this.wizardSteps.length}`;
        const data = this.wizardData[step.id] || {};
        
        let fieldsHtml = '';
        
        // Рендерим поля из конфигурации step.fields
        step.fields.forEach(field => {
            const value = data[field.name] || '';
            const required = field.required ? 'required' : '';
            const icon = this.getFieldIcon(field.type);
            
            if (field.type === 'checkbox') {
                const checked = !!(value === true || value === '1' || value === 1 || (typeof value === 'string' && value.toLowerCase() === 'true'));
                fieldsHtml += `
                    <div class="wizard-field">
                        <label class="wizard-label" style="display:flex; align-items:center; gap:10px;">
                            <input type="checkbox" name="${field.name}" id="sidebar-${field.name}" ${checked ? 'checked' : ''} style="width:18px; height:18px;">
                            <span>${field.label}</span>
                        </label>
                    </div>
                `;
            } else if (field.type === 'text') {
                fieldsHtml += `
                    <div class="wizard-field">
                        <label class="wizard-label">
                            <i class="icon">${icon}</i> ${field.label}
                            ${field.required ? '<span class="required">*</span>' : ''}
                        </label>
                        <input type="text" name="${field.name}" class="wizard-input" id="sidebar-${field.name}" value="${value || (field.name === 'title' ? (data.title || '') : '')}" ${required}>
                    </div>
                `;
            } else if (field.type === 'select') {
                // menu_parent: управляет размещением в боковом меню (не влияет на "подразделы на странице")
                if (field.name === 'menu_parent') {
                    const currentShow = (data.show_in_menu === true || data.show_in_menu === '1' || data.show_in_menu === 1 || (typeof data.show_in_menu === 'string' && data.show_in_menu.toLowerCase() === 'true'));
                    const selected = (value || data.menu_parent || step.menu_parent || '').toString();

                    const roots = this.wizardSteps.filter(s => {
                        if (!s || !s.endpoint) return false;
                        if (s.endpoint === step.endpoint) return false;
                        // Только корневые пункты, чтобы не усложнять циклы/глубокую вложенность
                        return !this._getStepParentForList(s);
                    });

                    const optionsHtml = [
                        `<option value="" ${selected === '' ? 'selected' : ''}>Верхний уровень</option>`,
                        ...roots.map(r => `<option value="${r.endpoint}" ${selected === r.endpoint ? 'selected' : ''}>Под разделом: ${r.title || r.endpoint}</option>`),
                    ].join('');

                    fieldsHtml += `
                        <div class="wizard-field" style="${currentShow ? '' : 'opacity:0.55; pointer-events:none;'}">
                            <label class="wizard-label"><i class="icon">🧭</i> ${field.label}</label>
                            <select name="${field.name}" id="sidebar-${field.name}" class="wizard-input">
                                ${optionsHtml}
                            </select>
                            ${currentShow ? '' : '<div style="font-size:12px;color:#6b7280;margin-top:6px;">Включите “Показывать в боковом меню”, чтобы перемещать</div>'}
                        </div>
                    `;
                }
            } else if (field.type === 'textarea') {
                fieldsHtml += `
                    <div class="wizard-field">
                        <label class="wizard-label">
                            <i class="icon">${icon}</i> ${field.label}
                            ${field.required ? '<span class="required">*</span>' : ''}
                        </label>
                        <textarea name="${field.name}" class="wizard-input" rows="4" id="sidebar-${field.name}" ${required}>${value || (field.name === 'content' ? (data.content || '') : '')}</textarea>
                    </div>
                `;
            } else if (field.type === 'images') {
                fieldsHtml += this.generateImageFieldHTML(field, value, step.id);
            } else if (field.type === 'documents') {
                fieldsHtml += this.generateDocumentFieldHTML(field, value, step.id);
            }
        });
        
        // Блоки контента
        const blocks = data.content_blocks || [];
        let contentBlocksHtml = '';
        // Показываем блоки контента для всех шагов (они поддерживают content_blocks)
        if (typeof window.generateBlocksHtml === 'function') {
            let blocks = this.wizardData[step.id]?.content_blocks || [];
            
            // Рекурсивная функция для нормализации блоков
            const normalizeBlocksRecursive = (blocksArray) => {
                const normalizedBlocks = [];
                for (const block of blocksArray) {
                    if (typeof block === 'object' && block !== null && !Array.isArray(block)) {
                        // Проверяем, есть ли внутри блока content_blocks
                        if (block.content_blocks && Array.isArray(block.content_blocks)) {
                            // Если есть, добавляем только вложенные блоки, сам блок не добавляем
                            normalizedBlocks.push(...normalizeBlocksRecursive(block.content_blocks));
                        } else {
                            // Создаем новый объект без content_blocks
                            const normalized = {};
                            for (const key in block) {
                                if (key !== 'content_blocks') {
                                    normalized[key] = block[key];
                                }
                            }
                            normalizedBlocks.push(normalized);
                        }
                    } else if (Array.isArray(block)) {
                        // Если блок - это массив, рекурсивно обрабатываем его
                        normalizedBlocks.push(...normalizeBlocksRecursive(block));
                    } else {
                        normalizedBlocks.push(block);
                    }
                }
                return normalizedBlocks;
            };
            
            // Нормализуем структуру блоков - убираем вложенные content_blocks и плоские блоки
            if (Array.isArray(blocks)) {
                blocks = normalizeBlocksRecursive(blocks);
                // Обновляем данные
                if (!this.wizardData[step.id]) {
                    this.wizardData[step.id] = {};
                }
                this.wizardData[step.id].content_blocks = blocks;
            }
            
            contentBlocksHtml = `
                <div class="wizard-content-blocks">
                    <div class="wizard-blocks-header">
                        <h4><i class="icon">📋</i> Блоки контента</h4>
                        <button type="button" onclick="addContentBlock('${step.id}')" class="btn btn-primary btn-sm">
                            <i class="icon">➕</i> Добавить блок
                        </button>
                    </div>
                    <div class="wizard-blocks-list" id="blocks-${step.id}-${Date.now()}">
                        ${window.generateBlocksHtml(step.id, blocks)}
                    </div>
                </div>
            `;
        }
        
        // Проверяем, можно ли удалить раздел (не статический)
        // Статические разделы - это разделы до "food" включительно + "nutrition-dishes-archive"
        // Все разделы после "food" можно удалять
        const staticSections = [
            'appeals', 'anti-corruption', 'nutrition', 'food', 'nutrition-dishes-archive'
        ];
        
        // Определяем порядок разделов для проверки
        const sectionOrder = [
            'appeals', 'anti-corruption', 'nutrition', 'food', 'nutrition-dishes-archive',
            'admission-grade1', 'admission-grade10', 'history', 'ushakov-festival', 
            'schedule', 'for-parents', 'gia-ege-oge', 'additional-info', 
            'class-leadership-payment', 'electronic-environment', 'useful-info', 
            'information-security', 'road-safety', 'targeted-training', 
            'social-order-implementation', 'recreation-organization', 
            'parent-education', 'memos', 'cbr-fraud-prevention', 
            'financial-literacy', 'parental-control', 'inclusive-education', 
            'anti-terrorism', 'orkse', 'sanitary-shield'
        ];
        
        // Раздел можно удалить, если:
        // 1. Он не в списке статических разделов (до food включительно + nutrition-dishes-archive)
        // 2. И не имеет явного флага static: true
        // 3. И он идет после "food" в порядке разделов
        const isInStaticList = staticSections.includes(step.endpoint);
        const foodIndex = sectionOrder.indexOf('food');
        const currentIndex = sectionOrder.indexOf(step.endpoint);
        const isAfterFood = currentIndex > foodIndex || (currentIndex === -1 && !isInStaticList);
        const isStatic = step.static === true || (isInStaticList && !isAfterFood);
        const canDelete = !isStatic;
        
        // Отладочная информация (можно убрать после проверки)
        if (canDelete) {
            console.log('Кнопка удаления будет показана для раздела:', step.endpoint, step.title);
        } else {
            console.log('Кнопка удаления НЕ будет показана для раздела:', step.endpoint, step.title, 'isStatic:', isStatic);
        }
        
        const deleteButtonHtml = canDelete ? `
            <button onclick="sidebarWizardManager.deleteCurrentSection()" 
                    class="btn btn-danger sidebar-delete-section-btn" 
                    style="background: #ef4444 !important; color: white !important; border: none !important; padding: 8px 16px !important; border-radius: 6px !important; cursor: pointer !important; font-size: 14px !important; margin-left: auto !important; flex-shrink: 0 !important; display: inline-block !important; white-space: nowrap !important;">
                🗑️ Удалить раздел
            </button>
        ` : '';
        
        content.innerHTML = `
            <div class="wizard-step-header sidebar-wizard-header" style="display: flex !important; align-items: center !important; justify-content: space-between !important; gap: 16px !important; margin-bottom: 24px !important; text-align: left !important;">
                <div style="flex: 1; min-width: 0;">
                    <h3 style="text-align: left !important;"><i class="icon">${step.icon}</i> ${step.title}</h3>
                    <p style="text-align: left !important;">Заполните информацию для раздела "${step.title}"</p>
                </div>
                ${deleteButtonHtml}
            </div>
            
            <div class="wizard-form">
                ${fieldsHtml}
                ${contentBlocksHtml}
            </div>
        `;
        
        // Инициализация полей
        this.initializeStepFields(step);

        // Подключаем обработчики кнопок работы с блоками контента
        try {
            const container = document.getElementById('sidebar-wizard-step-content');
            if (container) {
                container.querySelectorAll('.edit-block-btn').forEach(btn => {
                    const stepId = btn.getAttribute('data-step-id') || step.id;
                    const blockIndex = parseInt(btn.getAttribute('data-block-index') || '0', 10);
                    btn.onclick = () => {
                        if (typeof window.editContentBlock === 'function') {
                            window.editContentBlock(stepId, blockIndex);
                        }
                    };
                });
                container.querySelectorAll('.remove-block-btn').forEach(btn => {
                    const stepId = btn.getAttribute('data-step-id') || step.id;
                    const blockIndex = parseInt(btn.getAttribute('data-block-index') || '0', 10);
                    btn.onclick = () => {
                        if (typeof window.removeContentBlock === 'function') {
                            window.removeContentBlock(stepId, blockIndex);
                        }
                    };
                });
                container.querySelectorAll('.move-block-up-btn').forEach(btn => {
                    const stepId = btn.getAttribute('data-step-id') || step.id;
                    const blockIndex = parseInt(btn.getAttribute('data-block-index') || '0', 10);
                    btn.onclick = () => {
                        if (typeof window.moveBlockUp === 'function') {
                            window.moveBlockUp(stepId, blockIndex);
                        }
                    };
                });
                container.querySelectorAll('.move-block-down-btn').forEach(btn => {
                    const stepId = btn.getAttribute('data-step-id') || step.id;
                    const blockIndex = parseInt(btn.getAttribute('data-block-index') || '0', 10);
                    btn.onclick = () => {
                        if (typeof window.moveBlockDown === 'function') {
                            window.moveBlockDown(stepId, blockIndex);
                        }
                    };
                });
            }
        } catch (e) {
            // no-op
        }
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
    
    generateImageFieldHTML(field, value, stepId) {
        return `
            <div class="wizard-field">
                <label class="wizard-label">
                    <i class="icon">🖼️</i> ${field.label}
                    ${field.required ? '<span class="required">*</span>' : ''}
                </label>
                <div class="file-upload-container" id="${field.name}_upload_container">
                    <div class="file-drop-zone" id="${field.name}_drop_zone" ondrop="sidebarWizardManager.handleImageDrop(event, '${field.name}')" ondragover="sidebarWizardManager.handleDragOver(event)" ondragleave="sidebarWizardManager.handleDragLeave(event)">
                        <div class="drop-zone-content">
                            <i class="icon">🖼️</i>
                            <p>Перетащите изображения сюда или <span class="file-select-link" onclick="document.getElementById('${field.name}_image_input').click()">выберите изображения</span></p>
                            <p class="file-types">Поддерживаются: JPG, JPEG, PNG, GIF</p>
                        </div>
                    </div>
                    <input type="file" id="${field.name}_image_input" name="${field.name}" accept="image/*" style="display: none;" onchange="sidebarWizardManager.handleImageSelect(event, '${field.name}')" multiple>
                    <div id="${field.name}_image_list" class="image-list"></div>
                </div>
            </div>
        `;
    }
    
    generateDocumentFieldHTML(field, value, stepId) {
        return `
            <div class="wizard-field">
                <label class="wizard-label">
                    <i class="icon">📄</i> ${field.label}
                    ${field.required ? '<span class="required">*</span>' : ''}
                </label>
                <div class="file-upload-container" id="${field.name}_upload_container">
                    <div class="file-drop-zone" id="${field.name}_drop_zone" ondrop="sidebarWizardManager.handleDocumentDrop(event, '${field.name}')" ondragover="sidebarWizardManager.handleDragOver(event)" ondragleave="sidebarWizardManager.handleDragLeave(event)">
                        <div class="drop-zone-content">
                            <i class="icon">📄</i>
                            <p>Перетащите документы сюда или <span class="file-select-link" onclick="document.getElementById('${field.name}_document_input').click()">выберите документы</span></p>
                            <p class="file-types">Поддерживаются: PDF, DOC, DOCX, TXT, ZIP, RAR, 7Z, TAR, GZ</p>
                        </div>
                    </div>
                    <input type="file" id="${field.name}_document_input" name="${field.name}" accept=".pdf,.doc,.docx,.txt,.zip,.rar,.7z,.tar,.gz,.tgz" style="display: none;" onchange="sidebarWizardManager.handleDocumentSelect(event, '${field.name}')" multiple>
                    <div id="${field.name}_document_list" class="document-list"></div>
                </div>
            </div>
        `;
    }
    
    initializeStepFields(step) {
        setTimeout(() => {
            step.fields.forEach(field => {
                if (field.type === 'images') {
                    // Проверяем, что элемент DOM существует перед загрузкой
                    const imageList = document.getElementById(`${field.name}_image_list`);
                    if (imageList) {
                        this.loadExistingImages(field.name, step.id);
                    } else {
                        // Если элемент еще не создан, пробуем еще раз через небольшую задержку
                        setTimeout(() => {
                            const retryList = document.getElementById(`${field.name}_image_list`);
                            if (retryList) {
                                this.loadExistingImages(field.name, step.id);
                            }
                        }, 200);
                    }
                } else if (field.type === 'documents') {
                    // Проверяем, что элемент DOM существует перед загрузкой
                    const documentList = document.getElementById(`${field.name}_document_list`);
                    if (documentList) {
                        this.loadExistingDocuments(field.name, step.id);
                    } else {
                        // Если элемент еще не создан, пробуем еще раз через небольшую задержку
                        setTimeout(() => {
                            const retryList = document.getElementById(`${field.name}_document_list`);
                            if (retryList) {
                                this.loadExistingDocuments(field.name, step.id);
                            }
                        }, 200);
                    }
                }
            });
        }, 200);
    }

    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.add('drag-over');
    }

    handleDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.remove('drag-over');
    }

    async handleImageDrop(event, fieldName) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.remove('drag-over');
        const files = Array.from(event.dataTransfer.files).filter(f => f.type.startsWith('image/'));
        if (files.length > 0) {
            await this.handleImageSelect({ target: { files } }, fieldName);
        }
    }

    async handleDocumentDrop(event, fieldName) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.remove('drag-over');
        const files = Array.from(event.dataTransfer.files);
        if (files.length > 0) {
            await this.handleDocumentSelect({ target: { files } }, fieldName);
        }
    }

    async handleImageSelect(event, fieldName) {
        const files = Array.from(event.target.files || []);
        if (files.length === 0) return;
        
        const step = this.wizardSteps[this.currentStep];
        if (!step) return;
        
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('section', step.endpoint);
            formData.append('field_name', fieldName);
            
            try {
                const res = await fetch('/sidebar/upload_file', { method: 'POST', body: formData });
                const result = await res.json();
                if (result.success) {
                    const displayName = result.original_name || result.original_filename || result.filename;
                    let url = result.url || `/sidebar/download_file/${step.endpoint}/${result.filename}`;
                    try { url = new URL(url, window.location.origin).pathname; } catch (e) { /* keep */ }
                    this.addImageToList(fieldName, displayName, url, result.id);

                    // Обновляем локальные данные шага, чтобы сохранение/переоткрытие не теряли список
                    try {
                        const stepData = this.wizardData[step.id] || (this.wizardData[step.id] = {});
                        const entry = `${url}|${displayName}`;
                        const prev = (typeof stepData[fieldName] === 'string' ? stepData[fieldName] : '').trim();
                        const items = prev ? prev.split(',').map(x => x.trim()).filter(Boolean) : [];
                        if (!items.includes(entry)) items.push(entry);
                        stepData[fieldName] = items.join(', ');
                    } catch (e) { /* ignore */ }
                } else {
                    if (window.errorHandler && window.errorHandler.showError) {
                        window.errorHandler.showError(result.error || 'Ошибка загрузки изображения', result.instructions || []);
                    }
                }
            } catch (e) {
                console.error('Ошибка загрузки изображения:', e);
                if (window.errorHandler && window.errorHandler.showError) {
                    window.errorHandler.showError('Ошибка загрузки изображения', ['Попробуйте снова', 'Проверьте соединение']);
                }
            }
        }
        try { event.target.value = ''; } catch (e) { /* ignore */ }
    }

    async handleDocumentSelect(event, fieldName) {
        const files = Array.from(event.target.files || []);
        if (files.length === 0) return;
        
        const step = this.wizardSteps[this.currentStep];
        if (!step) return;
        
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('section', step.endpoint);
            formData.append('field_name', fieldName);
            
            try {
                const res = await fetch('/sidebar/upload_file', { method: 'POST', body: formData });
                const result = await res.json();
                if (result.success) {
                    const displayName = result.original_name || result.original_filename || result.filename;
                    let url = result.url || `/sidebar/download_file/${step.endpoint}/${result.filename}`;
                    try { url = new URL(url, window.location.origin).pathname; } catch (e) { /* keep */ }
                    this.addDocumentToList(fieldName, displayName, url, result.id);

                    try {
                        const stepData = this.wizardData[step.id] || (this.wizardData[step.id] = {});
                        const entry = `${url}|${displayName}`;
                        const prev = (typeof stepData[fieldName] === 'string' ? stepData[fieldName] : '').trim();
                        const items = prev ? prev.split(',').map(x => x.trim()).filter(Boolean) : [];
                        if (!items.includes(entry)) items.push(entry);
                        stepData[fieldName] = items.join(', ');
                    } catch (e) { /* ignore */ }
                } else {
                    if (window.errorHandler && window.errorHandler.showError) {
                        window.errorHandler.showError(result.error || 'Ошибка загрузки документа', result.instructions || []);
                    }
                }
            } catch (e) {
                console.error('Ошибка загрузки документа:', e);
                if (window.errorHandler && window.errorHandler.showError) {
                    window.errorHandler.showError('Ошибка загрузки документа', ['Попробуйте снова', 'Проверьте соединение']);
                }
            }
        }
        try { event.target.value = ''; } catch (e) { /* ignore */ }
    }
    
    async loadExistingImages(fieldName, stepId) {
        const imageList = document.getElementById(`${fieldName}_image_list`);
        if (!imageList) {
            console.warn(`Элемент ${fieldName}_image_list не найден для загрузки изображений`);
            return;
        }
        
        const step = this.wizardSteps.find(s => s.id === stepId);
        if (!step) {
            console.warn(`Шаг ${stepId} не найден для загрузки изображений`);
            return;
        }
        
        try {
            imageList.innerHTML = '';

            // 1) Восстанавливаем из сохраненного form_data (без зависимости от БД)
            const stepData = this.wizardData[stepId] || {};
            const raw = (typeof stepData[fieldName] === 'string' ? stepData[fieldName] : '').trim();
            if (raw) {
                const entries = raw.split(',').map(x => x.trim()).filter(Boolean);
                entries.forEach(entry => {
                    const parts = entry.split('|');
                    const u = (parts[0] || '').trim();
                    const name = (parts[1] || '').trim() || (u ? u.split('/').pop() : '');
                    if (!u) return;
                    this.addImageToList(fieldName, name, u, null);
                });
                return;
            }

            // 2) Фолбэк: API (если БД доступна)
            const res = await fetch(`/sidebar/get_section_files/${step.endpoint}?field_name=${encodeURIComponent(fieldName)}`);
            const result = await res.json();
            if (result.success && Array.isArray(result.files)) {
                const imageFiles = result.files.filter(f => f.is_image);
                imageFiles.forEach(fileInfo => {
                    const displayName = fileInfo.original_filename || fileInfo.original_name || fileInfo.display_name || fileInfo.filename;
                    const url = fileInfo.url || `/sidebar/download_file/${step.endpoint}/${fileInfo.filename}`;
                    this.addImageToList(fieldName, displayName, url, fileInfo.id);
                });
            }
        } catch (e) {
            console.error('Ошибка загрузки изображений:', e);
        }
    }
    
    async loadExistingDocuments(fieldName, stepId) {
        const documentList = document.getElementById(`${fieldName}_document_list`);
        if (!documentList) {
            console.warn(`Элемент ${fieldName}_document_list не найден для загрузки документов`);
            return;
        }
        
        const step = this.wizardSteps.find(s => s.id === stepId);
        if (!step) {
            console.warn(`Шаг ${stepId} не найден для загрузки документов`);
            return;
        }
        
        try {
            documentList.innerHTML = '';

            const stepData = this.wizardData[stepId] || {};
            const raw = (typeof stepData[fieldName] === 'string' ? stepData[fieldName] : '').trim();
            if (raw) {
                const entries = raw.split(',').map(x => x.trim()).filter(Boolean);
                entries.forEach(entry => {
                    const parts = entry.split('|');
                    const u = (parts[0] || '').trim();
                    const name = (parts[1] || '').trim() || (u ? u.split('/').pop() : '');
                    if (!u) return;
                    this.addDocumentToList(fieldName, name, u, null);
                });
                return;
            }

            const res = await fetch(`/sidebar/get_section_files/${step.endpoint}?field_name=${encodeURIComponent(fieldName)}`);
            const result = await res.json();
            if (result.success && Array.isArray(result.files)) {
                const documentFiles = result.files.filter(f => !f.is_image);
                documentFiles.forEach(fileInfo => {
                    const displayName = fileInfo.original_filename || fileInfo.original_name || fileInfo.display_name || fileInfo.filename;
                    const url = fileInfo.url || `/sidebar/download_file/${step.endpoint}/${fileInfo.filename}`;
                    this.addDocumentToList(fieldName, displayName, url, fileInfo.id);
                });
            }
        } catch (e) {
            console.error('Ошибка загрузки документов:', e);
        }
    }

    async loadExistingFiles(sectionEndpoint, fieldName, isImages){
        try{
            const res = await fetch(`/sidebar/get_section_files/${sectionEndpoint}?field_name=${encodeURIComponent(fieldName)}`);
            const result = await res.json();
            if(result.success && Array.isArray(result.files)){
                result.files.forEach(fileInfo => {
                    if ((isImages && fileInfo.is_image) || (!isImages && !fileInfo.is_image)){
                        const displayName = fileInfo.original_filename || fileInfo.original_name || fileInfo.display_name || fileInfo.filename;
                        const url = fileInfo.url || `/sidebar/download_file/${sectionEndpoint}/${fileInfo.filename}`;
                        if(isImages){ this.addImageToList(fieldName, displayName, url, fileInfo.id); }
                        else { this.addDocumentToList(fieldName, displayName, url, fileInfo.id); }
                    }
                });
            }
        }catch(e){ /* silent */ }
    }

    addImageToList(fieldName, displayName, url, fileId){
        const list = document.getElementById(`${fieldName}_image_list`);
        if(!list) return;
        const item = document.createElement('div');
        item.className='file-item';
        item.style.display='flex';
        item.style.gap='8px';
        item.style.alignItems='center';
        item.style.padding='8px';
        item.style.border='1px solid #e5e7eb';
        item.style.borderRadius='6px';
        item.style.marginBottom='8px';
        item.style.minWidth = '0';
        const thumb = document.createElement('img');
        thumb.src=url;
        thumb.alt=displayName;
        thumb.style.width='64px';
        thumb.style.height='64px';
        thumb.style.objectFit='cover';
        thumb.style.border='1px solid #e5e7eb';
        thumb.style.borderRadius='6px';
        const link = document.createElement('a');
        link.href=url;
        link.target='_blank';
        link.textContent=displayName;
        link.style.flex='1';
        link.style.minWidth='0';
        link.style.textDecoration='none';
        link.style.color='#2563eb';
        // Prevent long filenames from pushing the delete button out of bounds
        link.style.whiteSpace='nowrap';
        link.style.overflow='hidden';
        link.style.textOverflow='ellipsis';
        const del = document.createElement('button');
        del.textContent='Удалить';
        del.className='btn btn-secondary btn-sm';
        del.style.flexShrink='0';
        del.onclick = () => this.removeImage(fieldName, url, fileId);
        item.appendChild(thumb);
        item.appendChild(link);
        item.appendChild(del);
        list.appendChild(item);
    }

    addDocumentToList(fieldName, displayName, url, fileId){
        const list = document.getElementById(`${fieldName}_document_list`);
        if(!list) return;
        const item = document.createElement('div');
        item.className='file-item';
        item.style.display='flex';
        item.style.gap='8px';
        item.style.alignItems='center';
        item.style.padding='8px';
        item.style.border='1px solid #e5e7eb';
        item.style.borderRadius='6px';
        item.style.marginBottom='8px';
        item.style.minWidth = '0';
        const icon = document.createElement('div');
        icon.textContent='📄';
        icon.style.fontSize='1.5rem';
        icon.style.flexShrink='0';
        const link = document.createElement('a');
        link.href=url;
        link.target='_blank';
        link.textContent=displayName;
        link.style.flex='1';
        link.style.minWidth='0';
        link.style.textDecoration='none';
        link.style.color='#2563eb';
        // Prevent long filenames from pushing the delete button out of bounds
        link.style.whiteSpace='nowrap';
        link.style.overflow='hidden';
        link.style.textOverflow='ellipsis';
        const del = document.createElement('button');
        del.textContent='Удалить';
        del.className='btn btn-secondary btn-sm';
        del.style.flexShrink='0';
        del.onclick = () => this.removeDocument(fieldName, url, fileId);
        item.appendChild(icon);
        item.appendChild(link);
        item.appendChild(del);
        list.appendChild(item);
    }
    
    async removeImage(fieldName, imageUrl, fileId) {
        const step = this.wizardSteps[this.currentStep];
        if (!step) return;
        
        try {
            const imageFilename = (() => {
                try {
                    const u = new URL(imageUrl, window.location.origin);
                    return decodeURIComponent((u.pathname.split('/').pop() || '').trim());
                } catch (e) {
                    try { return decodeURIComponent((imageUrl.split('/').pop() || '').trim()); } catch (_e) { return (imageUrl.split('/').pop() || '').trim(); }
                }
            })();
            const res = await fetch('/sidebar/delete_file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: imageFilename,
                    section: step.endpoint,
                    field_name: fieldName
                })
            });
            const result = await res.json();
            if (result.success) {
                const imageList = document.getElementById(`${fieldName}_image_list`);
                if (imageList) {
                    Array.from(imageList.children).forEach(ch => {
                        const a = ch.querySelector('a');
                        const hrefPath = a && a.href ? (new URL(a.href, window.location.origin).pathname) : '';
                        const targetPath = imageUrl ? (new URL(imageUrl, window.location.origin).pathname) : '';
                        if (hrefPath && targetPath && hrefPath === targetPath) {
                            ch.remove();
                        }
                    });
                }
            }
        } catch (e) {
            console.error('Ошибка удаления изображения:', e);
        }
    }
    
    async removeDocument(fieldName, documentUrl, fileId) {
        const step = this.wizardSteps[this.currentStep];
        if (!step) return;
        
        try {
            const documentFilename = (() => {
                try {
                    const u = new URL(documentUrl, window.location.origin);
                    return decodeURIComponent((u.pathname.split('/').pop() || '').trim());
                } catch (e) {
                    try { return decodeURIComponent((documentUrl.split('/').pop() || '').trim()); } catch (_e) { return (documentUrl.split('/').pop() || '').trim(); }
                }
            })();
            const res = await fetch('/sidebar/delete_file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: documentFilename,
                    section: step.endpoint,
                    field_name: fieldName
                })
            });
            const result = await res.json();
            if (result.success) {
                const documentList = document.getElementById(`${fieldName}_document_list`);
                if (documentList) {
                    Array.from(documentList.children).forEach(ch => {
                        const a = ch.querySelector('a');
                        const hrefPath = a && a.href ? (new URL(a.href, window.location.origin).pathname) : '';
                        const targetPath = documentUrl ? (new URL(documentUrl, window.location.origin).pathname) : '';
                        if (hrefPath && targetPath && hrefPath === targetPath) {
                            ch.remove();
                        }
                    });
                }
            }
        } catch (e) {
            console.error('Ошибка удаления документа:', e);
        }
    }

    async uploadFiles(files, fieldName){
        const step = this.wizardSteps[this.currentStep]; if(!step) return;
        const section = step.endpoint;
        const promises = Array.from(files).map(async (file)=>{
            const form = new FormData();
            form.append('file', file);
            form.append('section', section);
            form.append('field_name', fieldName);
            try{
                const res = await fetch('/sidebar/upload_file', { method:'POST', body: form });
                const result = await res.json();
                if(result.success){
                    const displayName = result.original_name || result.original_filename || result.filename;
                    const url = result.url || `/sidebar/download_file/${section}/${result.filename}`;
                    if(result.is_image){ this.addImageToList(fieldName, displayName, url, result.id); }
                    else { this.addDocumentToList(fieldName, displayName, url, result.id); }
                }
            }catch(e){ /* ignore */ }
        });
        await Promise.all(promises);
    }

    async deleteFile(fieldName, fileUrl){
        const step = this.wizardSteps[this.currentStep]; if(!step) return;
        try{
            const res = await fetch('/sidebar/delete_file', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ filename: (fileUrl.split('/').pop()), section: step.endpoint, field_name: fieldName })});
            const result = await res.json();
            if(result.success){
                const list = document.getElementById(`sidebar-${fieldName}-list`);
                if(list){ Array.from(list.children).forEach(ch=>{ const a = ch.querySelector('a'); if(a && a.href === fileUrl){ ch.remove(); } }); }
            }
        }catch(e){ /* ignore */ }
    }

    async saveCurrent() {
        const step = this.wizardSteps[this.currentStep];
        if (!step) return;
        
        const stepData = {};
        
        // Собираем данные из полей
        step.fields.forEach(field => {
            const input = document.querySelector(`[name="${field.name}"]`);
            if (input) {
                if (field.type === 'checkbox') {
                    stepData[field.name] = input.checked ? '1' : '0';
                } else if (field.type === 'select') {
                    stepData[field.name] = input.value || '';
                } else if (field.type === 'textarea') {
                    stepData[field.name] = input.value || '';
                } else if (field.type === 'text') {
                    stepData[field.name] = input.value || '';
                }
            }
            
            // Обработка полей изображений
            if (field.type === 'images') {
                const imageList = document.getElementById(`${field.name}_image_list`);
                if (imageList) {
                    const imageItems = imageList.querySelectorAll('.file-item');
                    const images = [];
                    imageItems.forEach(item => {
                        const link = item.querySelector('a');
                        const displayName = link ? link.textContent : '';
                        let url = link ? link.href : '';
                        if (url) {
                            // Храним относительный URL, чтобы шаблоны корректно распознавали ссылки
                            // (link.href в браузере становится абсолютным).
                            try {
                                url = new URL(url, window.location.origin).pathname;
                            } catch (e) { /* keep as-is */ }
                            images.push(`${url}|${displayName}`);
                        }
                    });
                    stepData[field.name] = images.length > 0 ? images.join(',') : '';
                } else {
                    stepData[field.name] = '';
                }
            }
            
            // Обработка полей документов
            if (field.type === 'documents') {
                const documentList = document.getElementById(`${field.name}_document_list`);
                if (documentList) {
                    const documentItems = documentList.querySelectorAll('.file-item');
                    const documents = [];
                    documentItems.forEach(item => {
                        const link = item.querySelector('a');
                        const displayName = link ? link.textContent : '';
                        let url = link ? link.href : '';
                        if (url) {
                            try {
                                url = new URL(url, window.location.origin).pathname;
                            } catch (e) { /* keep as-is */ }
                            documents.push(`${url}|${displayName}`);
                        }
                    });
                    stepData[field.name] = documents.length > 0 ? documents.join(',') : '';
                } else {
                    stepData[field.name] = '';
                }
            }
            
            if (field.name === 'title') {
                stepData.title = stepData.title || stepData[field.name] || '';
            }
            if (field.name === 'content') {
                stepData.content = stepData.content || stepData[field.name] || '';
                stepData.text = stepData.content;
            }
        });
        
        // Собираем блоки контента
        const blocksListEl = document.querySelector('.wizard-blocks-list');
        if (blocksListEl) {
            const blockItems = blocksListEl.querySelectorAll('.wizard-block-item');
            const collectedBlocks = [];
            
            for (let i = 0; i < blockItems.length; i++) {
                const item = blockItems[i];
                const blockIndex = parseInt(item.dataset.blockIndex || i);
                const blockTypeText = item.querySelector('.wizard-block-type')?.textContent?.trim() || '';
                const blockType = this.extractBlockType(blockTypeText);
                
                // Получаем данные блока из wizardData или из DOM
                const existingBlocks = this.wizardData[step.id]?.content_blocks || [];
                let existingBlock = {};
                
                // Безопасно получаем блок по индексу
                if (Array.isArray(existingBlocks) && blockIndex >= 0 && blockIndex < existingBlocks.length) {
                    existingBlock = existingBlocks[blockIndex] || {};
                }
                
                // Создаем нормализованный блок, начиная с данных из existingBlock
                const normalizedBlock = {
                    type: blockType,
                    content: existingBlock.content || '',
                    title: existingBlock.title || '',
                    headers: existingBlock.headers || [],
                    rows: existingBlock.rows || [],
                    items: existingBlock.items || [],
                    documents: existingBlock.documents || [],
                    photos: existingBlock.photos || [],
                    persons: existingBlock.persons || [],
                    dishes: existingBlock.dishes || [],
                    dish: existingBlock.dish || null
                };
                
                // Копируем все остальные свойства из существующего блока (кроме content_blocks)
                for (const key in existingBlock) {
                    if (key !== 'content_blocks' && normalizedBlock[key] === undefined) {
                        normalizedBlock[key] = existingBlock[key];
                    }
                }
                
                // Убеждаемся, что тип блока сохранен правильно
                if (existingBlock.type) {
                    normalizedBlock.type = existingBlock.type;
                }
                
                // ВАЖНО: Обновляем данные блока из wizardData, если они были изменены через saveBlockEdit
                // Это гарантирует, что последние изменения (включая фото) сохраняются
                if (this.wizardData[step.id]?.content_blocks && 
                    Array.isArray(this.wizardData[step.id].content_blocks) && 
                    blockIndex >= 0 && 
                    blockIndex < this.wizardData[step.id].content_blocks.length) {
                    const latestBlock = this.wizardData[step.id].content_blocks[blockIndex];
                    if (latestBlock && typeof latestBlock === 'object') {
                        // Обновляем все свойства из последней версии блока
                        for (const key in latestBlock) {
                            if (key !== 'content_blocks') {
                                normalizedBlock[key] = latestBlock[key];
                            }
                        }
                    }
                }
                
                collectedBlocks.push(normalizedBlock);
            }
            
            stepData.content_blocks = collectedBlocks;
        } else {
            stepData.content_blocks = [];
        }
        
        // Рекурсивная функция для нормализации блоков
        const normalizeBlocksRecursive = (blocksArray) => {
            const normalizedBlocks = [];
            for (const block of blocksArray) {
                if (typeof block === 'object' && block !== null && !Array.isArray(block)) {
                    // Проверяем, есть ли внутри блока content_blocks
                    if (block.content_blocks && Array.isArray(block.content_blocks)) {
                        // Если есть, добавляем только вложенные блоки, сам блок не добавляем
                        normalizedBlocks.push(...normalizeBlocksRecursive(block.content_blocks));
                    } else {
                        // Создаем новый объект без content_blocks
                        const normalized = {};
                        for (const key in block) {
                            if (key !== 'content_blocks') {
                                normalized[key] = block[key];
                            }
                        }
                        normalizedBlocks.push(normalized);
                    }
                } else if (Array.isArray(block)) {
                    // Если блок - это массив, рекурсивно обрабатываем его
                    normalizedBlocks.push(...normalizeBlocksRecursive(block));
                } else {
                    normalizedBlocks.push(block);
                }
            }
            return normalizedBlocks;
        };
        
        // Нормализуем структуру блоков - убираем вложенные content_blocks
        if (Array.isArray(stepData.content_blocks)) {
            stepData.content_blocks = normalizeBlocksRecursive(stepData.content_blocks);
        }
        
        this.wizardData[step.id] = { ...(this.wizardData[step.id]||{}), ...stepData };
        const form = new FormData();
        form.append('wizard_data', JSON.stringify({[step.id]: stepData}));
        form.append('save_single','true');
        try {
            const res = await fetch('/sidebar/wizard_save', { method:'POST', body: form });
            const result = await res.json();
            const status = document.getElementById('sidebar-wizard-save-status');
            if (result.success) {
                if (status){
                    status.textContent='Сохранено';
                    status.style.color='#10b981';
                    setTimeout(()=>status.textContent='',1500);
                }
            } else {
                if (status){
                    status.textContent='Ошибка: '+(result.error||'');
                    status.style.color='#ef4444';
                }
            }
        } catch(e){
            const status = document.getElementById('sidebar-wizard-save-status');
            if (status){
                status.textContent='Ошибка сохранения';
                status.style.color='#ef4444';
            }
        }
    }
    
    extractBlockType(blockTypeText) {
        if (blockTypeText.includes('Текстовый')) return 'text';
        if (blockTypeText.includes('Таблица')) return 'table';
        if (blockTypeText.includes('Список')) return 'list';
        if (blockTypeText.includes('Документы')) return 'documents';
        if (blockTypeText.includes('Фотографии')) return 'photos';
        if (blockTypeText.includes('Персона')) return 'person';
        // Блоки блюд удалены из мастера заполнения
        return 'text';
    }

    go(delta){
        const next = this.currentStep + delta;
        if (next<0 || next>=this.wizardSteps.length) return;
        this.currentStep = next;
        this.renderCurrentStep();
    }

    async createSubsection(){
        const parent = this.wizardSteps[this.currentStep];
        // Используем существующий модал создания раздела, передав parent
        if (typeof window.openCreateSidebarSectionModal === 'function') {
            // Готовим UI: раскрываем родителя, чтобы новый подраздел сразу был виден после создания
            if (parent && parent.endpoint) {
                this.expandedStepEndpoints.add(parent.endpoint);
                this.renderSteps();
            }
            window.openCreateSidebarSectionModal({ parent: parent?.endpoint || '' });
        } else {
            alert('Окно создания раздела недоступно. Обновите страницу.');
        }
    }
    
    async deleteCurrentSection() {
        const step = this.wizardSteps[this.currentStep];
        if (!step) return;
        
        const sectionTitle = step.title || step.endpoint;
        if (!confirm(`Вы уверены, что хотите удалить раздел "${sectionTitle}"?\n\nЭто действие нельзя отменить. Все данные раздела будут удалены.`)) {
            return;
        }
        
        await this.deleteSubsection(step.endpoint, true);
    }
    
    async deleteSubsection(endpoint, isCurrentSection = false) {
        try {
            const response = await fetch('/sidebar/delete_subsection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ endpoint: endpoint })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Удаляем раздел из списка шагов
                const stepIndex = this.wizardSteps.findIndex(s => s.endpoint === endpoint);
                if (stepIndex >= 0) {
                    this.wizardSteps.splice(stepIndex, 1);
                    delete this.wizardData[endpoint];
                    
                    // Если удаленный шаг был текущим
                    if (isCurrentSection || this.currentStep >= stepIndex) {
                        // Если это был текущий раздел, закрываем мастер и перенаправляем
                        if (isCurrentSection) {
                            this.close();
                            // Перенаправляем на главную страницу или страницу админки
                            window.location.href = '/';
                            return;
                        }
                        // Иначе переключаемся на предыдущий
                        this.currentStep = Math.max(0, this.currentStep - 1);
                    }
                    
                    // Синхронизируем глобальные структуры
                    window.wizardSteps = this.wizardSteps;
                    window.wizardData = this.wizardData;
                    
                    // Обновляем отображение
                    this.renderSteps();
                    this.renderCurrentStep();
                }
                if (!isCurrentSection) {
                    alert('Раздел успешно удален');
                }
            } else {
                alert(`Ошибка: ${result.error}`);
            }
        } catch (error) {
            console.error('Ошибка при удалении раздела:', error);
            alert('Ошибка при удалении раздела');
        }
    }
}

// Инициализация sidebar мастера
let sidebarWizardManager;
document.addEventListener('DOMContentLoaded', () => {
    sidebarWizardManager = new SidebarWizardManager();
    window.sidebarWizardManager = sidebarWizardManager;
    // Совместимость с базовым шаблоном
    window.sidebarWizard = sidebarWizardManager;
});

// Глобальная функция для открытия sidebar мастера
function openSidebarWizard() {
    if (window.sidebarWizardManager) {
        window.sidebarWizardManager.open();
    } else {
        alert('Мастер заполнения бокового меню недоступен');
    }
}

window.openSidebarWizard = openSidebarWizard;

