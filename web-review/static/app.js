/**
 * Maliki Fiqh Masail Review — Single Page App
 */

const $ = (sel) => document.querySelector(sel);
const app = $('#app');
const breadcrumbEl = $('#breadcrumb');

// ===== Helpers =====

const RESULT_LABELS = {
    ittifaq: 'اتفاق',
    ikhtilaf: 'اختلاف',
    tafsilat: 'تفصيل',
};

const HUKM_LABELS = {
    wajib: 'واجب',
    mandub: 'مندوب',
    mubah: 'مباح',
    makruh: 'مكروه',
    haram: 'حرام',
};

function hukmBadge(hukm) {
    if (!hukm) return '<span class="badge badge-none">غير محدد</span>';
    const label = HUKM_LABELS[hukm] || hukm;
    const cls = HUKM_LABELS[hukm] ? `badge-${hukm}` : 'badge-none';
    return `<span class="badge ${cls}">${label}</span>`;
}

function resultBadge(result) {
    if (!result) return '';
    const label = RESULT_LABELS[result] || result;
    return `<span class="badge badge-${result}">${label}</span>`;
}

// Dynamic API — fetches from FastAPI backend
async function api(path) {
    const res = await fetch(path);
    return res.json();
}

function setBreadcrumb(items) {
    if (!items || items.length === 0) {
        breadcrumbEl.style.display = 'none';
        return;
    }
    breadcrumbEl.style.display = 'block';
    breadcrumbEl.innerHTML = items.map((item, i) => {
        if (i === items.length - 1) return `<span>${item.label}</span>`;
        return `<a href="${item.href}">${item.label}</a><span class="sep">/</span>`;
    }).join('');
}

function setActiveNav(id) {
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
}

// Review state from localStorage
function getReview(masalaKey) {
    try {
        const data = JSON.parse(localStorage.getItem('fiqh-reviews') || '{}');
        return data[masalaKey] || { status: 'ai', notes: '' };
    } catch { return { status: 'ai', notes: '' }; }
}

function saveReview(masalaKey, review) {
    try {
        const data = JSON.parse(localStorage.getItem('fiqh-reviews') || '{}');
        data[masalaKey] = review;
        localStorage.setItem('fiqh-reviews', JSON.stringify(data));
    } catch (e) { console.error(e); }
}

// ===== Views =====

async function viewDashboard() {
    setActiveNav('nav-home');
    setBreadcrumb(null);
    const kutub = await api('/api/kutub');

    let html = '<h2 class="page-title">الكتب الفقهية</h2>';
    html += '<div class="cards-grid">';

    for (const k of kutub) {
        html += `
        <div class="card" onclick="location.hash='#/kitab/${k.kitab_key}'">
            <div class="card-title">${k.kitab}</div>
            <div style="color:var(--cream-dim);margin-bottom:0.5rem;">
                ${k.masail_count} مسألة &mdash; ${k.abwab_count} باب
            </div>
            <div class="card-stats">
                <span class="stat-pill ittifaq">اتفاق: ${k.ittifaq}</span>
                <span class="stat-pill ikhtilaf">اختلاف: ${k.ikhtilaf}</span>
                <span class="stat-pill tafsilat">تفصيل: ${k.tafsilat}</span>
            </div>
        </div>`;
    }
    html += '</div>';
    app.innerHTML = html;
}

async function viewKitab(kitabKey) {
    setActiveNav('nav-home');

    // Get kitab name from the dashboard data
    const kutub = await api('/api/kutub');
    const kitabInfo = kutub.find(k => k.kitab_key === kitabKey);
    const kitabName = kitabInfo ? kitabInfo.kitab : kitabKey;

    localStorage.setItem('lastKitabKey', kitabKey);
    localStorage.setItem('lastKitabName', kitabName);

    setBreadcrumb([
        { label: 'الرئيسية', href: '#/' },
        { label: kitabName },
    ]);

    const abwab = await api(`/api/kutub/${kitabKey}/abwab`);

    let html = `<h2 class="page-title">${kitabName} — الأبواب</h2>`;
    html += '<div class="cards-grid">';

    for (const b of abwab) {
        const encodedBab = encodeURIComponent(b.bab);
        html += `
        <div class="card" onclick="location.hash='#/kitab/${kitabKey}/bab/${encodedBab}'">
            <div class="card-title">${b.bab}</div>
            <div style="color:var(--cream-dim);margin-bottom:0.5rem;">
                ${b.masail_count} مسألة
            </div>
            <div class="card-stats">
                <span class="stat-pill ittifaq">اتفاق: ${b.ittifaq}</span>
                <span class="stat-pill ikhtilaf">اختلاف: ${b.ikhtilaf}</span>
                <span class="stat-pill tafsilat">تفصيل: ${b.tafsilat}</span>
            </div>
        </div>`;
    }
    html += '</div>';
    app.innerHTML = html;
}

async function viewBab(kitabKey, babName) {
    setActiveNav('nav-home');
    setBreadcrumb([
        { label: 'الرئيسية', href: '#/' },
        { label: 'كتاب الطهارة', href: `#/kitab/${kitabKey}` },
        { label: babName },
    ]);

    const masail = await api(`/api/kutub/${kitabKey}/masail?bab=${encodeURIComponent(babName)}`);

    let html = `<h2 class="page-title">${babName}</h2>`;

    // Search bar
    html += `
    <div class="search-bar">
        <input type="text" id="masailSearch" placeholder="ابحث في المسائل..." oninput="filterMasailList()">
    </div>`;

    // Filter tabs
    html += `
    <div class="filter-tabs">
        <button class="active" data-filter="all" onclick="filterByResult('all', this)">الكل (${masail.length})</button>
        <button data-filter="ittifaq" onclick="filterByResult('ittifaq', this)">اتفاق</button>
        <button data-filter="ikhtilaf" onclick="filterByResult('ikhtilaf', this)">اختلاف</button>
        <button data-filter="tafsilat" onclick="filterByResult('tafsilat', this)">تفصيل</button>
    </div>`;

    html += '<div class="masail-list" id="masailListContainer">';
    for (const m of masail) {
        const review = getReview(m.masala_key);
        const reviewIndicator = review.status === 'approved'
            ? '<span class="badge badge-ittifaq" style="font-size:0.75rem">تمت المراجعة</span>'
            : review.status === 'rejected'
            ? '<span class="badge badge-ikhtilaf" style="font-size:0.75rem">مرفوض</span>'
            : '';

        html += `
        <div class="masala-row" data-result="${m.result}" data-title="${m.title_ar}" onclick="location.hash='#/masala/${m.masala_key}'">
            <div class="masala-info">
                <div class="masala-title">${m.title_ar}</div>
                <div class="masala-summary">${m.summary_ar || ''}</div>
            </div>
            <div class="masala-meta">
                ${reviewIndicator}
                <span class="count-circle">${m.positions_count}</span>
                ${resultBadge(m.result)}
            </div>
        </div>`;
    }
    html += '</div>';

    if (masail.length === 0) {
        html += '<div class="empty-state"><div class="icon">&#128214;</div>لا توجد مسائل في هذا الباب</div>';
    }

    app.innerHTML = html;
}

// Filter masail list by search text
window.filterMasailList = function () {
    const q = document.getElementById('masailSearch').value.trim();
    const rows = document.querySelectorAll('.masala-row');
    rows.forEach(row => {
        const title = row.getAttribute('data-title') || '';
        const text = row.textContent || '';
        const match = !q || title.includes(q) || text.includes(q);
        const activeFilter = document.querySelector('.filter-tabs button.active');
        const filter = activeFilter ? activeFilter.getAttribute('data-filter') : 'all';
        const resultMatch = filter === 'all' || row.getAttribute('data-result') === filter;
        row.style.display = (match && resultMatch) ? '' : 'none';
    });
};

window.filterByResult = function (result, btn) {
    document.querySelectorAll('.filter-tabs button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterMasailList();
};

async function viewMasala(masalaKey) {
    setActiveNav('nav-home');
    const m = await api(`/api/masail/${masalaKey}`);
    if (m.error) {
        app.innerHTML = '<div class="empty-state">المسألة غير موجودة</div>';
        return;
    }

    const comp = m.comparison || {};
    const result = comp.result || '';
    const resultLabel = RESULT_LABELS[result] || '';

    // Detect kitab from category
    const kitabKey = location.hash.includes('/kitab/')
        ? (localStorage.getItem('lastKitabKey') || 'tahara')
        : 'tahara';
    const kitabName = localStorage.getItem('lastKitabName') || 'كتاب الطهارة';

    setBreadcrumb([
        { label: 'الرئيسية', href: '#/' },
        { label: kitabName, href: `#/kitab/${kitabKey}` },
        { label: m.category, href: `#/kitab/${kitabKey}/bab/${encodeURIComponent(m.category)}` },
        { label: m.title_ar },
    ]);

    let html = '';

    // Title
    html += `<div class="detail-header"><div class="masala-title-big">${m.title_ar}</div></div>`;

    // Result banner
    if (result) {
        html += `
        <div class="result-banner ${result}">
            <div class="result-type">${resultLabel}</div>
            <div class="result-summary">${comp.summary_ar || ''}</div>
        </div>`;
    }

    // Details
    if (comp.details_ar) {
        html += `
        <div class="details-section">
            <h3>التفصيل</h3>
            <div>${comp.details_ar}</div>
        </div>`;
    }

    // View toggle
    html += `
    <h3 class="section-title">مواقف المتون (${m.positions.length} متن)</h3>
    <div class="view-toggle">
        <button class="active" id="btnCards" onclick="showCards()">بطاقات</button>
        <button id="btnTable" onclick="showTable()">جدول مقارنة</button>
    </div>`;

    // Cards view
    html += '<div id="positionsCards" class="positions-grid">';
    for (const p of m.positions) {
        html += `
        <div class="position-card">
            <div class="book-name">
                <span>${p.book}</span>
                ${hukmBadge(p.hukm)}
            </div>
            <div class="field-label">نص الحكم:</div>
            <div class="field-value">${p.hukm_text_ar || '—'}</div>
            ${p.dalil_ar ? `<div class="field-label">الدليل:</div><div class="field-value">${p.dalil_ar}</div>` : ''}
            ${p.conditions_ar ? `<div class="field-label">الشروط / ملاحظات:</div><div class="field-value">${p.conditions_ar}</div>` : ''}
        </div>`;
    }
    html += '</div>';

    // Table view (hidden by default)
    html += '<div id="positionsTable" style="display:none;overflow-x:auto;">';
    html += '<table class="positions-table">';
    html += '<thead><tr><th>المتن</th><th>الحكم</th><th>نص الحكم</th><th>الدليل</th><th>الشروط</th></tr></thead>';
    html += '<tbody>';
    for (const p of m.positions) {
        html += `<tr>
            <td style="white-space:nowrap;color:var(--gold)">${p.book}</td>
            <td>${hukmBadge(p.hukm)}</td>
            <td>${p.hukm_text_ar || '—'}</td>
            <td>${p.dalil_ar || '—'}</td>
            <td>${p.conditions_ar || '—'}</td>
        </tr>`;
    }
    html += '</tbody></table></div>';

    // Review section
    const review = getReview(masalaKey);
    const statusLabels = {
        ai: { label: 'مولّد بالذكاء الاصطناعي', cls: 'status-ai' },
        approved: { label: 'تمت المراجعة', cls: 'status-reviewed' },
        rejected: { label: 'مرفوض', cls: 'status-ai' },
        verified: { label: 'موثق', cls: 'status-verified' },
    };
    const st = statusLabels[review.status] || statusLabels.ai;

    html += `
    <div class="review-section">
        <h3>مراجعة العالم</h3>
        <div class="review-status">
            <span>الحالة:</span>
            <span class="status-badge ${st.cls}" id="reviewStatusBadge">${st.label}</span>
        </div>
        <textarea class="review-notes" id="reviewNotes" placeholder="ملاحظات المراجع...">${review.notes || ''}</textarea>
        <div class="review-buttons">
            <button class="btn btn-approve" onclick="doReview('${masalaKey}', 'approved')">قبول</button>
            <button class="btn btn-reject" onclick="doReview('${masalaKey}', 'rejected')">رفض</button>
            <button class="btn btn-reset" onclick="doReview('${masalaKey}', 'ai')">إعادة تعيين</button>
        </div>
    </div>`;

    app.innerHTML = html;
}

window.showCards = function () {
    document.getElementById('positionsCards').style.display = '';
    document.getElementById('positionsTable').style.display = 'none';
    document.getElementById('btnCards').classList.add('active');
    document.getElementById('btnTable').classList.remove('active');
};

window.showTable = function () {
    document.getElementById('positionsCards').style.display = 'none';
    document.getElementById('positionsTable').style.display = '';
    document.getElementById('btnTable').classList.add('active');
    document.getElementById('btnCards').classList.remove('active');
};

window.doReview = function (masalaKey, status) {
    const notes = document.getElementById('reviewNotes').value;
    saveReview(masalaKey, { status, notes });
    const statusLabels = {
        ai: { label: 'مولّد بالذكاء الاصطناعي', cls: 'status-ai' },
        approved: { label: 'تمت المراجعة', cls: 'status-reviewed' },
        rejected: { label: 'مرفوض', cls: 'status-ai' },
    };
    const st = statusLabels[status] || statusLabels.ai;
    const badge = document.getElementById('reviewStatusBadge');
    badge.textContent = st.label;
    badge.className = 'status-badge ' + st.cls;
};

async function viewStats() {
    setActiveNav('nav-stats');
    setBreadcrumb([{ label: 'الرئيسية', href: '#/' }, { label: 'الإحصائيات' }]);

    const stats = await api('/api/stats');
    const rc = stats.result_counts;
    const total = stats.total_masail || 1;

    let html = '<h2 class="page-title">الإحصائيات العامة</h2>';

    // Summary cards
    html += '<div class="stats-grid">';
    html += `<div class="stat-card"><div class="stat-number">${stats.total_masail}</div><div class="stat-label">إجمالي المسائل</div></div>`;
    html += `<div class="stat-card"><div class="stat-number">${stats.total_positions}</div><div class="stat-label">إجمالي المواقف</div></div>`;
    html += `<div class="stat-card"><div class="stat-number" style="color:var(--ittifaq)">${rc.ittifaq}</div><div class="stat-label">اتفاق</div></div>`;
    html += `<div class="stat-card"><div class="stat-number" style="color:var(--ikhtilaf)">${rc.ikhtilaf}</div><div class="stat-label">اختلاف</div></div>`;
    html += `<div class="stat-card"><div class="stat-number" style="color:var(--tafsilat)">${rc.tafsilat}</div><div class="stat-label">تفصيل</div></div>`;
    html += '</div>';

    // Result breakdown bar
    html += '<div class="chart-container"><h3>توزيع النتائج</h3><div class="bar-chart">';
    for (const [key, label] of [['ittifaq', 'اتفاق'], ['ikhtilaf', 'اختلاف'], ['tafsilat', 'تفصيل']]) {
        const pct = Math.round((rc[key] / total) * 100);
        html += `
        <div class="bar-row">
            <div class="bar-label">${label}</div>
            <div class="bar-track">
                <div class="bar-fill ${key}" style="width:${pct}%">${rc[key]}</div>
            </div>
        </div>`;
    }
    html += '</div></div>';

    // Per-bab breakdown
    html += '<div class="chart-container"><h3>المسائل حسب الباب</h3><div class="bar-chart">';
    const babStats = stats.bab_stats;
    const maxBab = Math.max(...Object.values(babStats).map(b => b.masail_count), 1);
    for (const [bab, bst] of Object.entries(babStats)) {
        const pct = Math.round((bst.masail_count / maxBab) * 100);
        html += `
        <div class="bar-row">
            <div class="bar-label">${bab}</div>
            <div class="bar-track">
                <div class="bar-fill gold" style="width:${pct}%">${bst.masail_count}</div>
            </div>
        </div>`;
    }
    html += '</div></div>';

    // Per-book breakdown
    html += '<div class="chart-container"><h3>المواقف حسب المتن</h3><div class="bar-chart">';
    const bookCounts = stats.book_counts;
    const maxBook = Math.max(...Object.values(bookCounts), 1);
    // Sort by count desc
    const sortedBooks = Object.entries(bookCounts).sort((a, b) => b[1] - a[1]);
    for (const [book, count] of sortedBooks) {
        const pct = Math.round((count / maxBook) * 100);
        html += `
        <div class="bar-row">
            <div class="bar-label">${book}</div>
            <div class="bar-track">
                <div class="bar-fill gold" style="width:${pct}%">${count}</div>
            </div>
        </div>`;
    }
    html += '</div></div>';

    // Hukm breakdown
    html += '<div class="chart-container"><h3>التوزيع حسب الحكم</h3><div class="bar-chart">';
    const hukmCounts = stats.hukm_counts;
    const maxHukm = Math.max(...Object.values(hukmCounts), 1);
    const hukmColors = { wajib: 'ittifaq', mandub: 'tafsilat', makruh: 'tafsilat', haram: 'ikhtilaf' };
    for (const [hukm, count] of Object.entries(hukmCounts)) {
        const pct = Math.round((count / maxHukm) * 100);
        const label = HUKM_LABELS[hukm] || hukm;
        const cls = hukmColors[hukm] || 'gold';
        html += `
        <div class="bar-row">
            <div class="bar-label">${label}</div>
            <div class="bar-track">
                <div class="bar-fill ${cls}" style="width:${pct}%">${count}</div>
            </div>
        </div>`;
    }
    html += '</div></div>';

    app.innerHTML = html;
}

// ===== Router =====

async function route() {
    const hash = location.hash || '#/';
    window.scrollTo(0, 0);

    try {
        if (hash === '#/' || hash === '#') {
            await viewDashboard();
        } else if (hash === '#/stats') {
            await viewStats();
        } else if (hash.match(/^#\/kitab\/([^/]+)\/bab\/(.+)$/)) {
            const m = hash.match(/^#\/kitab\/([^/]+)\/bab\/(.+)$/);
            await viewBab(m[1], decodeURIComponent(m[2]));
        } else if (hash.match(/^#\/kitab\/([^/]+)$/)) {
            const m = hash.match(/^#\/kitab\/([^/]+)$/);
            await viewKitab(m[1]);
        } else if (hash.match(/^#\/masala\/(.+)$/)) {
            const m = hash.match(/^#\/masala\/(.+)$/);
            await viewMasala(m[1]);
        } else {
            await viewDashboard();
        }
    } catch (e) {
        console.error(e);
        app.innerHTML = `<div class="empty-state"><div class="icon">&#9888;</div>حدث خطأ: ${e.message}</div>`;
    }
}

window.addEventListener('hashchange', route);
window.addEventListener('DOMContentLoaded', route);

// Scroll-to-top button
window.addEventListener('scroll', () => {
    const btn = document.getElementById('scrollTop');
    if (window.scrollY > 300) {
        btn.style.display = 'flex';
    } else {
        btn.style.display = 'none';
    }
});
