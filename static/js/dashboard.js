/* ==========================================================
   Lab Manager — Dashboard JS (vanilla)
   ========================================================== */

// ──────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────

async function api(url, opts = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...opts,
    });
    if (!res.ok && !url.includes('/report/export')) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || '请求失败');
    }
    return res;
}

function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function toast(msg, type = 'info') {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = msg;
    document.getElementById('toastContainer').appendChild(el);
    setTimeout(() => el.remove(), 3200);
}

function todayStr() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

// ──────────────────────────────────────────────
// Navigation
// ──────────────────────────────────────────────

const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view');

function switchView(name) {
    navItems.forEach(n => n.classList.toggle('active', n.dataset.view === name));
    views.forEach(v => v.classList.toggle('active', v.id === `view-${name}`));

    if (name === 'dashboard')     refreshDashboard();
    else if (name === 'inventory')    loadInventory();
    else if (name === 'transactions') loadTransactions();
    else if (name === 'assets')       loadAssets();
}

navItems.forEach(n => {
    n.addEventListener('click', e => {
        e.preventDefault();
        switchView(n.dataset.view);
    });
});

// ──────────────────────────────────────────────
// Health check
// ──────────────────────────────────────────────

async function checkHealth() {
    const el = document.getElementById('serverStatus');
    try {
        await api('/api/health');
        el.className = 'server-status online';
        el.querySelector('.status-text').textContent = t('serverOnline');
    } catch {
        el.className = 'server-status offline';
        el.querySelector('.status-text').textContent = t('serverOffline');
    }
}

// ──────────────────────────────────────────────
// Dashboard View
// ──────────────────────────────────────────────

async function refreshDashboard() {
    try {
        const [invRes, lowRes, txRes, txAllRes] = await Promise.all([
            api('/api/inventory').then(r => r.json()),
            api('/api/inventory/low-stock').then(r => r.json()),
            api('/api/transactions?limit=10').then(r => r.json()),
            api('/api/transactions?limit=500').then(r => r.json()),
        ]);

        const items = invRes.items || [];
        const lowItems = lowRes.items || [];
        const txRecords = txRes.records || [];

        // stats
        document.getElementById('statTotalItems').textContent = items.length;
        const totalQty = items.reduce((s, i) => s + (parseInt(i.quantity) || 0), 0);
        document.getElementById('statTotalQty').textContent = totalQty.toLocaleString();
        document.getElementById('statLowStock').textContent = lowItems.length;

        // today ops
        const today = todayStr();
        const todayOps = txRecords.filter(r => (r.timestamp || '').startsWith(today)).length;
        document.getElementById('statTodayOps').textContent = todayOps;

        // recent tx table
        renderRecentTxTable(txRecords);

        // low stock panel
        renderLowStockPanel(lowItems);

        // charts
        renderInvCategoryChart(items);
        renderTxTrendChart(txAllRes.records || []);
    } catch (e) {
        console.error('Dashboard refresh error:', e);
    }
}

function renderRecentTxTable(records) {
    const tbody = document.querySelector('#dashRecentTxTable tbody');
    const empty = document.getElementById('dashRecentTxEmpty');
    if (!records.length) {
        tbody.innerHTML = '';
        empty.style.display = '';
        return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = records.map(r => `
        <tr>
            <td>${esc(r.tx_id)}</td>
            <td>${esc(r.item_name)}</td>
            <td>${r.type === 'in'
                ? `<span class="badge badge-green">${t('badgeIn')}</span>`
                : `<span class="badge badge-red">${t('badgeOut')}</span>`}</td>
            <td>${esc(r.quantity)}</td>
            <td><strong>${r.balance_after != null ? esc(r.balance_after) : '—'}</strong></td>
            <td>${esc(r.operator)}</td>
            <td>${esc(r.timestamp)}</td>(items) {
    const panel = document.getElementById('dashLowStockList');
    if (!items.length) {
        panel.innerHTML = `<div class="empty-state">${t('noLowStock')}</div>`;
        return;
    }
    panel.innerHTML = items.map(i => `
        <div class="alert-item">
            <div>
                <span class="alert-item-name">${esc(i.name)}</span>
                <span class="alert-item-meta">（${t('alertMin')} ${esc(i.min_stock)}）</span>
            </div>
            <span class="alert-item-qty">${t('alertRemain')} ${esc(i.quantity)} ${esc(i.unit)}</span>
        </div>
    `).join('');
}

// ──────────────────────────────────────────────
// Inventory View
// ──────────────────────────────────────────────

let allInventoryItems = [];

async function loadInventory() {
    try {
        const [invRes, catRes] = await Promise.all([
            api('/api/inventory').then(r => r.json()),
            api('/api/inventory/categories').then(r => r.json()),
        ]);
        allInventoryItems = invRes.items || [];
        renderInventoryTable(allInventoryItems);

        // populate category filter
        const sel = document.getElementById('invCategoryFilter');
        const current = sel.value;
        sel.innerHTML = `<option value="">${t('optAllCategories')}</option>`;
        (catRes.categories || []).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            sel.appendChild(opt);
        });
        sel.value = current;
    } catch (e) {
        toast(t('loadInvFail') + ': ' + e.message, 'error');
    }
}

function renderInventoryTable(items) {
    const tbody = document.querySelector('#invTable tbody');
    const empty = document.getElementById('invEmpty');
    if (!items.length) {
        tbody.innerHTML = '';
        empty.style.display = '';
        return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = items.map(i => {
        const qty = parseInt(i.quantity) || 0;
        const min = parseInt(i.min_stock) || 0;
        let statusBadge;
        if (qty === 0) statusBadge = `<span class="badge badge-red">${t('badgeOutOfStock')}</span>`;
        else if (min > 0 && qty < min) statusBadge = `<span class="badge badge-yellow">${t('badgeLowStock')}</span>`;
        else statusBadge = `<span class="badge badge-green">${t('badgeNormal')}</span>`;

        return `<tr>
            <td>${esc(i.item_id)}</td>
            <td>${esc(i.name)}</td>
            <td>${esc(i.category)}</td>
            <td>${esc(i.quantity)}</td>
            <td>${esc(i.unit)}</td>
            <td>${esc(i.location)}</td>
            <td>${statusBadge}</td>
        </tr>`;
    }).join('');
}

// search + category filter
let searchTimer;
document.getElementById('invSearchInput').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(filterInventory, 300);
});
document.getElementById('invCategoryFilter').addEventListener('change', filterInventory);

async function filterInventory() {
    const q = document.getElementById('invSearchInput').value.trim();
    const cat = document.getElementById('invCategoryFilter').value;

    let items;
    if (q) {
        const res = await api(`/api/inventory/search?q=${encodeURIComponent(q)}`).then(r => r.json());
        items = res.items || [];
    } else {
        items = allInventoryItems;
    }

    if (cat) {
        items = items.filter(i => i.category === cat);
    }

    renderInventoryTable(items);
}

// ──────────────────────────────────────────────
// Create Item Modal
// ──────────────────────────────────────────────

function openCreateItemModal() {
    document.getElementById('createItemModal').classList.add('open');
}
function closeCreateItemModal() {
    document.getElementById('createItemModal').classList.remove('open');
}

async function submitCreateItem() {
    const name     = document.getElementById('newItemName').value.trim();
    const category = document.getElementById('newItemCategory').value.trim();
    const unit     = document.getElementById('newItemUnit').value.trim() || '个';
    const qty      = parseInt(document.getElementById('newItemQty').value) || 0;
    const minStock = parseInt(document.getElementById('newItemMinStock').value) || 0;
    const location = document.getElementById('newItemLocation').value.trim();

    if (!name || !category) {
        toast(t('validNameCat'), 'error');
        return;
    }

    // Use the AI agent to create the item
    const msg = `创建新商品：名称="${name}"，分类="${category}"，单位="${unit}"，初始数量=${qty}，最低库存=${minStock}，位置="${location}"`;
    try {
        const res = await api('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ message: msg }),
        }).then(r => r.json());

        toast(t('toastCreateSuccess'), 'success');
        closeCreateItemModal();
        // clear form
        ['newItemName', 'newItemCategory', 'newItemLocation'].forEach(id => document.getElementById(id).value = '');
        document.getElementById('newItemQty').value = '0';
        document.getElementById('newItemMinStock').value = '0';
        document.getElementById('newItemUnit').value = '个';
        loadInventory();
    } catch (e) {
        toast(t('toastCreateFail') + ': ' + e.message, 'error');
    }
}

// close modal on overlay click
document.getElementById('createItemModal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeCreateItemModal();
});

// ──────────────────────────────────────────────
// Transactions View
// ──────────────────────────────────────────────

async function loadTransactions() {
    const txType = document.getElementById('txTypeFilter').value;
    const dateFrom = document.getElementById('txDateFrom').value;
    const dateTo = document.getElementById('txDateTo').value;

    let url = '/api/transactions?limit=200';
    if (txType) url += `&type=${txType}`;

    try {
        const res = await api(url).then(r => r.json());
        let records = res.records || [];

        // client-side date filter
        if (dateFrom) records = records.filter(r => (r.timestamp || '') >= dateFrom);
        if (dateTo) records = records.filter(r => (r.timestamp || '').slice(0, 10) <= dateTo);

        renderTransactionsTable(records);
    } catch (e) {
        toast(t('loadTxFail') + ': ' + e.message, 'error');
    }
}

function renderTransactionsTable(records) {
    const tbody = document.querySelector('#txTable tbody');
    const empty = document.getElementById('txEmpty');
    if (!records.length) {
        tbody.innerHTML = '';
        empty.style.display = '';
        return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = records.map(r => `
        <tr>
            <td>${esc(r.tx_id)}</td>
            <td>${esc(r.item_name)}</td>
            <td>${r.type === 'in'
                ? `<span class="badge badge-green">${t('badgeIn')}</span>`
                : `<span class="badge badge-red">${t('badgeOut')}</span>`}</td>
            <td>${esc(r.quantity)}</td>
            <td><strong>${r.balance_after != null ? esc(r.balance_after) : '—'}</strong></td>
            <td>${esc(r.operator)}</td>
            <td>${esc(r.recipient) || '—'}</td>
            <td>${esc(r.timestamp)}</td>
        </tr>
    `).join('');
}

// ──────────────────────────────────────────────
// Export Reports
// ──────────────────────────────────────────────

async function exportReport(type) {
    toast(t('toastGenerating'), 'info');
    try {
        const res = await fetch('/api/report/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || t('toastExportFail'));
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const disposition = res.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?(.+?)"?$/);
        a.download = match ? match[1] : `${type}_report.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        toast(t('toastDownloaded'), 'success');
    } catch (e) {
        toast(t('toastExportFail') + ': ' + e.message, 'error');
    }
}

// ──────────────────────────────────────────────
// Assets View
// ──────────────────────────────────────────────

let allAssets = [];

async function loadAssets() {
    try {
        const [assetRes, catRes, summaryRes] = await Promise.all([
            api('/api/assets').then(r => r.json()),
            api('/api/assets/categories').then(r => r.json()),
            api('/api/assets/summary').then(r => r.json()),
        ]);
        allAssets = assetRes.assets || [];
        cacheAssets(allAssets);
        renderAssetTable(allAssets);

        // stats
        const s = summaryRes;
        document.getElementById('statAssetTotal').textContent = s.total || 0;
        document.getElementById('statAssetInUse').textContent = (s.by_status && s.by_status['在用']) || 0;
        document.getElementById('statAssetIdle').textContent = (s.by_status && s.by_status['闲置']) || 0;
        const other = Object.entries(s.by_status || {})
            .filter(([k]) => !['在用', '闲置'].includes(k))
            .reduce((sum, [, v]) => sum + v, 0);
        document.getElementById('statAssetOther').textContent = other;

        // category filter
        const sel = document.getElementById('assetCategoryFilter');
        const current = sel.value;
        sel.innerHTML = `<option value="">${t('optAllCategories')}</option>`;
        (catRes.categories || []).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c; opt.textContent = c;
            sel.appendChild(opt);
        });
        sel.value = current;

        // charts
        renderAssetCategoryChart(summaryRes);
        renderAssetStatusChart(summaryRes);
    } catch (e) {
        toast(t('loadAssetFail') + ': ' + e.message, 'error');
    }
}

const STATUS_BADGE = {
    '在用':  'badge-green',
    '闲置':  'badge-blue',
    '维修':  'badge-yellow',
    '借出':  'badge-orange',
    '报废':  'badge-red',
};

function fmtDate(v) {
    if (!v) return '—';
    const s = String(v).slice(0, 10);
    return s === 'None' || s === '' ? '—' : s;
}

function renderAssetTable(assets) {
    const tbody = document.querySelector('#assetTable tbody');
    const empty = document.getElementById('assetEmpty');
    if (!assets.length) {
        tbody.innerHTML = '';
        empty.style.display = '';
        return;
    }
    empty.style.display = 'none';
    tbody.innerHTML = assets.map(a => {
        const cls = STATUS_BADGE[a.status] || 'badge-gray';
        return `<tr>
            <td>${esc(a.asset_id)}</td>
            <td title="${esc(a.name)}">${esc((a.name || '').slice(0, 30))}</td>
            <td>${esc(a.category)}</td>
            <td>${esc(a.model)}</td>
            <td title="${esc(a.serial_number)}">${esc((a.serial_number || '').slice(0, 15))}</td>
            <td><span class="badge ${cls}">${esc(a.status)}</span></td>
            <td>${esc(a.assigned_to || a.custodian || '—')}</td>
            <td>${esc(a.location_detail || a.building || '—')}</td>
            <td>${fmtDate(a.start_date)}</td>
            <td>${esc(a.asset_age || '—')}</td>
            <td>${esc(a.map_aging || '—')}</td>
            <td>${fmtDate(a.dispose_date)}</td>
            <td><button class="btn btn-ghost btn-sm" onclick="openEditAssetModal('${esc(a.asset_id)}')">✏️</button></td>
        </tr>`;
    }).join('');
}

// Asset search and filters
let assetSearchTimer;
document.getElementById('assetSearchInput').addEventListener('input', () => {
    clearTimeout(assetSearchTimer);
    assetSearchTimer = setTimeout(filterAssets, 300);
});
document.getElementById('assetCategoryFilter').addEventListener('change', filterAssets);
document.getElementById('assetStatusFilter').addEventListener('change', filterAssets);

async function filterAssets() {
    const q = document.getElementById('assetSearchInput').value.trim();
    const cat = document.getElementById('assetCategoryFilter').value;
    const status = document.getElementById('assetStatusFilter').value;

    let items;
    if (q) {
        const res = await api(`/api/assets/search?q=${encodeURIComponent(q)}`).then(r => r.json());
        items = res.assets || [];
    } else {
        items = allAssets;
    }
    if (cat) items = items.filter(a => a.category === cat);
    if (status) items = items.filter(a => a.status === status);
    renderAssetTable(items);
}

// ──────────────────────────────────────────────
// SAP Import Modal
// ──────────────────────────────────────────────

let sapSelectedFile = null;

function openSapImportModal() {
    document.getElementById('sapImportModal').classList.add('open');
    document.getElementById('sapImportResult').style.display = 'none';
    document.getElementById('sapFileName').style.display = 'none';
    sapSelectedFile = null;
    document.getElementById('sapImportBtn').disabled = true;
}
function closeSapImportModal() {
    document.getElementById('sapImportModal').classList.remove('open');
}

function handleSapFileSelect() {
    const input = document.getElementById('sapFileInput');
    if (input.files.length) {
        sapSelectedFile = input.files[0];
        document.getElementById('sapFileName').textContent = '📎 ' + sapSelectedFile.name;
        document.getElementById('sapFileName').style.display = '';
        document.getElementById('sapImportBtn').disabled = false;
    }
}

// drag & drop
const sapDrop = document.getElementById('sapDropZone');
if (sapDrop) {
    sapDrop.addEventListener('dragover', e => { e.preventDefault(); sapDrop.classList.add('drag-over'); });
    sapDrop.addEventListener('dragleave', () => sapDrop.classList.remove('drag-over'));
    sapDrop.addEventListener('drop', e => {
        e.preventDefault();
        sapDrop.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            sapSelectedFile = e.dataTransfer.files[0];
            document.getElementById('sapFileName').textContent = '📎 ' + sapSelectedFile.name;
            document.getElementById('sapFileName').style.display = '';
            document.getElementById('sapImportBtn').disabled = false;
        }
    });
    sapDrop.addEventListener('click', () => document.getElementById('sapFileInput').click());
}

document.getElementById('sapImportModal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeSapImportModal();
});

async function submitSapImport() {
    if (!sapSelectedFile) return;
    const btn = document.getElementById('sapImportBtn');
    btn.disabled = true;
    btn.textContent = t('btnImporting');

    const form = new FormData();
    form.append('file', sapSelectedFile);

    try {
        const res = await fetch('/api/assets/import-sap', { method: 'POST', body: form });
        const data = await res.json();
        const resultEl = document.getElementById('sapImportResult');
        resultEl.style.display = '';

        if (data.success > 0) {
            resultEl.innerHTML = `
                <div class="import-result success">
                    ✅ ${t('sapSuccess')} <strong>${data.success}</strong> ${t('sapItems')}
                    ${data.skipped ? `，${t('sapSkipped')} ${data.skipped} ${t('sapSkippedReason')}` : ''}
                    ${data.errors.length ? `<br>⚠️ ${data.errors.length} ${t('sapErrors')}` : ''}
                </div>`;
            toast(`${t('toastImported')} ${data.success} ${t('sapItems')}`, 'success');
            loadAssets();
        } else {
            resultEl.innerHTML = `<div class="import-result error">❌ ${t('sapFail')}：${data.errors.join('; ')}</div>`;
            toast(t('toastImportFail'), 'error');
        }
    } catch (e) {
        toast(t('toastImportFail') + ': ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = t('btnStartImport');
    }
}

// ──────────────────────────────────────────────
// Chat View
// ──────────────────────────────────────────────

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');

chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
});

function sendSuggestion(chip) {
    chatInput.value = chip.textContent;
    sendChatMessage();
}

async function sendChatMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    // remove welcome
    const welcome = chatMessages.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    appendMsg('user', msg);
    chatInput.value = '';
    chatSendBtn.disabled = true;

    // loading indicator
    const loadingEl = appendMsg('agent', t('chatThinking'), true);

    try {
        const res = await api('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ message: msg }),
        }).then(r => r.json());

        loadingEl.remove();

        // show tool calls if any
        if (res.tool_calls && res.tool_calls.length) {
            res.tool_calls.forEach((tc, idx) => {
                const result = (res.tool_results && res.tool_results[idx]) || '';
                appendToolCall(tc, result);
            });
        }

        appendMsg('agent', res.reply);
    } catch (e) {
        loadingEl.remove();
        appendMsg('agent', t('chatError') + ': ' + e.message);
    } finally {
        chatSendBtn.disabled = false;
        chatInput.focus();
    }
}

function appendMsg(role, text, loading = false) {
    const div = document.createElement('div');
    div.className = `msg msg-${role}` + (loading ? ' msg-loading' : '');

    const avatar = role === 'user' ? '👤' : '🤖';
    div.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-bubble">${esc(text)}</div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
}

function appendToolCall(tc, result) {
    const div = document.createElement('div');
    div.className = 'tool-call-indicator';
    const name = typeof tc === 'string' ? tc : (tc.name || tc.function?.name || 'tool');
    div.innerHTML = `<span class="tool-icon">⚙️</span> ${t('toolCallLabel')}: <strong>${esc(name)}</strong>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function clearChat() {
    try {
        await api('/api/chat/clear', { method: 'POST' });
        chatMessages.innerHTML = `
            <div class="chat-welcome">
                <div class="chat-welcome-icon">🤖</div>
                <h3 data-i18n="chatWelcomeTitle">${t('chatWelcomeTitle')}</h3>
                <p data-i18n="chatWelcomeDesc">${t('chatWelcomeDesc')}</p>
                <div class="chat-suggestions">
                    <button class="suggestion-chip" data-i18n="chipViewAll" onclick="sendSuggestion(this)">${t('chipViewAll')}</button>
                    <button class="suggestion-chip" data-i18n="chipStockIn" onclick="sendSuggestion(this)">${t('chipStockIn')}</button>
                    <button class="suggestion-chip" data-i18n="chipLowStock" onclick="sendSuggestion(this)">${t('chipLowStock')}</button>
                    <button class="suggestion-chip" data-i18n="chipExport" onclick="sendSuggestion(this)">${t('chipExport')}</button>
                </div>
            </div>`;
        toast(t('chatCleared'), 'success');
    } catch (e) {
        toast(t('chatClearFail') + ': ' + e.message, 'error');
    }
}

// ──────────────────────────────────────────────
// Asset Edit Modal
// ──────────────────────────────────────────────

let _allAssets = [];

function cacheAssets(list) { _allAssets = list; }

function openEditAssetModal(assetId) {
    const a = _allAssets.find(x => x.asset_id === assetId);
    if (!a) return;
    document.getElementById('editAssetId').value = a.asset_id;
    document.getElementById('editAssignee').value = a.assigned_to || a.custodian || '';
    document.getElementById('editBuilding').value = a.building || '';
    document.getElementById('editRoom').value = a.room || '';
    document.getElementById('editLocationDetail').value = a.location_detail || '';
    document.getElementById('editStartDate').value = (a.start_date || '').slice(0, 10) || '';
    document.getElementById('editDisposeDate').value = (a.dispose_date || '').slice(0, 10) || '';
    document.getElementById('editNotes').value = a.notes || '';
    document.getElementById('editAssetModal').classList.add('active');
    applyI18n();
}

function closeEditAssetModal() {
    document.getElementById('editAssetModal').classList.remove('active');
}

async function submitEditAsset() {
    const id = document.getElementById('editAssetId').value;
    const payload = {
        assigned_to: document.getElementById('editAssignee').value,
        building: document.getElementById('editBuilding').value,
        room: document.getElementById('editRoom').value,
        location_detail: document.getElementById('editLocationDetail').value,
        start_date: document.getElementById('editStartDate').value,
        dispose_date: document.getElementById('editDisposeDate').value,
        notes: document.getElementById('editNotes').value
    };
    try {
        await api(`/api/assets/${encodeURIComponent(id)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        toast(t('toastUpdateSuccess'), 'success');
        closeEditAssetModal();
        loadAssets();
    } catch (e) {
        toast(t('toastUpdateFail') + ': ' + e.message, 'error');
    }
}

// ──────────────────────────────────────────────
// Init
// ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    applyI18n();
    checkHealth();
    refreshDashboard();
    setInterval(checkHealth, 30000);
});
