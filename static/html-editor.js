// HTML редактор - модуль для работы с HTML контентом
class HtmlEditor {
    constructor() {
        this.editors = new Map();
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeHtmlEditors();
        });
    }

    initializeHtmlEditors() {
        const editorElements = document.querySelectorAll('.html-editor');
        editorElements.forEach(element => {
            this.createEditor(element);
        });
    }

    createEditor(element) {
        const editorId = element.id || 'editor_' + Date.now();
        element.id = editorId;
        
        const editor = {
            element: element,
            id: editorId,
            isActive: false,
            toolbar: null,
            preview: null
        };
        
        this.editors.set(editorId, editor);
        this.renderEditor(editor);
    }

    renderEditor(editor) {
        const container = document.createElement('div');
        container.className = 'html-editor-container';
        
        // Создаем тулбар
        const toolbar = this.createToolbar(editor);
        container.appendChild(toolbar);
        
        // Создаем область редактирования
        const editorArea = this.createEditorArea(editor);
        container.appendChild(editorArea);
        
        // Создаем превью
        const preview = this.createPreview(editor);
        container.appendChild(preview);
        
        // Заменяем оригинальный элемент
        editor.element.parentNode.replaceChild(container, editor.element);
        editor.toolbar = toolbar;
        editor.preview = preview;
    }

    createToolbar(editor) {
        const toolbar = document.createElement('div');
        toolbar.className = 'html-editor-toolbar';
        
        const buttons = [
            { icon: 'B', action: 'bold', title: 'Жирный' },
            { icon: 'I', action: 'italic', title: 'Курсив' },
            { icon: 'U', action: 'underline', title: 'Подчеркнутый' },
            { icon: 'S', action: 'strikethrough', title: 'Зачеркнутый' },
            { separator: true },
            { icon: 'H1', action: 'h1', title: 'Заголовок 1' },
            { icon: 'H2', action: 'h2', title: 'Заголовок 2' },
            { icon: 'H3', action: 'h3', title: 'Заголовок 3' },
            { separator: true },
            { icon: '📝', action: 'paragraph', title: 'Абзац' },
            { icon: '•', action: 'ul', title: 'Маркированный список' },
            { icon: '1.', action: 'ol', title: 'Нумерованный список' },
            { separator: true },
            { icon: '🔗', action: 'link', title: 'Ссылка' },
            { icon: '🖼️', action: 'image', title: 'Изображение' },
            { separator: true },
            { icon: '↶', action: 'undo', title: 'Отменить' },
            { icon: '↷', action: 'redo', title: 'Повторить' },
            { separator: true },
            { icon: '👁️', action: 'preview', title: 'Превью' },
            { icon: '📝', action: 'edit', title: 'Редактировать' }
        ];
        
        buttons.forEach(button => {
            if (button.separator) {
                const separator = document.createElement('div');
                separator.className = 'html-editor-separator';
                toolbar.appendChild(separator);
            } else {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'html-editor-btn';
                btn.innerHTML = button.icon;
                btn.title = button.title;
                btn.onclick = () => this.handleToolbarAction(editor, button.action);
                toolbar.appendChild(btn);
            }
        });
        
        return toolbar;
    }

    createEditorArea(editor) {
        const editorArea = document.createElement('div');
        editorArea.className = 'html-editor-area';
        
        const textarea = document.createElement('textarea');
        textarea.className = 'html-editor-textarea';
        textarea.value = editor.element.value || '';
        textarea.placeholder = 'Введите HTML код или используйте кнопки форматирования...';
        textarea.oninput = () => this.updatePreview(editor);
        
        editorArea.appendChild(textarea);
        editor.textarea = textarea;
        
        return editorArea;
    }

    createPreview(editor) {
        const preview = document.createElement('div');
        preview.className = 'html-editor-preview';
        preview.innerHTML = '<p>Превью будет отображено здесь...</p>';
        
        return preview;
    }

    handleToolbarAction(editor, action) {
        const textarea = editor.textarea;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);
        
        let newText = '';
        
        switch (action) {
            case 'bold':
                newText = `<strong>${selectedText || 'жирный текст'}</strong>`;
                break;
            case 'italic':
                newText = `<em>${selectedText || 'курсивный текст'}</em>`;
                break;
            case 'underline':
                newText = `<u>${selectedText || 'подчеркнутый текст'}</u>`;
                break;
            case 'strikethrough':
                newText = `<s>${selectedText || 'зачеркнутый текст'}</s>`;
                break;
            case 'h1':
                newText = `<h1>${selectedText || 'Заголовок 1'}</h1>`;
                break;
            case 'h2':
                newText = `<h2>${selectedText || 'Заголовок 2'}</h2>`;
                break;
            case 'h3':
                newText = `<h3>${selectedText || 'Заголовок 3'}</h3>`;
                break;
            case 'paragraph':
                newText = `<p>${selectedText || 'Новый абзац'}</p>`;
                break;
            case 'ul':
                newText = `<ul>\n<li>${selectedText || 'Элемент списка'}</li>\n</ul>`;
                break;
            case 'ol':
                newText = `<ol>\n<li>${selectedText || 'Элемент списка'}</li>\n</ol>`;
                break;
            case 'link':
                const url = prompt('Введите URL ссылки:', 'https://');
                if (url) {
                    newText = `<a href="${url}">${selectedText || 'Текст ссылки'}</a>`;
                }
                break;
            case 'image':
                const imageUrl = prompt('Введите URL изображения:', 'https://');
                if (imageUrl) {
                    newText = `<img src="${imageUrl}" alt="${selectedText || 'Описание изображения'}" style="max-width: 100%; height: auto;">`;
                }
                break;
            case 'undo':
                // Простая реализация отмены
                this.undo(editor);
                return;
            case 'redo':
                // Простая реализация повтора
                this.redo(editor);
                return;
            case 'preview':
                this.togglePreview(editor);
                return;
            case 'edit':
                this.toggleEdit(editor);
                return;
        }
        
        if (newText) {
            this.insertText(textarea, newText, start, end);
            this.updatePreview(editor);
        }
    }

    insertText(textarea, text, start, end) {
        const before = textarea.value.substring(0, start);
        const after = textarea.value.substring(end);
        const newValue = before + text + after;
        
        textarea.value = newValue;
        textarea.focus();
        
        // Устанавливаем курсор после вставленного текста
        const newPosition = start + text.length;
        textarea.setSelectionRange(newPosition, newPosition);
    }

    updatePreview(editor) {
        if (!editor.preview) return;
        
        const content = editor.textarea.value;
        if (content.trim()) {
            editor.preview.innerHTML = content;
        } else {
            editor.preview.innerHTML = '<p>Превью будет отображено здесь...</p>';
        }
    }

    togglePreview(editor) {
        const textarea = editor.textarea;
        const preview = editor.preview;
        
        if (textarea.style.display === 'none') {
            textarea.style.display = 'block';
            preview.style.display = 'none';
        } else {
            textarea.style.display = 'none';
            preview.style.display = 'block';
            this.updatePreview(editor);
        }
    }

    toggleEdit(editor) {
        const textarea = editor.textarea;
        const preview = editor.preview;
        
        if (textarea.style.display === 'none') {
            textarea.style.display = 'block';
            preview.style.display = 'none';
        } else {
            textarea.style.display = 'none';
            preview.style.display = 'block';
        }
    }

    undo(editor) {
        // Простая реализация отмены
        if (editor.history && editor.history.length > 0) {
            const previousState = editor.history.pop();
            editor.textarea.value = previousState;
            this.updatePreview(editor);
        }
    }

    redo(editor) {
        // Простая реализация повтора
        if (editor.redoHistory && editor.redoHistory.length > 0) {
            const nextState = editor.redoHistory.pop();
            editor.textarea.value = nextState;
            this.updatePreview(editor);
        }
    }

    saveHistory(editor) {
        if (!editor.history) {
            editor.history = [];
        }
        if (!editor.redoHistory) {
            editor.redoHistory = [];
        }
        
        editor.history.push(editor.textarea.value);
        editor.redoHistory = []; // Очищаем историю повтора при новом действии
        
        // Ограничиваем размер истории
        if (editor.history.length > 50) {
            editor.history.shift();
        }
    }

    getValue(editorId) {
        const editor = this.editors.get(editorId);
        return editor ? editor.textarea.value : '';
    }

    setValue(editorId, value) {
        const editor = this.editors.get(editorId);
        if (editor) {
            editor.textarea.value = value;
            this.updatePreview(editor);
        }
    }

    destroy(editorId) {
        const editor = this.editors.get(editorId);
        if (editor) {
            this.editors.delete(editorId);
        }
    }
}

// Глобальные функции для совместимости
function insertHtmlTag(tag, placeholder = '') {
    const activeEditor = document.querySelector('.html-editor-textarea:focus');
    if (activeEditor) {
        const start = activeEditor.selectionStart;
        const end = activeEditor.selectionEnd;
        const selectedText = activeEditor.value.substring(start, end);
        const newText = `<${tag}>${selectedText || placeholder}</${tag}>`;
        
        const before = activeEditor.value.substring(0, start);
        const after = activeEditor.value.substring(end);
        const newValue = before + newText + after;
        
        activeEditor.value = newValue;
        activeEditor.focus();
        
        const newPosition = start + newText.length;
        activeEditor.setSelectionRange(newPosition, newPosition);
    }
}

function updateHtmlPreview(editorId) {
    const editor = htmlEditor.editors.get(editorId);
    if (editor) {
        htmlEditor.updatePreview(editor);
    }
}

function initializeHtmlEditors() {
    if (htmlEditor) {
        htmlEditor.initializeHtmlEditors();
    } else {
        // Если htmlEditor еще не инициализирован, ждем DOMContentLoaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                if (htmlEditor) {
                    htmlEditor.initializeHtmlEditors();
                }
            });
        } else {
            // DOM уже загружен, но htmlEditor еще не создан
            // Создаем его немедленно
            htmlEditor = new HtmlEditor();
            window.htmlEditor = htmlEditor;
            htmlEditor.initializeHtmlEditors();
        }
    }
}

// Инициализация HTML редактора
let htmlEditor;
document.addEventListener('DOMContentLoaded', () => {
    htmlEditor = new HtmlEditor();
    window.htmlEditor = htmlEditor;
});

// Экспорт для глобального доступа
window.insertHtmlTag = insertHtmlTag;
window.updateHtmlPreview = updateHtmlPreview;
window.initializeHtmlEditors = initializeHtmlEditors;
