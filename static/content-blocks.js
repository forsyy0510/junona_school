// Модуль для работы с блоками контента
class ContentBlockManager {
    constructor() {
        this.blocks = new Map();
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeContentBlocks();
        });
    }

    initializeContentBlocks() {
        const blockElements = document.querySelectorAll('.content-block');
        blockElements.forEach(block => {
            this.registerBlock(block);
        });
    }

    registerBlock(block) {
        const blockId = block.id || 'block_' + Date.now();
        block.id = blockId;
        
        const blockData = {
            element: block,
            id: blockId,
            type: block.dataset.type || 'text',
            content: block.dataset.content || '',
            isEditable: block.hasAttribute('data-editable'),
            editor: null
        };
        
        this.blocks.set(blockId, blockData);
        this.setupBlockEvents(blockData);
    }

    setupBlockEvents(blockData) {
        if (blockData.isEditable) {
            this.setupEditableBlock(blockData);
        }
    }

    setupEditableBlock(blockData) {
        const editButton = blockData.element.querySelector('.edit-block-btn');
        const saveButton = blockData.element.querySelector('.save-block-btn');
        const cancelButton = blockData.element.querySelector('.cancel-block-btn');
        
        if (editButton) {
            editButton.addEventListener('click', () => {
                this.startEditing(blockData.id);
            });
        }
        
        if (saveButton) {
            saveButton.addEventListener('click', () => {
                this.saveBlock(blockData.id);
            });
        }
        
        if (cancelButton) {
            cancelButton.addEventListener('click', () => {
                this.cancelEditing(blockData.id);
            });
        }
    }

    startEditing(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData || !blockData.isEditable) return;
        
        blockData.element.classList.add('editing');
        
        // Создаем редактор в зависимости от типа блока
        switch (blockData.type) {
            case 'text':
                this.createTextEditor(blockData);
                break;
            case 'html':
                this.createHtmlEditor(blockData);
                break;
            case 'table':
                this.createTableEditor(blockData);
                break;
            case 'list':
                this.createListEditor(blockData);
                break;
            case 'documents':
                this.createDocumentsEditor(blockData);
                break;
            case 'photos':
                this.createPhotosEditor(blockData);
                break;
            case 'persons':
                this.createPersonsEditor(blockData);
                break;
        }
    }

    createTextEditor(blockData) {
        const content = blockData.element.querySelector('.block-content');
        if (!content) return;
        
        const textarea = document.createElement('textarea');
        textarea.className = 'block-editor-textarea';
        textarea.value = content.textContent;
        textarea.rows = 10;
        
        content.style.display = 'none';
        content.parentNode.insertBefore(textarea, content);
        
        blockData.editor = textarea;
    }

    createHtmlEditor(blockData) {
        const content = blockData.element.querySelector('.block-content');
        if (!content) return;
        
        const textarea = document.createElement('textarea');
        textarea.className = 'block-editor-textarea html-editor';
        textarea.value = content.innerHTML;
        textarea.rows = 15;
        
        content.style.display = 'none';
        content.parentNode.insertBefore(textarea, content);
        
        blockData.editor = textarea;
        
        // Инициализируем HTML редактор
        if (window.htmlEditor) {
            window.htmlEditor.createEditor(textarea);
        }
    }

    createTableEditor(blockData) {
        const content = blockData.element.querySelector('.block-content');
        if (!content) return;
        
        const editor = document.createElement('div');
        editor.className = 'table-editor';
        
        // Создаем интерфейс для редактирования таблицы
        editor.innerHTML = `
            <div class="table-editor-controls">
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.addTableRow('${blockData.id}')">+ Строка</button>
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.addTableColumn('${blockData.id}')">+ Столбец</button>
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.removeTableRow('${blockData.id}')">- Строка</button>
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.removeTableColumn('${blockData.id}')">- Столбец</button>
            </div>
            <div class="table-editor-content" id="table_editor_${blockData.id}"></div>
        `;
        
        content.style.display = 'none';
        content.parentNode.insertBefore(editor, content);
        
        blockData.editor = editor;
        this.initializeTableEditor(blockData);
    }

    createListEditor(blockData) {
        const content = blockData.element.querySelector('.block-content');
        if (!content) return;
        
        const editor = document.createElement('div');
        editor.className = 'list-editor';
        
        editor.innerHTML = `
            <div class="list-editor-controls">
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.addListItem('${blockData.id}')">+ Элемент</button>
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.removeListItem('${blockData.id}')">- Элемент</button>
            </div>
            <div class="list-editor-content" id="list_editor_${blockData.id}"></div>
        `;
        
        content.style.display = 'none';
        content.parentNode.insertBefore(editor, content);
        
        blockData.editor = editor;
        this.initializeListEditor(blockData);
    }

    createDocumentsEditor(blockData) {
        const content = blockData.element.querySelector('.block-content');
        if (!content) return;
        
        const editor = document.createElement('div');
        editor.className = 'documents-editor';
        
        editor.innerHTML = `
            <div class="documents-editor-controls">
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.addDocument('${blockData.id}')">+ Документ</button>
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.removeDocument('${blockData.id}')">- Документ</button>
            </div>
            <div class="documents-editor-content" id="documents_editor_${blockData.id}"></div>
        `;
        
        content.style.display = 'none';
        content.parentNode.insertBefore(editor, content);
        
        blockData.editor = editor;
        this.initializeDocumentsEditor(blockData);
    }

    createPhotosEditor(blockData) {
        const content = blockData.element.querySelector('.block-content');
        if (!content) return;
        
        const editor = document.createElement('div');
        editor.className = 'photos-editor';
        
        editor.innerHTML = `
            <div class="photos-editor-controls">
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.addPhoto('${blockData.id}')">+ Фото</button>
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.removePhoto('${blockData.id}')">- Фото</button>
            </div>
            <div class="photos-editor-content" id="photos_editor_${blockData.id}"></div>
        `;
        
        content.style.display = 'none';
        content.parentNode.insertBefore(editor, content);
        
        blockData.editor = editor;
        this.initializePhotosEditor(blockData);
    }

    createPersonsEditor(blockData) {
        const content = blockData.element.querySelector('.block-content');
        if (!content) return;
        
        const editor = document.createElement('div');
        editor.className = 'persons-editor';
        
        editor.innerHTML = `
            <div class="persons-editor-controls">
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.addPerson('${blockData.id}')">+ Персона</button>
                <button type="button" class="btn btn-sm" onclick="contentBlockManager.removePerson('${blockData.id}')">- Персона</button>
            </div>
            <div class="persons-editor-content" id="persons_editor_${blockData.id}"></div>
        `;
        
        content.style.display = 'none';
        content.parentNode.insertBefore(editor, content);
        
        blockData.editor = editor;
        this.initializePersonsEditor(blockData);
    }

    // Методы для работы с таблицами
    initializeTableEditor(blockData) {
        const editor = blockData.editor;
        const content = editor.querySelector('.table-editor-content');
        
        // Парсим существующую таблицу или создаем новую
        const existingTable = blockData.element.querySelector('.block-content table');
        if (existingTable) {
            content.innerHTML = existingTable.outerHTML;
        } else {
            this.createNewTable(content);
        }
    }

    createNewTable(container) {
        const table = document.createElement('table');
        table.className = 'table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Столбец 1</th>
                    <th>Столбец 2</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td contenteditable="true">Ячейка 1</td>
                    <td contenteditable="true">Ячейка 2</td>
                </tr>
            </tbody>
        `;
        container.appendChild(table);
    }

    addTableRow(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const table = blockData.editor.querySelector('table tbody');
        if (table) {
            const newRow = document.createElement('tr');
            const cellCount = table.rows[0] ? table.rows[0].cells.length : 2;
            
            for (let i = 0; i < cellCount; i++) {
                const cell = document.createElement('td');
                cell.contentEditable = true;
                cell.textContent = 'Новая ячейка';
                newRow.appendChild(cell);
            }
            
            table.appendChild(newRow);
        }
    }

    addTableColumn(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const table = blockData.editor.querySelector('table');
        if (table) {
            const headerRow = table.querySelector('thead tr');
            const bodyRows = table.querySelectorAll('tbody tr');
            
            if (headerRow) {
                const headerCell = document.createElement('th');
                headerCell.textContent = 'Новый столбец';
                headerRow.appendChild(headerCell);
            }
            
            bodyRows.forEach(row => {
                const cell = document.createElement('td');
                cell.contentEditable = true;
                cell.textContent = 'Новая ячейка';
                row.appendChild(cell);
            });
        }
    }

    removeTableRow(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const table = blockData.editor.querySelector('table tbody');
        if (table && table.rows.length > 1) {
            table.removeChild(table.lastChild);
        }
    }

    removeTableColumn(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const table = blockData.editor.querySelector('table');
        if (table) {
            const headerRow = table.querySelector('thead tr');
            const bodyRows = table.querySelectorAll('tbody tr');
            
            if (headerRow && headerRow.cells.length > 1) {
                headerRow.removeChild(headerRow.lastChild);
            }
            
            bodyRows.forEach(row => {
                if (row.cells.length > 1) {
                    row.removeChild(row.lastChild);
                }
            });
        }
    }

    // Методы для работы со списками
    initializeListEditor(blockData) {
        const editor = blockData.editor;
        const content = editor.querySelector('.list-editor-content');
        
        // Парсим существующий список или создаем новый
        const existingList = blockData.element.querySelector('.block-content ul, .block-content ol');
        if (existingList) {
            content.innerHTML = existingList.outerHTML;
        } else {
            this.createNewList(content);
        }
    }

    createNewList(container) {
        const list = document.createElement('ul');
        list.className = 'list-unstyled';
        list.innerHTML = `
            <li contenteditable="true">Элемент списка 1</li>
            <li contenteditable="true">Элемент списка 2</li>
        `;
        container.appendChild(list);
    }

    addListItem(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const list = blockData.editor.querySelector('ul, ol');
        if (list) {
            const newItem = document.createElement('li');
            newItem.contentEditable = true;
            newItem.textContent = 'Новый элемент';
            list.appendChild(newItem);
        }
    }

    removeListItem(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const list = blockData.editor.querySelector('ul, ol');
        if (list && list.children.length > 1) {
            list.removeChild(list.lastChild);
        }
    }

    // Методы для работы с документами
    initializeDocumentsEditor(blockData) {
        const editor = blockData.editor;
        const content = editor.querySelector('.documents-editor-content');
        
        // Парсим существующие документы или создаем новый список
        const existingDocs = blockData.element.querySelector('.block-content .document-list');
        if (existingDocs) {
            content.innerHTML = existingDocs.outerHTML;
        } else {
            this.createNewDocumentList(content);
        }
    }

    createNewDocumentList(container) {
        const list = document.createElement('div');
        list.className = 'document-list';
        list.innerHTML = `
            <div class="document-item">
                <input type="text" placeholder="Название документа" class="form-control">
                <input type="file" class="form-control">
            </div>
        `;
        container.appendChild(list);
    }

    addDocument(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const list = blockData.editor.querySelector('.document-list');
        if (list) {
            const newItem = document.createElement('div');
            newItem.className = 'document-item';
            newItem.innerHTML = `
                <input type="text" placeholder="Название документа" class="form-control">
                <input type="file" class="form-control">
            `;
            list.appendChild(newItem);
        }
    }

    removeDocument(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const list = blockData.editor.querySelector('.document-list');
        if (list && list.children.length > 1) {
            list.removeChild(list.lastChild);
        }
    }

    // Методы для работы с фотографиями
    initializePhotosEditor(blockData) {
        const editor = blockData.editor;
        const content = editor.querySelector('.photos-editor-content');
        
        // Парсим существующие фотографии или создаем новый список
        const existingPhotos = blockData.element.querySelector('.block-content .photo-list');
        if (existingPhotos) {
            content.innerHTML = existingPhotos.outerHTML;
        } else {
            this.createNewPhotoList(content);
        }
    }

    createNewPhotoList(container) {
        const list = document.createElement('div');
        list.className = 'photo-list';
        list.innerHTML = `
            <div class="photo-item">
                <input type="text" placeholder="Описание фото" class="form-control">
                <input type="file" accept="image/*" class="form-control">
            </div>
        `;
        container.appendChild(list);
    }

    addPhoto(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const list = blockData.editor.querySelector('.photo-list');
        if (list) {
            const newItem = document.createElement('div');
            newItem.className = 'photo-item';
            newItem.innerHTML = `
                <input type="text" placeholder="Описание фото" class="form-control">
                <input type="file" accept="image/*" class="form-control">
            `;
            list.appendChild(newItem);
        }
    }

    removePhoto(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const list = blockData.editor.querySelector('.photo-list');
        if (list && list.children.length > 1) {
            list.removeChild(list.lastChild);
        }
    }

    // Методы для работы с персонами
    initializePersonsEditor(blockData) {
        const editor = blockData.editor;
        const content = editor.querySelector('.persons-editor-content');
        
        // Парсим существующих персон или создаем новый список
        const existingPersons = blockData.element.querySelector('.block-content .person-list');
        if (existingPersons) {
            content.innerHTML = existingPersons.outerHTML;
        } else {
            this.createNewPersonList(content);
        }
    }

    createNewPersonList(container) {
        const list = document.createElement('div');
        list.className = 'person-list';
        list.innerHTML = `
            <div class="person-item">
                <input type="text" placeholder="ФИО" class="form-control">
                <input type="text" placeholder="Должность" class="form-control">
                <input type="text" placeholder="Контакт" class="form-control">
                <input type="file" accept="image/*" class="form-control">
            </div>
        `;
        container.appendChild(list);
    }

    addPerson(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const list = blockData.editor.querySelector('.person-list');
        if (list) {
            const newItem = document.createElement('div');
            newItem.className = 'person-item';
            newItem.innerHTML = `
                <input type="text" placeholder="ФИО" class="form-control">
                <input type="text" placeholder="Должность" class="form-control">
                <input type="text" placeholder="Контакт" class="form-control">
                <input type="file" accept="image/*" class="form-control">
            `;
            list.appendChild(newItem);
        }
    }

    removePerson(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const list = blockData.editor.querySelector('.person-list');
        if (list && list.children.length > 1) {
            list.removeChild(list.lastChild);
        }
    }

    // Методы для сохранения и отмены
    saveBlock(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const content = blockData.element.querySelector('.block-content');
        if (!content) return;
        
        // Сохраняем содержимое в зависимости от типа блока
        switch (blockData.type) {
            case 'text':
                content.textContent = blockData.editor.value;
                break;
            case 'html':
                content.innerHTML = blockData.editor.value;
                break;
            case 'table':
            case 'list':
            case 'documents':
            case 'photos':
            case 'persons':
                content.innerHTML = blockData.editor.innerHTML;
                break;
        }
        
        this.finishEditing(blockId);
    }

    cancelEditing(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        this.finishEditing(blockId);
    }

    finishEditing(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        blockData.element.classList.remove('editing');
        
        const content = blockData.element.querySelector('.block-content');
        if (content) {
            content.style.display = 'block';
        }
        
        if (blockData.editor) {
            blockData.editor.remove();
            blockData.editor = null;
        }
    }

    // Методы для работы с блоками
    createBlock(type, content = '', isEditable = false) {
        const blockId = 'block_' + Date.now();
        const block = document.createElement('div');
        block.className = 'content-block';
        block.id = blockId;
        block.dataset.type = type;
        block.dataset.content = content;
        
        if (isEditable) {
            block.setAttribute('data-editable', 'true');
        }
        
        block.innerHTML = `
            <div class="block-content">${content}</div>
            ${isEditable ? `
                <div class="block-controls">
                    <button class="btn btn-sm edit-block-btn">Редактировать</button>
                    <button class="btn btn-sm save-block-btn" style="display: none;">Сохранить</button>
                    <button class="btn btn-sm cancel-block-btn" style="display: none;">Отмена</button>
                </div>
            ` : ''}
        `;
        
        this.registerBlock(block);
        return blockId;
    }

    removeBlock(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        blockData.element.remove();
        this.blocks.delete(blockId);
    }

    getBlockContent(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return '';
        
        const content = blockData.element.querySelector('.block-content');
        return content ? content.innerHTML : '';
    }

    setBlockContent(blockId, content) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const contentElement = blockData.element.querySelector('.block-content');
        if (contentElement) {
            contentElement.innerHTML = content;
        }
    }
}

// Инициализация менеджера блоков контента
let contentBlockManager;
document.addEventListener('DOMContentLoaded', () => {
    contentBlockManager = new ContentBlockManager();
});

// Экспорт для глобального доступа
window.contentBlockManager = contentBlockManager;
