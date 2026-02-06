// Карта сайта: разделы левого меню — дерево, перемещение, подразделы, редактирование

let sitemapData = [];
let draggedElement = null;
let dropTargetMode = null; // 'child' | 'before' | null

document.addEventListener('DOMContentLoaded', () => {
    loadSitemap();
    setupDragAndDrop();
});

async function loadSitemap() {
    const loading = document.getElementById('sitemap-loading');
    const tree = document.getElementById('sitemap-tree');
    const empty = document.getElementById('sitemap-empty');

    try {
        const response = await fetch('/admin/api/sections');
        const result = await response.json();

        loading.style.display = 'none';

        if (result.success && result.sections.length > 0) {
            sitemapData = result.sections;
            renderTree();
            tree.style.display = 'block';
        } else {
            empty.style.display = 'block';
        }
    } catch (error) {
        loading.innerHTML = `<div style="color: #ef4444;">Ошибка загрузки: ${escapeHtml(error.message)}</div>`;
    }
}

function renderTree() {
    const tree = document.getElementById('sitemap-tree');
    const sortedData = [...sitemapData];
    sortedData.forEach(item => {
        if (item.parent && String(item.parent).startsWith('/sidebar/')) {
            item.parent = String(item.parent).replace('/sidebar/', '');
        }
    });
    sortedData.sort((a, b) => (a.order || 0) - (b.order || 0));

    const rootItems = sortedData.filter(item => !item.parent);

    tree.innerHTML = '';

    function renderNode(item, level) {
        const node = document.createElement('div');
        node.className = 'sitemap-node';
        node.dataset.id = item.id;
        node.dataset.endpoint = item.endpoint;

        const directChildren = sortedData.filter(ch => (ch.parent || '') === item.endpoint);
        directChildren.sort((a, b) => (a.order || 0) - (b.order || 0));

        const row = createItemRow(item, level, directChildren.length > 0);
        node.appendChild(row);

        if (directChildren.length > 0) {
            const childrenWrap = document.createElement('div');
            childrenWrap.className = 'sitemap-children';
            directChildren.forEach(ch => {
                childrenWrap.appendChild(renderNode(ch, level + 1));
            });
            node.appendChild(childrenWrap);
        }

        return node;
    }

    rootItems.forEach(item => {
        tree.appendChild(renderNode(item, 0));
    });
}

function getDescendantEndpoints(endpoint) {
    const result = [];
    function collect(ep) {
        sitemapData.filter(s => (s.parent || '') === ep).forEach(s => {
            result.push(s.endpoint);
            collect(s.endpoint);
        });
    }
    collect(endpoint);
    return result;
}

function getMoveToParentOptionsHTML(currentItem) {
    const descendants = getDescendantEndpoints(currentItem.endpoint);
    const currentParent = (currentItem.parent || '').toString();
    let html = '<option value="">— Корень —</option>';
    sitemapData.forEach(s => {
        if (s.id === currentItem.id) return;
        if (descendants.indexOf(s.endpoint) !== -1) return;
        const selected = (s.endpoint === currentParent) ? ' selected' : '';
        html += `<option value="${escapeAttr(s.endpoint)}"${selected}>${escapeHtml(s.title)}</option>`;
    });
    return html;
}

function moveSectionToParent(sectionId, newParentEndpoint) {
    const section = sitemapData.find(s => s.id === parseInt(sectionId, 10));
    if (!section) return;
    section.parent = (newParentEndpoint && newParentEndpoint.trim()) || null;
    renderTree();
}

function createItemRow(item, level, hasChildren) {
    const row = document.createElement('div');
    row.className = 'sitemap-item';
    row.dataset.id = item.id;
    row.dataset.endpoint = item.endpoint;
    row.draggable = true;

    if (level > 0) {
        row.style.marginLeft = (level * 24) + 'px';
    }

    row.innerHTML = `
        <div class="sitemap-item-handle" title="Перетащите для изменения порядка или в другой раздел">☰</div>
        <div class="sitemap-item-content">
            <div>
                <div class="sitemap-item-title">${escapeHtml(item.title)}</div>
                <div class="sitemap-item-url">${escapeHtml(item.url || '/sidebar/' + item.endpoint)}</div>
            </div>
        </div>
        <div class="sitemap-item-actions">
            <select class="sitemap-move-select" onchange="moveSectionToParent(${item.id}, this.value)" title="Переместить в другой раздел (сделать подразделом)">
                ${getMoveToParentOptionsHTML(item)}
            </select>
            <button type="button" class="btn-edit" onclick="editSection(${item.id}, this.dataset.title)" data-title="${escapeAttr(item.title)}" title="Редактировать название">✏️</button>
            <button type="button" class="btn-sub" onclick="addSubSection(this.dataset.endpoint, this.dataset.parentTitle)" data-endpoint="${escapeAttr(item.endpoint)}" data-parent-title="${escapeAttr(item.title)}" title="Добавить подраздел">➕ Подраздел</button>
            <a href="/sidebar/${escapeAttr(item.endpoint)}" class="btn-edit" style="text-decoration:none;display:inline-flex;align-items:center;" title="Открыть раздел">📄</a>
            <button type="button" class="btn-delete" onclick="deleteSection(${item.id}, this.dataset.title)" data-title="${escapeAttr(item.title)}" title="Удалить">🗑️</button>
        </div>
    `;
    return row;
}

function setupDragAndDrop() {
    document.addEventListener('dragstart', (e) => {
        const item = e.target.closest('.sitemap-item');
        if (item) {
            draggedElement = item;
            item.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', item.dataset.id);
        }
    });

    document.addEventListener('dragend', (e) => {
        const item = e.target.closest('.sitemap-item');
        if (item) {
            item.classList.remove('dragging');
            document.querySelectorAll('.sitemap-item').forEach(el => {
                el.classList.remove('drag-over', 'drop-as-child');
            });
        }
        draggedElement = null;
        dropTargetMode = null;
    });

    document.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (!draggedElement) return;
        const targetRow = e.target.closest('.sitemap-item');
        if (!targetRow || targetRow === draggedElement) return;
        if (draggedElement.closest('.sitemap-node') && targetRow.closest('.sitemap-node') && draggedElement.closest('.sitemap-node').contains(targetRow)) return;

        document.querySelectorAll('.sitemap-item').forEach(el => el.classList.remove('drag-over', 'drop-as-child'));
        const rect = targetRow.getBoundingClientRect();
        const mid = rect.top + rect.height / 2;
        if (e.clientY < mid) {
            targetRow.classList.add('drag-over');
            targetRow.classList.remove('drop-as-child');
            dropTargetMode = 'before';
        } else {
            targetRow.classList.remove('drag-over');
            targetRow.classList.add('drop-as-child');
            dropTargetMode = 'child';
        }
    });

    document.addEventListener('dragleave', (e) => {
        if (!e.target.closest || !e.target.closest('.sitemap-item')) return;
        const stillInside = e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest('.sitemap-item');
        if (!stillInside) {
            e.target.closest('.sitemap-item').classList.remove('drag-over', 'drop-as-child');
            dropTargetMode = null;
        }
    });

    document.addEventListener('drop', (e) => {
        e.preventDefault();
        const targetRow = e.target.closest('.sitemap-item');
        if (!targetRow || !draggedElement || targetRow === draggedElement) return;

        const targetNode = targetRow.closest('.sitemap-node');
        const draggedNode = draggedElement.closest('.sitemap-node');
        if (!targetNode || !draggedNode) return;
        if (draggedNode.contains(targetNode)) return;

        const targetId = parseInt(targetRow.dataset.id);
        const draggedId = parseInt(draggedElement.dataset.id);
        const targetSection = sitemapData.find(s => s.id === targetId);
        const draggedSection = sitemapData.find(s => s.id === draggedId);
        if (!targetSection || !draggedSection) return;

        if (dropTargetMode === 'child') {
            draggedSection.parent = targetSection.endpoint;
            const childrenContainer = targetNode.querySelector(':scope > .sitemap-children');
            if (childrenContainer) {
                childrenContainer.appendChild(draggedNode);
            } else {
                const wrap = document.createElement('div');
                wrap.className = 'sitemap-children';
                wrap.appendChild(draggedNode);
                targetNode.appendChild(wrap);
            }
        } else {
            draggedSection.parent = targetSection.parent || null;
            const parent = targetNode.parentElement;
            const isTreeRoot = parent && parent.id === 'sitemap-tree';
            const insertBefore = isTreeRoot ? targetNode : targetNode;
            if (parent) {
                parent.insertBefore(draggedNode, dropTargetMode === 'before' ? insertBefore : insertBefore.nextSibling);
            }
        }

        applyOrderFromDOM();
        document.querySelectorAll('.sitemap-item').forEach(el => el.classList.remove('drag-over', 'drop-as-child'));
        dropTargetMode = null;
    });
}

function applyOrderFromDOM() {
    const tree = document.getElementById('sitemap-tree');
    if (!tree) return;

    function walk(container, parentEndpoint) {
        const nodes = container.querySelectorAll(':scope > .sitemap-node');
        nodes.forEach((node, index) => {
            const row = node.querySelector(':scope > .sitemap-item');
            if (!row) return;
            const id = parseInt(row.dataset.id);
            const section = sitemapData.find(s => s.id === id);
            if (section) {
                section.order = index;
                section.parent = parentEndpoint || null;
            }
            const children = node.querySelector(':scope > .sitemap-children');
            if (children) walk(children, row.dataset.endpoint);
        });
    }

    walk(tree, null);
}

async function saveOrder() {
    applyOrderFromDOM();
    const updates = sitemapData.map(s => ({
        id: s.id,
        order: s.order ?? 0,
        parent: s.parent || null
    }));

    try {
        const response = await fetch('/admin/api/sections/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ updates })
        });
        const result = await response.json();

        if (result.success) {
            alert('Изменения сохранены');
            loadSitemap();
        } else {
            alert('Ошибка: ' + (result.error || 'Не удалось сохранить'));
        }
    } catch (error) {
        alert('Ошибка сохранения: ' + error.message);
    }
}

async function editSection(sectionId, currentTitle) {
    const title = prompt('Название раздела:', currentTitle);
    if (title === null || !title.trim()) return;

    try {
        const response = await fetch('/admin/api/sections/' + sectionId, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title.trim() })
        });
        const result = await response.json();

        if (result.success) {
            const section = sitemapData.find(s => s.id === sectionId);
            if (section) section.title = result.section.title;
            renderTree();
        } else {
            alert('Ошибка: ' + (result.error || 'Не удалось обновить'));
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

function addSubSection(parentEndpoint, parentTitle) {
    const title = prompt('Название подраздела для «' + parentTitle + '»:');
    if (!title || !title.trim()) return;

    (async () => {
        try {
            const response = await fetch('/admin/api/sections/quick-create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title.trim(), parent: parentEndpoint })
            });
            const result = await response.json();

            if (result.success) {
                alert('Подраздел создан');
                loadSitemap();
            } else {
                alert('Ошибка: ' + (result.error || 'Не удалось создать'));
            }
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    })();
}

async function deleteSection(sectionId, title) {
    if (!confirm('Удалить раздел «' + title + '»?')) return;

    try {
        const response = await fetch('/admin/api/sections/' + sectionId, { method: 'DELETE' });
        const result = await response.json();

        if (result.success) {
            alert('Раздел удалён');
            loadSitemap();
        } else {
            alert('Ошибка: ' + (result.error || 'Не удалось удалить'));
        }
    } catch (error) {
        alert('Ошибка удаления: ' + error.message);
    }
}

function addNewSection() {
    const title = prompt('Название нового раздела (корневой пункт меню):');
    if (!title || !title.trim()) return;

    (async () => {
        try {
            const response = await fetch('/admin/api/sections/quick-create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title.trim() })
            });
            const result = await response.json();

            if (result.success) {
                alert('Раздел создан');
                loadSitemap();
            } else {
                alert('Ошибка: ' + (result.error || 'Не удалось создать'));
            }
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    })();
}

function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/"/g, '&quot;');
}
