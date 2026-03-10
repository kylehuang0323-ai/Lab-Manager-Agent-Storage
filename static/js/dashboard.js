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
        el.querySelector('.status-text').textContent = '服务运行中';
    } catch {
        el.className = 'server-status offline';
        el.querySelector('.status-text').textContent = '连接失败';
    }
}

// ──────────────────────────────────────────────
// Dashboard View
// ──────────────────────────────────────────────

async function refreshDashboard() {
    try {
        const [invRes, lowRes, txRes] = await Promise.all([
            api('/api/inventory').then(r => r.json()),
            api('/api/inventory/low-stock').then(r => r.json()),
            api('/api/transactions?limit=10').then(r => r.json()),
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
                ? '<span class="badge badge-green">入库</span>'
                : '<span class="badge badge-red">出库</span>'}</td>
            <td>${esc(r.quantity)}</td>
            <td>${esc(r.operator)}</td>
            <td>${esc(r.timestamp)}</td>
        </tr>
    `).join('');
}

function renderLowStockPanel(items) {
    const panel = document.getElementById('dashLowStockList');
    if (!items.length) {
        panel.innerHTML = '<div class="empty-state">✅ 暂无低库存告警</div>';
        return;
    }
    panel.innerHTML = items.map(i => `
        <div class="alert-item">
            <div>
                <span class="alert-item-name">${esc(i.name)}</span>
                <span class="alert-item-meta">（最低 ${esc(i.min_stock)}）</span>
            </div>
            <span class="alert-item-qty">剩余 ${esc(i.quantity)} ${esc(i.unit)}</span>
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
        sel.innerHTML = '<option value="">全部分类</option>';
        (catRes.categories || []).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            sel.appendChild(opt);
        });
        sel.value = current;
    } catch (e) {
        toast('加载库存失败: ' + e.message, 'error');
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
        if (qty === 0) statusBadge = '<span class="badge badge-red">缺货</span>';
        else if (min > 0 && qty < min) statusBadge = '<span class="badge badge-yellow">低库存</span>';
        else statusBadge = '<span class="badge badge-green">正常</span>';

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
        toast('请填写名称和分类', 'error');
        return;
    }

    // Use the AI agent to create the item
    const msg = `创建新商品：名称="${name}"，分类="${category}"，单位="${unit}"，初始数量=${qty}，最低库存=${minStock}，位置="${location}"`;
    try {
        const res = await api('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ message: msg }),
        }).then(r => r.json());

        toast('商品创建成功', 'success');
        closeCreateItemModal();
        // clear form
        ['newItemName', 'newItemCategory', 'newItemLocation'].forEach(id => document.getElementById(id).value = '');
        document.getElementById('newItemQty').value = '0';
        document.getElementById('newItemMinStock').value = '0';
        document.getElementById('newItemUnit').value = '个';
        loadInventory();
    } catch (e) {
        toast('创建失败: ' + e.message, 'error');
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
        toast('加载记录失败: ' + e.message, 'error');
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
                ? '<span class="badge badge-green">入库</span>'
                : '<span class="badge badge-red">出库</span>'}</td>
            <td>${esc(r.quantity)}</td>
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
    toast('正在生成报表…', 'info');
    try {
        const res = await fetch('/api/report/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || '导出失败');
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
        toast('报表已下载', 'success');
    } catch (e) {
        toast('导出失败: ' + e.message, 'error');
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
    const loadingEl = appendMsg('agent', '思考中…', true);

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
        appendMsg('agent', '❌ 请求失败: ' + e.message);
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
    div.innerHTML = `<span class="tool-icon">⚙️</span> 调用工具: <strong>${esc(name)}</strong>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function clearChat() {
    try {
        await api('/api/chat/clear', { method: 'POST' });
        chatMessages.innerHTML = `
            <div class="chat-welcome">
                <div class="chat-welcome-icon">🤖</div>
                <h3>你好，我是 Lab Manager AI 助手</h3>
                <p>你可以用自然语言来管理库存，例如：</p>
                <div class="chat-suggestions">
                    <button class="suggestion-chip" onclick="sendSuggestion(this)">查看所有库存</button>
                    <button class="suggestion-chip" onclick="sendSuggestion(this)">入库 50 个鼠标</button>
                    <button class="suggestion-chip" onclick="sendSuggestion(this)">哪些商品库存不足？</button>
                    <button class="suggestion-chip" onclick="sendSuggestion(this)">导出库存报表</button>
                </div>
            </div>`;
        toast('对话已清除', 'success');
    } catch (e) {
        toast('清除失败: ' + e.message, 'error');
    }
}

// ──────────────────────────────────────────────
// Init
// ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    refreshDashboard();
    setInterval(checkHealth, 30000);
});
