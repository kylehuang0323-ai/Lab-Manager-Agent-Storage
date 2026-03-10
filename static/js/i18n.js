/* ==========================================================
   Lab Manager — i18n (Internationalization)
   Bilingual: 中文 (zh) / English (en)
   ========================================================== */

const I18N = {
    zh: {
        // Page title
        pageTitle: 'Lab Manager — 智能库存管理',

        // Sidebar
        navDashboard: '仪表盘',
        navInventory: '库存管理',
        navTransactions: '出入库记录',
        navAssets: '资产管理',
        navChat: 'AI 助手',
        serverOnline: '服务运行中',
        serverOffline: '连接失败',
        serverConnecting: '连接中…',

        // Dashboard
        dashTitle: '仪表盘',
        btnRefresh: '🔄 刷新',
        statTotalItems: '总商品种类',
        statTotalQty: '总库存数量',
        statLowStock: '低库存告警数',
        statTodayOps: '今日操作数',
        panelRecentTx: '📋 最近出入库记录',
        panelLowStock: '⚠️ 低库存告警',
        thTxId: '流水号',
        thItem: '商品',
        thType: '类型',
        thQty: '数量',
        thOperator: '操作人',
        thTime: '时间',
        emptyRecords: '暂无记录',
        noLowStock: '✅ 暂无低库存告警',
        alertMin: '最低',
        alertRemain: '剩余',
        badgeIn: '入库',
        badgeOut: '出库',

        // Inventory
        invTitle: '库存管理',
        btnNewItem: '＋ 新建商品',
        btnExportReport: '📥 导出报表',
        phSearchInv: '搜索名称 / 分类 / 位置…',
        optAllCategories: '全部分类',
        thId: '编号',
        thName: '名称',
        thCategory: '分类',
        thUnit: '单位',
        thLocation: '位置',
        thStatus: '状态',
        badgeOutOfStock: '缺货',
        badgeLowStock: '低库存',
        badgeNormal: '正常',
        emptyInventory: '暂无库存数据',
        loadInvFail: '加载库存失败',

        // Transactions
        txTitle: '出入库记录',
        btnExportTx: '📥 导出流水',
        optAllTypes: '全部类型',
        optIn: '入库',
        optOut: '出库',
        btnQuery: '查询',
        thRecipient: '领用人',
        emptyTx: '暂无出入库记录',
        loadTxFail: '加载记录失败',

        // Assets
        assetTitle: '资产管理',
        btnImportSap: '📤 导入 SAP 报表',
        statAssetTotal: '资产总数',
        statInUse: '在用',
        statIdle: '闲置',
        statOther: '维修/借出/报废',
        phSearchAsset: '搜索名称 / 编号 / SN / 使用人…',
        optAllStatus: '全部状态',
        statusInUse: '在用',
        statusIdle: '闲置',
        statusRepair: '维修',
        statusLent: '借出',
        statusDisposed: '报废',
        thAssetId: '资产ID',
        thModel: '型号',
        thSN: 'SN',
        thAssignee: '使用人',
        emptyAssets: '暂无资产数据，请先导入 SAP 报表',
        loadAssetFail: '加载资产失败',

        // Create Item Modal
        modalNewItem: '新建商品',
        lblItemName: '商品名称',
        phItemName: '例如：USB-C 数据线',
        lblCategory: '分类',
        phCategory: '例如：数据线',
        lblUnit: '单位',
        lblInitQty: '初始数量',
        lblMinStock: '最低库存',
        lblLocation: '存放位置',
        phLocation: '例如：A 区-柜 3',
        btnCancel: '取消',
        btnCreate: '创建',
        toastCreateSuccess: '商品创建成功',
        toastCreateFail: '创建失败',
        validNameCat: '请填写名称和分类',

        // SAP Import Modal
        modalSapImport: '📤 导入 SAP 固资报表',
        sapImportDesc: '上传从 SAP 导出的固资明细 Excel 文件（.xlsx），系统将自动识别格式并导入。',
        sapDropText: '拖拽文件到此处 或',
        sapBrowse: '浏览文件',
        btnStartImport: '开始导入',
        btnImporting: '导入中…',
        sapSuccess: '成功导入',
        sapItems: '项资产',
        sapSkipped: '跳过',
        sapSkippedReason: '项（已存在/空行）',
        sapErrors: '项错误',
        sapFail: '导入失败',
        toastImported: '已导入',
        toastImportFail: '导入失败',

        // Chat
        chatTitle: 'AI 助手',
        btnClearChat: '🗑️ 清除对话',
        chatWelcomeTitle: '你好，我是 Lab Manager AI 助手',
        chatWelcomeDesc: '你可以用自然语言来管理库存，例如：',
        chipViewAll: '查看所有库存',
        chipStockIn: '入库 50 个鼠标',
        chipLowStock: '哪些商品库存不足？',
        chipExport: '导出库存报表',
        phChatInput: '输入指令，如：入库 50 个鼠标…',
        btnSend: '发送',
        chatThinking: '思考中…',
        chatError: '❌ 请求失败',
        chatCleared: '对话已清除',
        chatClearFail: '清除失败',
        toolCallLabel: '调用工具',

        // Report export
        toastGenerating: '正在生成报表…',
        toastDownloaded: '报表已下载',
        toastExportFail: '导出失败',

        // Language
        langLabel: '🌐 中/EN',
    },

    en: {
        pageTitle: 'Lab Manager — Smart Inventory',

        navDashboard: 'Dashboard',
        navInventory: 'Inventory',
        navTransactions: 'Transactions',
        navAssets: 'Assets',
        navChat: 'AI Chat',
        serverOnline: 'Server Online',
        serverOffline: 'Connection Failed',
        serverConnecting: 'Connecting…',

        dashTitle: 'Dashboard',
        btnRefresh: '🔄 Refresh',
        statTotalItems: 'Item Types',
        statTotalQty: 'Total Stock',
        statLowStock: 'Low Stock Alerts',
        statTodayOps: "Today's Ops",
        panelRecentTx: '📋 Recent Transactions',
        panelLowStock: '⚠️ Low Stock Alerts',
        thTxId: 'TX ID',
        thItem: 'Item',
        thType: 'Type',
        thQty: 'Qty',
        thOperator: 'Operator',
        thTime: 'Time',
        emptyRecords: 'No records',
        noLowStock: '✅ No low stock alerts',
        alertMin: 'Min',
        alertRemain: 'Remaining',
        badgeIn: 'In',
        badgeOut: 'Out',

        invTitle: 'Inventory',
        btnNewItem: '＋ New Item',
        btnExportReport: '📥 Export Report',
        phSearchInv: 'Search name / category / location…',
        optAllCategories: 'All Categories',
        thId: 'ID',
        thName: 'Name',
        thCategory: 'Category',
        thUnit: 'Unit',
        thLocation: 'Location',
        thStatus: 'Status',
        badgeOutOfStock: 'Out of Stock',
        badgeLowStock: 'Low Stock',
        badgeNormal: 'Normal',
        emptyInventory: 'No inventory data',
        loadInvFail: 'Failed to load inventory',

        txTitle: 'Transactions',
        btnExportTx: '📥 Export Transactions',
        optAllTypes: 'All Types',
        optIn: 'Stock In',
        optOut: 'Stock Out',
        btnQuery: 'Search',
        thRecipient: 'Recipient',
        emptyTx: 'No transaction records',
        loadTxFail: 'Failed to load records',

        assetTitle: 'Asset Management',
        btnImportSap: '📤 Import SAP Report',
        statAssetTotal: 'Total Assets',
        statInUse: 'In Use',
        statIdle: 'Idle',
        statOther: 'Repair/Lent/Disposed',
        phSearchAsset: 'Search name / ID / SN / assignee…',
        optAllStatus: 'All Status',
        statusInUse: 'In Use',
        statusIdle: 'Idle',
        statusRepair: 'Repair',
        statusLent: 'Lent',
        statusDisposed: 'Disposed',
        thAssetId: 'Asset ID',
        thModel: 'Model',
        thSN: 'SN',
        thAssignee: 'Assignee',
        emptyAssets: 'No assets. Please import a SAP report first.',
        loadAssetFail: 'Failed to load assets',

        modalNewItem: 'New Item',
        lblItemName: 'Item Name',
        phItemName: 'e.g. USB-C Cable',
        lblCategory: 'Category',
        phCategory: 'e.g. Cable',
        lblUnit: 'Unit',
        lblInitQty: 'Initial Qty',
        lblMinStock: 'Min Stock',
        lblLocation: 'Location',
        phLocation: 'e.g. Zone A - Shelf 3',
        btnCancel: 'Cancel',
        btnCreate: 'Create',
        toastCreateSuccess: 'Item created',
        toastCreateFail: 'Create failed',
        validNameCat: 'Name and category are required',

        modalSapImport: '📤 Import SAP Fixed Asset Report',
        sapImportDesc: 'Upload the SAP fixed asset detail Excel file (.xlsx). The system will auto-detect the format.',
        sapDropText: 'Drop file here or',
        sapBrowse: 'Browse',
        btnStartImport: 'Start Import',
        btnImporting: 'Importing…',
        sapSuccess: 'Successfully imported',
        sapItems: 'assets',
        sapSkipped: 'skipped',
        sapSkippedReason: '(existing/empty)',
        sapErrors: 'errors',
        sapFail: 'Import failed',
        toastImported: 'Imported',
        toastImportFail: 'Import failed',

        chatTitle: 'AI Chat',
        btnClearChat: '🗑️ Clear Chat',
        chatWelcomeTitle: "Hi, I'm the Lab Manager AI Assistant",
        chatWelcomeDesc: 'You can manage inventory using natural language, e.g.:',
        chipViewAll: 'View all inventory',
        chipStockIn: 'Stock in 50 mice',
        chipLowStock: 'Which items are low stock?',
        chipExport: 'Export inventory report',
        phChatInput: 'Type a command, e.g. stock in 50 mice…',
        btnSend: 'Send',
        chatThinking: 'Thinking…',
        chatError: '❌ Request failed',
        chatCleared: 'Chat cleared',
        chatClearFail: 'Clear failed',
        toolCallLabel: 'Tool call',

        toastGenerating: 'Generating report…',
        toastDownloaded: 'Report downloaded',
        toastExportFail: 'Export failed',

        langLabel: '🌐 中/EN',
    },
};

// ──────────────────────────────────────────────
// i18n Engine
// ──────────────────────────────────────────────

let currentLang = localStorage.getItem('labmgr_lang') || 'zh';

function t(key) {
    return (I18N[currentLang] && I18N[currentLang][key]) || (I18N.zh[key]) || key;
}

function applyI18n() {
    document.title = t('pageTitle');
    document.documentElement.lang = currentLang === 'zh' ? 'zh-CN' : 'en';

    // All elements with data-i18n attribute: set textContent
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.dataset.i18n);
    });
    // Placeholders
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        el.placeholder = t(el.dataset.i18nPh);
    });
    // innerHTML (for elements with emoji + text)
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        el.innerHTML = t(el.dataset.i18nHtml);
    });

    // Update language toggle button text
    const langBtn = document.getElementById('langToggleBtn');
    if (langBtn) {
        langBtn.textContent = currentLang === 'zh' ? '🌐 EN' : '🌐 中文';
    }
}

function toggleLang() {
    currentLang = currentLang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('labmgr_lang', currentLang);
    applyI18n();
}
