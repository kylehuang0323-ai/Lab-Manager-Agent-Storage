/* ==========================================================
   Lab Manager — Chart.js Visualizations
   Glassmorphism palette + neon glow theme
   ========================================================== */

const CHART_COLORS = [
    'rgba(99,102,241,.85)',   // indigo
    'rgba(52,211,153,.85)',   // emerald
    'rgba(251,191,36,.85)',   // amber
    'rgba(248,113,113,.85)',  // rose
    'rgba(96,165,250,.85)',   // sky
    'rgba(251,146,60,.85)',   // orange
    'rgba(167,139,250,.85)',  // violet
    'rgba(45,212,191,.85)',   // teal
    'rgba(244,114,182,.85)',  // pink
    'rgba(163,230,53,.85)',   // lime
];

const CHART_BORDERS = CHART_COLORS.map(c => c.replace(',.85)', ',1)'));

const GLOW_COLORS = [
    'rgba(99,102,241,.25)',
    'rgba(52,211,153,.25)',
    'rgba(251,191,36,.25)',
    'rgba(248,113,113,.25)',
    'rgba(96,165,250,.25)',
    'rgba(251,146,60,.25)',
    'rgba(167,139,250,.25)',
    'rgba(45,212,191,.25)',
    'rgba(244,114,182,.25)',
    'rgba(163,230,53,.25)',
];

// Shared defaults for dark glassmorphism look
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(80,110,180,.12)';
Chart.defaults.font.family = "'Inter', -apple-system, 'Segoe UI', sans-serif";

// Track chart instances for cleanup
const _charts = {};

function destroyChart(id) {
    if (_charts[id]) { _charts[id].destroy(); delete _charts[id]; }
}

// ──────────────────────────────────────────────
// 1. Inventory Category Doughnut
// ──────────────────────────────────────────────
function renderInvCategoryChart(items) {
    destroyChart('invCat');
    const canvas = document.getElementById('chartInvCategory');
    if (!canvas || !items.length) return;

    const catMap = {};
    items.forEach(i => {
        const c = i.category || '未分类';
        catMap[c] = (catMap[c] || 0) + (parseInt(i.quantity) || 0);
    });
    const labels = Object.keys(catMap);
    const data = Object.values(catMap);

    _charts['invCat'] = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: CHART_COLORS.slice(0, labels.length),
                borderColor: 'rgba(8,12,30,.6)',
                borderWidth: 2,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '62%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { padding: 14, usePointStyle: true, pointStyleWidth: 10, font: { size: 12 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(17,25,50,.9)',
                    borderColor: 'rgba(99,102,241,.3)',
                    borderWidth: 1,
                    titleFont: { weight: 600 },
                    padding: 10,
                    cornerRadius: 8,
                }
            }
        }
    });
}

// ──────────────────────────────────────────────
// 2. Transaction Trend Line Chart (last 7 days)
// ──────────────────────────────────────────────
function renderTxTrendChart(records) {
    destroyChart('txTrend');
    const canvas = document.getElementById('chartTxTrend');
    if (!canvas) return;

    // Build last 7 days
    const days = [];
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        days.push(d.toISOString().slice(0, 10));
    }

    const inMap = {}, outMap = {};
    days.forEach(d => { inMap[d] = 0; outMap[d] = 0; });
    (records || []).forEach(r => {
        const day = (r.timestamp || '').slice(0, 10);
        if (inMap[day] !== undefined) {
            if (r.type === 'in') inMap[day] += parseInt(r.quantity) || 0;
            else outMap[day] += parseInt(r.quantity) || 0;
        }
    });

    const labels = days.map(d => d.slice(5)); // MM-DD

    _charts['txTrend'] = new Chart(canvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: typeof t === 'function' ? t('badgeIn') : '入库',
                    data: days.map(d => inMap[d]),
                    borderColor: 'rgba(52,211,153,1)',
                    backgroundColor: 'rgba(52,211,153,.1)',
                    fill: true,
                    tension: .4,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    pointBackgroundColor: 'rgba(52,211,153,1)',
                    pointBorderColor: 'rgba(8,12,30,.8)',
                    pointBorderWidth: 2,
                    borderWidth: 2.5,
                },
                {
                    label: typeof t === 'function' ? t('badgeOut') : '出库',
                    data: days.map(d => outMap[d]),
                    borderColor: 'rgba(248,113,113,1)',
                    backgroundColor: 'rgba(248,113,113,.1)',
                    fill: true,
                    tension: .4,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    pointBackgroundColor: 'rgba(248,113,113,1)',
                    pointBorderColor: 'rgba(8,12,30,.8)',
                    pointBorderWidth: 2,
                    borderWidth: 2.5,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: {
                    grid: { color: 'rgba(80,110,180,.08)' },
                    ticks: { font: { size: 11 } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(80,110,180,.08)' },
                    ticks: { precision: 0, font: { size: 11 } }
                }
            },
            plugins: {
                legend: {
                    labels: { padding: 16, usePointStyle: true, pointStyleWidth: 10, font: { size: 12 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(17,25,50,.9)',
                    borderColor: 'rgba(99,102,241,.3)',
                    borderWidth: 1,
                    padding: 10,
                    cornerRadius: 8,
                }
            }
        }
    });
}

// ──────────────────────────────────────────────
// 3. Asset Category Doughnut
// ──────────────────────────────────────────────
function renderAssetCategoryChart(summary) {
    destroyChart('assetCat');
    const canvas = document.getElementById('chartAssetCategory');
    if (!canvas || !summary || !summary.by_category) return;

    const labels = Object.keys(summary.by_category);
    const data = Object.values(summary.by_category);

    _charts['assetCat'] = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: CHART_COLORS.slice(0, labels.length),
                borderColor: 'rgba(8,12,30,.6)',
                borderWidth: 2,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '62%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { padding: 14, usePointStyle: true, pointStyleWidth: 10, font: { size: 12 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(17,25,50,.9)',
                    borderColor: 'rgba(99,102,241,.3)',
                    borderWidth: 1,
                    padding: 10,
                    cornerRadius: 8,
                }
            }
        }
    });
}

// ──────────────────────────────────────────────
// 4. Asset Status Horizontal Bar
// ──────────────────────────────────────────────
function renderAssetStatusChart(summary) {
    destroyChart('assetStatus');
    const canvas = document.getElementById('chartAssetStatus');
    if (!canvas || !summary || !summary.by_status) return;

    const labels = Object.keys(summary.by_status);
    const data = Object.values(summary.by_status);

    const statusColors = {
        '在用': 'rgba(52,211,153,.8)',
        '闲置': 'rgba(96,165,250,.8)',
        '维修': 'rgba(251,191,36,.8)',
        '借出': 'rgba(251,146,60,.8)',
        '报废': 'rgba(248,113,113,.8)',
    };
    const bgColors = labels.map((l, i) => statusColors[l] || CHART_COLORS[i % CHART_COLORS.length]);
    const glowBg = bgColors.map(c => c.replace(',.8)', ',.15)'));

    _charts['assetStatus'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: bgColors,
                borderColor: bgColors.map(c => c.replace(',.8)', ',1)')),
                borderWidth: 1,
                borderRadius: 6,
                borderSkipped: false,
                hoverBackgroundColor: bgColors.map(c => c.replace(',.8)', ',.95)')),
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: 'rgba(80,110,180,.08)' },
                    ticks: { precision: 0, font: { size: 11 } }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 12, weight: 500 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17,25,50,.9)',
                    borderColor: 'rgba(99,102,241,.3)',
                    borderWidth: 1,
                    padding: 10,
                    cornerRadius: 8,
                }
            }
        }
    });
}
