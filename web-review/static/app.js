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

const KITAB_NAMES_AR = {
    tahara: 'كتاب الطهارة', salat: 'كتاب الصلاة', zakat: 'كتاب الزكاة',
    siyam: 'كتاب الصيام', hajj: 'كتاب الحج', nikah: 'كتاب النكاح',
    talaq: 'كتاب الطلاق', buyu: 'كتاب البيوع', faraid: 'كتاب الفرائض',
    qada: 'كتاب القضاء', hudud: 'كتاب الحدود', misc: 'كتب متفرقة',
};

const HUKM_LABELS = {
    wajib: 'واجب',
    mandub: 'مندوب',
    mustahab: 'مستحب',
    mubah: 'مباح',
    makruh: 'مكروه',
    haram: 'حرام',
    sahih: 'صحيح',
    fasid: 'فاسد',
    batil: 'باطل',
    sunna: 'سنة',
    sunna_muakkada: 'سنة مؤكدة',
    fard: 'فرض',
    fard_kifaya: 'فرض كفاية',
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
    const kitabName = localStorage.getItem('lastKitabName') || KITAB_NAMES_AR[kitabKey] || kitabKey;
    setBreadcrumb([
        { label: 'الرئيسية', href: '#/' },
        { label: kitabName, href: `#/kitab/${kitabKey}` },
        { label: babName },
    ]);

    // Fetch all masail and filter client-side (avoids Arabic query string issues)
    const allMasail = await api(`/api/kutub/${kitabKey}/masail`);
    const masail = allMasail.filter(m => m.category === babName);

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

    // Scholar feedback form (saved to DB)
    html += `
    <div class="review-section">
        <h3>تعليقات العلماء</h3>
        <div id="feedbackList" class="feedback-list"><div class="loading">جاري تحميل التعليقات...</div></div>
        <div class="feedback-form">
            <h4>إضافة تعليق جديد</h4>
            <input type="text" id="fbScholar" class="review-input" placeholder="اسم العالم / المراجع">
            <select id="fbStatus" class="review-select">
                <option value="pending">في الانتظار</option>
                <option value="approved">موافق على النتيجة</option>
                <option value="rejected">غير موافق</option>
                <option value="needs_revision">يحتاج مراجعة</option>
            </select>
            <select id="fbSuggestedResult" class="review-select">
                <option value="">— تصحيح النتيجة (اختياري) —</option>
                <option value="ittifaq">اتفاق</option>
                <option value="ikhtilaf">اختلاف</option>
                <option value="tafsilat">تفصيل</option>
            </select>
            <textarea id="fbComment" class="review-notes" placeholder="التعليق أو التصحيح..."></textarea>
            <textarea id="fbCorrections" class="review-notes" placeholder="تصحيحات تفصيلية (اختياري)..."></textarea>
            <button class="btn btn-approve" onclick="submitFeedback('${masalaKey}')">إرسال التعليق</button>
        </div>
    </div>`;

    app.innerHTML = html;

    // Load existing feedback for this masala
    loadMasalaFeedback(masalaKey);
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

// === Feedback functions ===

const FB_STATUS_LABELS = {
    pending: { label: 'في الانتظار', cls: 'status-ai' },
    approved: { label: 'موافق', cls: 'status-reviewed' },
    rejected: { label: 'غير موافق', cls: 'badge-ikhtilaf' },
    needs_revision: { label: 'يحتاج مراجعة', cls: 'badge-tafsilat' },
};

async function loadMasalaFeedback(masalaKey) {
    const el = document.getElementById('feedbackList');
    try {
        const feedbacks = await api(`/api/feedback/masala/${masalaKey}`);
        if (!feedbacks.length) {
            el.innerHTML = '<div style="color:var(--cream-dim);padding:0.5rem;">لا توجد تعليقات بعد</div>';
            return;
        }
        el.innerHTML = feedbacks.map(fb => {
            const st = FB_STATUS_LABELS[fb.status] || FB_STATUS_LABELS.pending;
            const date = fb.created_at ? new Date(fb.created_at).toLocaleDateString('ar-MA') : '';
            return `
            <div class="feedback-card">
                <div class="feedback-header">
                    <strong>${fb.scholar_name || 'مجهول'}</strong>
                    <span class="status-badge ${st.cls}">${st.label}</span>
                    <span style="color:var(--cream-dim);font-size:0.8rem;">${date}</span>
                </div>
                ${fb.suggested_result ? `<div>النتيجة المقترحة: ${resultBadge(fb.suggested_result)}</div>` : ''}
                <div class="feedback-comment">${fb.comment || ''}</div>
                ${fb.corrections ? `<div class="feedback-corrections"><strong>تصحيحات:</strong> ${fb.corrections}</div>` : ''}
            </div>`;
        }).join('');
    } catch (e) {
        el.innerHTML = '<div style="color:#D4453A;">خطأ في تحميل التعليقات</div>';
    }
}

window.submitFeedback = async function(masalaKey) {
    const data = {
        masala_key: masalaKey,
        scholar_name: document.getElementById('fbScholar').value,
        status: document.getElementById('fbStatus').value,
        comment: document.getElementById('fbComment').value,
        suggested_result: document.getElementById('fbSuggestedResult').value,
        corrections: document.getElementById('fbCorrections').value,
    };
    try {
        const fbUrl = '/api/feedback/'.replace('/api/', '/fiqh/api/') || '/api/feedback/';
        await fetch(fbUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        // Clear form
        document.getElementById('fbScholar').value = '';
        document.getElementById('fbComment').value = '';
        document.getElementById('fbCorrections').value = '';
        document.getElementById('fbSuggestedResult').value = '';
        document.getElementById('fbStatus').value = 'pending';
        // Reload feedback
        loadMasalaFeedback(masalaKey);
    } catch (e) {
        alert('خطأ في إرسال التعليق: ' + e.message);
    }
};

async function viewFeedback() {
    setActiveNav('nav-feedback');
    setBreadcrumb([{ label: 'الرئيسية', href: '#/' }, { label: 'المراجعات' }]);

    const stats = await api('/api/feedback/stats');
    const feedbacks = await api('/api/feedback/all');

    let html = '<h2 class="page-title">مراجعات العلماء</h2>';

    // Stats cards
    html += '<div class="stats-grid">';
    html += `<div class="stat-card"><div class="stat-number">${stats.total || 0}</div><div class="stat-label">إجمالي التعليقات</div></div>`;
    const bs = stats.by_status || {};
    html += `<div class="stat-card"><div class="stat-number" style="color:var(--ittifaq)">${bs.approved || 0}</div><div class="stat-label">موافق</div></div>`;
    html += `<div class="stat-card"><div class="stat-number" style="color:var(--ikhtilaf)">${bs.rejected || 0}</div><div class="stat-label">غير موافق</div></div>`;
    html += `<div class="stat-card"><div class="stat-number" style="color:var(--tafsilat)">${bs.needs_revision || 0}</div><div class="stat-label">يحتاج مراجعة</div></div>`;
    html += `<div class="stat-card"><div class="stat-number">${bs.pending || 0}</div><div class="stat-label">في الانتظار</div></div>`;
    html += '</div>';

    // Filter tabs
    html += `
    <div class="filter-tabs">
        <button class="active" onclick="filterFeedback('all', this)">الكل</button>
        <button onclick="filterFeedback('pending', this)">في الانتظار</button>
        <button onclick="filterFeedback('approved', this)">موافق</button>
        <button onclick="filterFeedback('rejected', this)">غير موافق</button>
        <button onclick="filterFeedback('needs_revision', this)">يحتاج مراجعة</button>
    </div>`;

    // Feedback list
    html += '<div class="masail-list" id="feedbackListAll">';
    if (!feedbacks.length) {
        html += '<div class="empty-state">لا توجد مراجعات بعد</div>';
    }
    for (const fb of feedbacks) {
        const st = FB_STATUS_LABELS[fb.status] || FB_STATUS_LABELS.pending;
        const date = fb.created_at ? new Date(fb.created_at).toLocaleDateString('ar-MA') : '';
        html += `
        <div class="masala-row feedback-row" data-status="${fb.status}" onclick="location.hash='#/masala/${fb.masala_key}'">
            <div class="masala-info">
                <div class="masala-title">${fb.masala_key}</div>
                <div class="masala-summary">
                    <strong>${fb.scholar_name || 'مجهول'}</strong> — ${fb.comment ? fb.comment.substring(0, 120) + '...' : 'بدون تعليق'}
                </div>
            </div>
            <div class="masala-meta">
                <span style="color:var(--cream-dim);font-size:0.8rem;">${date}</span>
                <span class="status-badge ${st.cls}">${st.label}</span>
                ${fb.suggested_result ? resultBadge(fb.suggested_result) : ''}
            </div>
        </div>`;
    }
    html += '</div>';

    app.innerHTML = html;
}

window.filterFeedback = function(status, btn) {
    document.querySelectorAll('.filter-tabs button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.feedback-row').forEach(row => {
        row.style.display = (status === 'all' || row.getAttribute('data-status') === status) ? '' : 'none';
    });
};

// === المراجع (Sources) ===

async function viewMaraji3() {
    setActiveNav('nav-maraji3');
    setBreadcrumb([{ label: 'الرئيسية', href: '#/' }, { label: 'المراجع' }]);

    const sources = await api('/api/maraji3');

    let html = '<h2 class="page-title">المراجع والمصادر</h2>';
    html += '<p style="color:var(--cream-dim);margin-bottom:1.5rem;">المتون والكتب المستخدمة في استخراج الأحكام ومقارنتها</p>';

    // Summary
    html += '<div class="stats-grid">';
    html += `<div class="stat-card"><div class="stat-number">${sources.length}</div><div class="stat-label">عدد المصادر</div></div>`;
    const totalPositions = sources.reduce((s, b) => s + b.positions_count, 0);
    html += `<div class="stat-card"><div class="stat-number">${totalPositions}</div><div class="stat-label">إجمالي المواقف المستخرجة</div></div>`;
    html += '</div>';

    // Level labels
    const LEVEL_LABELS = { 'مبتدئ': 'badge-ittifaq', 'متوسط': 'badge-tafsilat', 'متقدم': 'badge-ikhtilaf', 'متخصص': 'badge-none' };
    const TYPE_LABELS = { 'متن': 'badge-wajib', 'نظم': 'badge-mandub', 'موسوعة': 'badge-none', 'شرح': 'badge-mubah' };

    // Source cards
    html += '<div class="maraji3-list">';
    for (const src of sources) {
        const levelCls = LEVEL_LABELS[src.level] || 'badge-none';
        const typeCls = TYPE_LABELS[src.type] || 'badge-none';

        html += `
        <div class="card marji3-card">
            <div class="marji3-header">
                <div class="marji3-title">${src.book}</div>
                <div class="marji3-badges">
                    ${src.type ? `<span class="badge ${typeCls}">${src.type}</span>` : ''}
                    ${src.level ? `<span class="badge ${levelCls}">${src.level}</span>` : ''}
                </div>
            </div>
            ${src.author ? `<div class="marji3-author"><strong>المؤلف:</strong> ${src.author} ${src.death ? `(ت ${src.death})` : ''}</div>` : ''}
            ${src.description ? `<div class="marji3-desc">${src.description}</div>` : ''}
            <div class="marji3-stats">
                <span><strong>${src.positions_count}</strong> موقف مستخرج</span>
                <span><strong>${src.masail_count}</strong> مسألة</span>
                <span>الكتب: ${src.kutub_covered.join(' · ')}</span>
            </div>
            ${src.sample_texts.length ? `
            <div class="marji3-samples">
                <div style="color:var(--gold-dim);font-size:0.85rem;margin-bottom:0.3rem;">نموذج من النصوص المستخرجة:</div>
                ${src.sample_texts.map(t => `<div class="sample-text">"${t}..."</div>`).join('')}
            </div>` : ''}
        </div>`;
    }
    html += '</div>';

    // Methodology note
    html += `
    <div class="card" style="margin-top:2rem;border-color:var(--gold-dim);">
        <h3 style="color:var(--gold);margin-bottom:0.8rem;">منهجية الاستخراج</h3>
        <div style="color:var(--cream);line-height:2;">
            <p>تم استخراج المواقف الفقهية من المتون المذكورة أعلاه باستخدام الذكاء الاصطناعي (Claude) بناء على المعرفة المخزنة من هذه الكتب.</p>
            <p><strong>مستويات الموثوقية:</strong></p>
            <ul style="padding-right:1.5rem;">
                <li><span class="badge status-ai" style="font-size:0.8rem;">مولّد بالذكاء الاصطناعي</span> — يحتاج مراجعة عالم</li>
                <li><span class="badge status-reviewed" style="font-size:0.8rem;">تمت المراجعة</span> — راجعه عالم وأقره</li>
                <li><span class="badge status-verified" style="font-size:0.8rem;">موثق</span> — تم التحقق من النص الأصلي</li>
            </ul>
            <p style="margin-top:0.8rem;">المتون المستخدمة تمثل طبقات مختلفة من التعليم الفقهي المالكي: من مستوى المبتدئين (الأخضري، ابن عاشر) إلى المتخصصين (المدونة، مختصر خليل).</p>
        </div>
    </div>`;

    app.innerHTML = html;
}

async function viewStats() {
    setActiveNav('nav-stats');
    setBreadcrumb([{ label: 'الرئيسية', href: '#/' }, { label: 'الإحصائيات' }]);

    const stats = await api('/api/stats');
    const fbStats = await api('/api/feedback/stats');
    const rc = stats.result_counts;
    const total = stats.total_masail || 1;
    const reviewedKeys = new Set(fbStats.reviewed_masail_keys || []);

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

    // Scholar coverage per bab
    const totalReviewed = reviewedKeys.size;
    const coveragePct = total > 0 ? Math.round((totalReviewed / total) * 100) : 0;

    html += `<div class="chart-container">
        <h3>تغطية المراجعة العلمية</h3>
        <div class="stats-grid" style="margin-bottom:1rem;">
            <div class="stat-card"><div class="stat-number">${totalReviewed}</div><div class="stat-label">مسائل تمت مراجعتها</div></div>
            <div class="stat-card"><div class="stat-number">${total - totalReviewed}</div><div class="stat-label">مسائل بدون مراجعة</div></div>
            <div class="stat-card"><div class="stat-number" style="color:${coveragePct > 50 ? 'var(--ittifaq)' : 'var(--tafsilat)'}">${coveragePct}%</div><div class="stat-label">نسبة التغطية الإجمالية</div></div>
        </div>
        <div class="bar-chart">`;

    // Get all masail to calculate per-bab coverage
    const allKutub = await api('/api/kutub');
    for (const k of allKutub) {
        const abwab = await api(`/api/kutub/${k.kitab_key}/abwab`);
        html += `<div style="color:var(--gold);font-weight:bold;margin:1rem 0 0.5rem;">${k.kitab}</div>`;
        const allMasail = await api(`/api/kutub/${k.kitab_key}/masail`);

        for (const b of abwab) {
            const babMasail = allMasail.filter(m => m.category === b.bab);
            const babReviewed = babMasail.filter(m => reviewedKeys.has(m.masala_key)).length;
            const babTotal = babMasail.length;
            const babPct = babTotal > 0 ? Math.round((babReviewed / babTotal) * 100) : 0;
            const barCls = babPct === 100 ? 'ittifaq' : babPct > 0 ? 'tafsilat' : 'ikhtilaf';

            html += `
            <div class="bar-row">
                <div class="bar-label">${b.bab} <span style="color:var(--cream-dim);font-size:0.8rem;">(${babReviewed}/${babTotal})</span></div>
                <div class="bar-track">
                    <div class="bar-fill ${barCls}" style="width:${Math.max(babPct, 2)}%">${babPct}%</div>
                </div>
            </div>`;
        }
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
        } else if (hash === '#/maraji3') {
            await viewMaraji3();
        } else if (hash === '#/feedback') {
            await viewFeedback();
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
