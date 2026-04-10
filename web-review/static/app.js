/**
 * Maliki Fiqh Masail Review — Single Page App
 */

const $ = (sel) => document.querySelector(sel);
const app = $('#app');
const breadcrumbEl = $('#breadcrumb');

// ===== Helpers =====

function escHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
const escAttr = escHtml;

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
    const res = await fetch(path.replace('/api/', '/fiqh/api/'));
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

// ===== Book Data Loaders =====

const _bookCache = {};
async function loadBookData(filename) {
    if (!_bookCache[filename]) {
        const res = await fetch(filename);
        if (!res.ok) throw new Error(`فشل تحميل ${filename}`);
        const d = await res.json();
        if (!d || !Array.isArray(d.kutub)) throw new Error(`بيانات ${filename} غير صالحة`);
        _bookCache[filename] = d;
    }
    return _bookCache[filename];
}

let _muwattaData = null;
async function loadMuwatta() {
    if (!_muwattaData) {
        _muwattaData = await loadBookData('muwatta-masail.json');
    }
    return _muwattaData;
}

async function loadMudawwana() { return loadBookData('mudawwana-masail.json'); }
async function loadRisala() { return loadBookData('risala-masail.json'); }
async function loadKhalil() { return loadBookData('khalil-masail.json'); }

let _comparisonData = null;
async function loadComparison() {
    if (!_comparisonData) {
        const res = await fetch('tahara-comparison.json');
        if (!res.ok) return { kutub: [], total_comparisons: 0, average_tawafoq: 0 };
        _comparisonData = await res.json();
    }
    return _comparisonData;
}

// ===== Muwatta Views =====

async function viewMuwatta() {
    setActiveNav('nav-masail');
    setBreadcrumb([
        { label: 'المسائل', href: '#/masail-home' },
        { label: 'الموطأ' },
    ]);
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const data = await loadMuwatta();
    const kutub = data.kutub;

    let totalMasail = 0;
    let totalAbwab = 0;
    let totalSub = 0;
    for (const k of kutub) {
        totalAbwab += k.abwab.length;
        totalMasail += k.masail_count || 0;
        totalSub += k.sub_masail_count || 0;
    }

    const remaining = data.stats ? data.stats.remaining_kutub : 0;

    let html = `
    <h2 class="page-title">مسائل الموطأ</h2>
    <div style="text-align:center;color:var(--cream-dim);margin-bottom:1rem;">
        ${escHtml(data.author)}
    </div>
    <div class="stats-bar" style="margin-bottom:1.5rem;">
        <div class="stat-item"><span class="stat-num">${kutub.length}</span><span class="stat-lbl">كتاب</span></div>
        <div class="stat-item"><span class="stat-num">${totalAbwab}</span><span class="stat-lbl">باب</span></div>
        <div class="stat-item"><span class="stat-num">${totalMasail}</span><span class="stat-lbl">مسألة</span></div>
        <div class="stat-item"><span class="stat-num">${totalSub}</span><span class="stat-lbl">فرعية</span></div>
    </div>
    ${remaining > 0 ? `<div style="text-align:center;color:var(--gold);margin-bottom:1.5rem;font-size:.9rem;">تم استخراج ${kutub.length} من 62 كتاباً — ${remaining} كتاباً متبقياً</div>` : ''}
    <div class="cards-grid">`;

    for (const k of kutub) {
        const mc = k.masail_count || k.abwab.reduce((s, b) => s + b.masail.length, 0);
        const sc = k.sub_masail_count || 0;
        html += `
        <div class="card" onclick="location.hash='#/muwatta/kitab/${k.kitab_num}'">
            <div class="card-title">${escHtml(k.kitab_name)}</div>
            <div class="card-stats">
                <span class="stat-pill tafsilat">${k.abwab.length} باب</span>
                <span class="stat-pill ittifaq">${mc} مسألة</span>
                ${sc > 0 ? `<span class="stat-pill ikhtilaf">${sc} فرعية</span>` : ''}
            </div>
        </div>`;
    }

    html += '</div>';
    app.innerHTML = html;
}

async function viewMuwattaKitab(kitabNum) {
    setActiveNav('nav-masail');
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const data = await loadMuwatta();
    const kitab = data.kutub.find(k => k.kitab_num == kitabNum);
    if (!kitab) { app.innerHTML = '<div class="empty-state">الكتاب غير موجود</div>'; return; }

    setBreadcrumb([
        { label: 'المسائل', href: '#/masail-home' },
        { label: 'الموطأ', href: '#/muwatta' },
        { label: kitab.kitab_name },
    ]);

    const totalMasail = kitab.abwab.reduce((s, b) => s + b.masail.length, 0);

    let html = `<div class="page-enter">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;margin-bottom:1.2rem;">
        <div>
            <h2 class="page-title" style="margin-bottom:0.25rem;">${escHtml(kitab.kitab_name)}</h2>
            <div style="color:var(--cream-dim);font-size:.9rem;">${totalMasail} مسألة — ${kitab.abwab.length} باب</div>
        </div>
        <div class="mw-view-toggle">
            <button class="active">📋 قائمة</button>
            <button onclick="location.hash='#/muwatta/kitab/${kitabNum}/mindmap'">🗺 خريطة ذهنية</button>
        </div>
    </div>

    <div class="mw-search-wrap">
        <span class="mw-search-icon">🔍</span>
        <input class="mw-search-input" id="mwSearch" type="search" placeholder="ابحث في المسائل والأحكام..." dir="rtl" oninput="mwFilterMasail(this.value)">
    </div>

    <div id="mwMasailContainer">`;

    for (const bab of kitab.abwab) {
        const babId = 'bab-' + (bab.bab_num || bab.bab_name || '').toString().replace(/\s+/g, '-').replace(/[^\w-]/g, '');
        html += `
        <div class="mw-bab-group" id="${escHtml(babId)}">
            <div class="mw-bab-group-header" onclick="toggleBabGroup('${escHtml(babId)}')">
                <div>
                    <span class="mw-bab-group-title">${escHtml(bab.bab_name || 'باب')}</span>
                </div>
                <div style="display:flex;align-items:center;gap:.6rem;">
                    <span class="mw-bab-group-count">${bab.masail.length} مسألة</span>
                    <span class="mw-bab-group-arrow">▼</span>
                </div>
            </div>
            <div class="mw-bab-group-body">`;
        for (const m of bab.masail) {
            html += renderMasalaCard(m, bab);
        }
        html += `</div></div>`;
    }

    html += `</div></div>`;
    app.innerHTML = html;

    // Apply saved review states to cards
    applyMwReviewStates();
}

function renderMasalaCard(m, bab) {
    const id = m.masala_id || m.id || '';
    const topic = m.masala_topic || m.masala_title || m.title || '';
    const hukm = m.hukm || '';
    const babName = m.bab || bab.bab_name || '';
    const babNum = m.bab_num || bab.bab_num || '';
    const tags = m.fiqh_tags || [];
    const rulings = m.rulings || (m.qawl_malik ? m.qawl_malik.map(t => ({speaker:'مالك',text:t})) : []);
    const dalilArr = m.dalil || [];
    const subMasail = m.sub_masail || [];

    let html = `
    <div class="mw-masala-card" id="${escHtml(id)}">
        <div class="mw-masala-header">
            <span class="mw-masala-num">باب ${escHtml(String(babNum))}</span>
            <span class="mw-masala-page">${escHtml(babName)}</span>
        </div>
        <h4 class="mw-masala-title">${escHtml(topic)}</h4>

        ${hukm ? `<div class="mw-masala-hukm"><strong>الحكم:</strong> ${fixArabicDisplay(escHtml(hukm))}</div>` : ''}`;

    // أقوال العلماء (rulings grouped by speaker)
    if (rulings.length > 0) {
        // Group by speaker
        const bySpk = {};
        for (const r of rulings) {
            const key = r.speaker || '';
            if (!bySpk[key]) bySpk[key] = [];
            bySpk[key].push(r);
        }
        html += `<div class="mw-qawl-malik">`;
        for (const [speaker, items] of Object.entries(bySpk)) {
            const via = items[0].via ? ` <span style="color:var(--cream-dim);font-size:.85rem;">(عن طريق ${escHtml(items[0].via)})</span>` : '';
            html += `<div style="margin-bottom:.6rem;">
                <strong style="color:var(--gold);">أقوال ${escHtml(speaker)}:${via}</strong>`;
            for (const r of items) {
                html += `<blockquote class="mw-quote">${fixArabicDisplay(escHtml(r.text || ''))}</blockquote>`;
            }
            html += `</div>`;
        }
        html += `</div>`;
    }

    // أدلة — structured evidence list (حديث، أثر، قرآن، قول مالك، متن)
    if (dalilArr.length > 0) {
        html += `<div class="mw-dalil-section">
            <strong>الأدلة (${dalilArr.length}):</strong>
            <ul class="mw-dalil-list">`;
        for (const d of dalilArr) {
            const typeLabel = d.type === 'hadith' ? 'حديث' : d.type === 'athar' ? 'أثر' : d.type || '';
            const hasFullText = d.full_text ? true : false;
            const clickAttr = hasFullText ? `class="mw-dalil-clickable" onclick="showDalilPopup(this)" data-full-text="${escAttr(d.full_text)}" data-shamela-url="${escAttr(d.shamela_url || '')}" data-type="${escAttr(typeLabel)}" data-num="${d.num || ''}" data-hadith-grade="${escAttr(d.hadith_grade || '')}"` : '';
            const summary = d.summary || (d.full_text ? fixArabicDisplay(d.full_text.substring(0, 120)) + '...' : '');
            html += `<li ${clickAttr}>
                <span class="mw-dalil-type">${escHtml(typeLabel)} ${d.num || ''}</span>
                <span class="mw-dalil-narrator">${escHtml(d.narrator || '')}</span>
                ${summary ? `<span class="mw-dalil-summary">— ${escHtml(summary)}</span>` : ''}
                ${hasFullText ? '<span class="mw-dalil-expand">↩</span>' : ''}
            </li>`;
        }
        html += `</ul></div>`;
    }

    // Source text popup button (for non-الموطأ books)
    const source = m._source;
    if (source && source.full_text) {
        const shaUrl = source.shamela_url || '';
        html += `<div style="margin-top:.8rem;text-align:center;">
            <button class="mw-source-btn" onclick="showSourcePopup(this)"
                data-full-text="${escAttr(source.full_text)}"
                data-shamela-url="${escAttr(shaUrl)}"
                data-page-start="${source.page_start || ''}"
                data-page-end="${source.page_end || ''}"
                data-topic="${escAttr(topic)}"
                style="background:var(--card-bg);border:1px solid var(--gold);color:var(--gold);padding:.4rem 1rem;border-radius:.3rem;cursor:pointer;font-family:inherit;font-size:.85rem;">
                📖 عرض النص الكامل
            </button>
        </div>`;
    }

    // Old format fallback (dalil as string)
    if (typeof m.dalil === 'string' && m.dalil) {
        html += `<div class="mw-masala-dalil"><strong>الدليل:</strong> ${escHtml(m.dalil)}</div>`;
    }

    // مسائل فرعية
    if (subMasail.length > 0) {
        html += `<div class="mw-sub-masail">
            <strong>مسائل فرعية (${subMasail.length}):</strong>`;
        for (const s of subMasail) {
            html += `<div class="mw-sub-masala">
                <span class="mw-sub-title">${escHtml(s.title)}</span>
                <span class="mw-sub-hukm">${escHtml(s.hukm)}</span>
            </div>`;
        }
        html += `</div>`;
    }

    // وسوم فقهية
    if (tags.length > 0) {
        html += `<div class="mw-tags">`;
        for (const t of tags) {
            html += `<span class="mw-tag">${escHtml(t)}</span>`;
        }
        html += `</div>`;
    }

    // Notes (old format)
    if (m.notes) {
        html += `<div class="mw-masala-notes"><strong>ملاحظات:</strong> ${escHtml(m.notes)}</div>`;
    }

    // ── Inline Scholar Review ──
    if (id) {
        const saved = getMwReview(id);
        const hasCls = saved ? ` has-review status-${saved.status}` : '';
        const btnLabel = saved ? `✓ ${saved.status === 'approved' ? 'موافق' : saved.status === 'rejected' ? 'غير موافق' : 'يحتاج تعديل'}` : '+ مراجعة';
        const scholarDisplay = saved && saved.scholar ? `<span style="color:var(--cream-dim);font-size:.8rem;margin-right:.5rem;">— ${escHtml(saved.scholar)}</span>` : '';
        html += `
    <div style="margin-top:.9rem;padding-top:.7rem;border-top:1px solid rgba(200,169,110,0.1);display:flex;align-items:center;flex-wrap:wrap;gap:.4rem;">
        <button class="mw-review-toggle${hasCls}" id="rvbtn-${escAttr(id)}" onclick="toggleMwReview('${escAttr(id)}')">
            ${btnLabel}
        </button>
        ${scholarDisplay}
    </div>
    <div class="mw-review-panel hidden" id="rvpanel-${escAttr(id)}">
        <div class="mw-review-row">
            <input class="mw-review-input" id="rvs-${escAttr(id)}" type="text" placeholder="اسم الشيخ (اختياري)" value="${escAttr(saved ? saved.scholar || '' : '')}">
            <select class="mw-review-select" id="rvst-${escAttr(id)}">
                <option value="pending">— حكم المراجعة</option>
                <option value="approved"  ${saved && saved.status==='approved'          ? 'selected':''}>✓ موافق — المسألة صحيحة</option>
                <option value="needs_revision" ${saved && saved.status==='needs_revision' ? 'selected':''}>⚠ يحتاج تعديل</option>
                <option value="rejected"  ${saved && saved.status==='rejected'          ? 'selected':''}>✗ غير موافق — خاطئة</option>
            </select>
        </div>
        <textarea class="mw-review-textarea" id="rvc-${escAttr(id)}" placeholder="ملاحظات، تصحيحات، مصادر بديلة...">${escHtml(saved ? saved.comment || '' : '')}</textarea>
        <div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;">
            <button class="btn btn-approve" onclick="saveMwReview('${escAttr(id)}')" style="font-size:.85rem;padding:.32rem .9rem;">حفظ المراجعة</button>
            ${saved ? `<button class="btn btn-reset" onclick="deleteMwReview('${escAttr(id)}')" style="font-size:.8rem;padding:.28rem .7rem;">حذف</button>` : ''}
        </div>
        <div class="mw-review-saved" id="rvsaved-${escAttr(id)}">✓ تم الحفظ</div>
    </div>`;
    }

    html += `</div>`;
    return html;
}

// ─── MwReview helpers ───────────────────────────────────────────

function getMwReview(id) {
    try { return (JSON.parse(localStorage.getItem('mw-reviews') || '{}'))[id] || null; }
    catch { return null; }
}

function applyMwReviewStates() {
    try {
        const all = JSON.parse(localStorage.getItem('mw-reviews') || '{}');
        for (const [id, rv] of Object.entries(all)) {
            const card = document.getElementById(id);
            if (card) {
                card.classList.remove('review-approved','review-rejected','review-needs_revision');
                card.classList.add('review-' + rv.status);
            }
        }
    } catch {}
}

window.toggleMwReview = function(id) {
    const panel = document.getElementById('rvpanel-' + id);
    if (panel) panel.classList.toggle('hidden');
};

window.saveMwReview = async function(id) {
    const scholar = (document.getElementById('rvs-'  + id) || {value:''}).value.trim();
    const status  = (document.getElementById('rvst-' + id) || {value:'pending'}).value;
    const comment = (document.getElementById('rvc-'  + id) || {value:''}).value.trim();
    const data = { scholar, status, comment, savedAt: new Date().toISOString() };

    // Save locally
    try {
        const all = JSON.parse(localStorage.getItem('mw-reviews') || '{}');
        all[id] = data;
        localStorage.setItem('mw-reviews', JSON.stringify(all));
    } catch {}

    // Try posting to API
    try {
        await fetch('/fiqh/api/feedback/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ masala_key: id, scholar_name: scholar, status, comment }),
        });
    } catch {}

    // Update button label
    const btn = document.getElementById('rvbtn-' + id);
    if (btn) {
        const label = status === 'approved' ? 'موافق' : status === 'rejected' ? 'غير موافق' : 'يحتاج تعديل';
        btn.textContent = '✓ ' + label;
        btn.className = `mw-review-toggle has-review status-${status}`;
    }

    // Update card border
    const card = document.getElementById(id);
    if (card) {
        card.classList.remove('review-approved','review-rejected','review-needs_revision');
        card.classList.add('review-' + status);
    }

    // Flash saved indicator
    const savedEl = document.getElementById('rvsaved-' + id);
    if (savedEl) {
        savedEl.style.display = 'flex';
        setTimeout(() => { savedEl.style.display = 'none'; }, 2200);
    }
};

window.deleteMwReview = function(id) {
    try {
        const all = JSON.parse(localStorage.getItem('mw-reviews') || '{}');
        delete all[id];
        localStorage.setItem('mw-reviews', JSON.stringify(all));
    } catch {}
    const btn = document.getElementById('rvbtn-' + id);
    if (btn) { btn.textContent = '+ مراجعة'; btn.className = 'mw-review-toggle'; }
    const card = document.getElementById(id);
    if (card) card.classList.remove('review-approved','review-rejected','review-needs_revision');
    const panel = document.getElementById('rvpanel-' + id);
    if (panel) panel.classList.add('hidden');
};

window.toggleBabGroup = function(babId) {
    const g = document.getElementById(babId);
    if (g) g.classList.toggle('collapsed');
};

window.mwFilterMasail = function(query) {
    const q = query.trim();
    const cards = document.querySelectorAll('.mw-masala-card');
    let shown = 0;
    cards.forEach(c => {
        const match = !q || c.textContent.includes(q);
        c.style.display = match ? '' : 'none';
        if (match) shown++;
    });
    // Update bab group visibility
    document.querySelectorAll('.mw-bab-group').forEach(g => {
        const vis = g.querySelectorAll('.mw-masala-card:not([style*="none"])');
        g.style.display = vis.length ? '' : 'none';
        if (q && vis.length) g.classList.remove('collapsed');
    });
    const icon = document.querySelector('.mw-search-icon');
    if (icon) icon.textContent = q ? `${shown}` : '🔍';
};

// ─── Mind Map View ───────────────────────────────────────────────

async function viewMuwattaKitabMindMap(kitabNum) {
    setActiveNav('nav-masail');
    app.innerHTML = '<div class="loading">جاري بناء الخريطة...</div>';

    const data = await loadMuwatta();
    const kitab = data.kutub.find(k => k.kitab_num == kitabNum);
    if (!kitab) { app.innerHTML = '<div class="empty-state">الكتاب غير موجود</div>'; return; }

    setBreadcrumb([
        { label: 'المسائل', href: '#/masail-home' },
        { label: 'الموطأ', href: '#/muwatta' },
        { label: kitab.kitab_name, href: `#/muwatta/kitab/${kitabNum}` },
        { label: 'خريطة ذهنية' },
    ]);

    const totalMasail = kitab.abwab.reduce((s, b) => s + b.masail.length, 0);

    app.innerHTML = `<div class="page-enter">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;margin-bottom:1rem;">
        <div>
            <h2 class="page-title" style="margin-bottom:0.2rem;">${escHtml(kitab.kitab_name)}</h2>
            <div style="color:var(--cream-dim);font-size:.9rem;">${totalMasail} مسألة — ${kitab.abwab.length} باب</div>
        </div>
        <div class="mw-view-toggle">
            <button onclick="location.hash='#/muwatta/kitab/${kitabNum}'">📋 قائمة</button>
            <button class="active">🗺 خريطة ذهنية</button>
        </div>
    </div>
    <div class="mindmap-wrap" id="mmWrap">
        <canvas id="mmCanvas"></canvas>
        <div class="mindmap-controls">
            <button onclick="mmZoom(0.18)" title="تكبير">＋</button>
            <button onclick="mmZoom(-0.18)" title="تصغير">－</button>
            <button onclick="mmReset()" title="إعادة ضبط">⊙</button>
        </div>
        <div id="mmTooltip" class="mindmap-tooltip"></div>
        <div class="mindmap-hint">اسحب للتنقل · عجلة الفأرة للتكبير · انقر على مسألة للذهاب إليها في القائمة</div>
        <div class="mindmap-legend" id="mmLegend"></div>
    </div></div>`;

    const wrap = document.getElementById('mmWrap');
    const canvas = document.getElementById('mmCanvas');
    canvas.width  = wrap.clientWidth  || 900;
    canvas.height = wrap.clientHeight || 600;

    const mm = {
        nodes: buildMmNodes(kitab, canvas.width, canvas.height),
        pan: { x: 0, y: 0 },
        scale: 1,
        dragging: false,
        hasDragged: false,
        dragStart: null,
        panStart: null,
        kitabNum,
    };
    window._mm = mm;
    window._mmCanvas = canvas;

    drawMm(canvas, mm);
    buildMmLegend();
    attachMmEvents(canvas, mm, kitabNum);
}

const MM_HUKM_COLOR = {
    wajib:'#2D7D46', fard:'#2D7D46', mandub:'#3A8DD4', mustahab:'#3A8DD4',
    sunna:'#3A8DD4', sunna_muakkada:'#3A8DD4', mubah:'#5A6A5A',
    makruh:'#C87A20', haram:'#C0392B', batil:'#C0392B',
    sahih:'#5BA85B', fasid:'#C87A20', fard_kifaya:'#2D7D46',
};

function buildMmNodes(kitab, W, H) {
    const cx = W / 2, cy = H / 2;
    const abwab = kitab.abwab;
    const N = abwab.length;
    const R1 = Math.min(190, Math.max(140, W * 0.20));
    const R2 = R1 + Math.min(195, Math.max(140, W * 0.21));

    const result = { root: { x: cx, y: cy, r: 52, label: kitab.kitab_name }, abwab: [] };

    for (let i = 0; i < N; i++) {
        const bab = abwab[i];
        const angle = (2 * Math.PI * i / N) - Math.PI / 2;
        const bx = cx + R1 * Math.cos(angle);
        const by = cy + R1 * Math.sin(angle);

        const masailNodes = [];
        const masail = bab.masail || [];
        const M = masail.length;
        const spread = Math.min(Math.PI * 0.6, (2 * Math.PI / N) * 0.80);

        for (let j = 0; j < M; j++) {
            const m = masail[j];
            const mAngle = M === 1 ? angle : angle + spread * (j / (M - 1) - 0.5);
            masailNodes.push({
                x: cx + R2 * Math.cos(mAngle),
                y: cy + R2 * Math.sin(mAngle),
                r: 14,
                label: m.masala_topic || m.masala_title || m.title || '',
                masalaId: m.masala_id || m.id || '',
                hukm: m.hukm || '',
            });
        }

        result.abwab.push({
            x: bx, y: by, r: 26,
            label: bab.bab_name || ('باب ' + (bab.bab_num || i + 1)),
            masail: masailNodes,
        });
    }
    return result;
}

function drawMm(canvas, mm) {
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    // Background
    ctx.fillStyle = '#0a1a0a';
    ctx.fillRect(0, 0, W, H);

    // Dot grid
    ctx.fillStyle = 'rgba(200,169,110,0.04)';
    for (let x = 0; x < W; x += 36) for (let y = 0; y < H; y += 36) {
        ctx.beginPath(); ctx.arc(x, y, 1, 0, Math.PI * 2); ctx.fill();
    }

    ctx.save();
    // Transform: pan + scale around center
    ctx.translate(W / 2 + mm.pan.x, H / 2 + mm.pan.y);
    ctx.scale(mm.scale, mm.scale);
    ctx.translate(-W / 2, -H / 2);

    const { root, abwab } = mm.nodes;

    // Edges root → bab
    abwab.forEach(bab => {
        mmEdge(ctx, root.x, root.y, bab.x, bab.y, 'rgba(200,169,110,0.35)', 1.8);
        // Edges bab → masail
        bab.masail.forEach(m => {
            mmEdge(ctx, bab.x, bab.y, m.x, m.y, 'rgba(200,169,110,0.12)', 1);
        });
    });

    // Masail nodes
    abwab.forEach(bab => bab.masail.forEach(m => mmNodeMasala(ctx, m)));
    // Bab nodes
    abwab.forEach(bab => mmNodeBab(ctx, bab));
    // Root
    mmNodeRoot(ctx, root, W, H);

    ctx.restore();
}

function mmEdge(ctx, x1, y1, x2, y2, color, w) {
    ctx.save();
    ctx.strokeStyle = color; ctx.lineWidth = w;
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.restore();
}

function mmNodeRoot(ctx, node, W, H) {
    ctx.save();
    // Glow
    const grd = ctx.createRadialGradient(node.x,node.y,node.r*0.4,node.x,node.y,node.r*2);
    grd.addColorStop(0,'rgba(200,169,110,0.18)'); grd.addColorStop(1,'transparent');
    ctx.fillStyle = grd;
    ctx.beginPath(); ctx.arc(node.x,node.y,node.r*2,0,Math.PI*2); ctx.fill();
    // Outer ring
    ctx.strokeStyle='rgba(200,169,110,0.4)'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.arc(node.x,node.y,node.r+8,0,Math.PI*2); ctx.stroke();
    // Fill
    ctx.fillStyle='#162816'; ctx.strokeStyle='#C8A96E'; ctx.lineWidth=2;
    ctx.beginPath(); ctx.arc(node.x,node.y,node.r,0,Math.PI*2); ctx.fill(); ctx.stroke();
    // Text
    ctx.fillStyle='#C8A96E'; ctx.textAlign='center'; ctx.textBaseline='middle';
    mmWrapText(ctx, node.label, node.x, node.y, node.r * 1.6, 'bold 14px "Amiri",serif', 15);
    ctx.restore();
}

function mmNodeBab(ctx, node) {
    ctx.save();
    ctx.fillStyle='#1A3D24'; ctx.strokeStyle='#2D7D46'; ctx.lineWidth=1.5;
    ctx.beginPath(); ctx.arc(node.x,node.y,node.r,0,Math.PI*2); ctx.fill(); ctx.stroke();
    ctx.fillStyle='#8FD4A0'; ctx.font='12px "Amiri",serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
    const lbl = node.label.length > 10 ? node.label.slice(0,9)+'…' : node.label;
    ctx.fillText(lbl, node.x, node.y);
    ctx.restore();
}

function mmNodeMasala(ctx, node) {
    const color = MM_HUKM_COLOR[node.hukm] || '#4A5A4A';
    ctx.save();
    ctx.fillStyle = color + '30'; ctx.strokeStyle = color; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.arc(node.x,node.y,node.r,0,Math.PI*2); ctx.fill(); ctx.stroke();
    ctx.fillStyle='#E8E0D0'; ctx.font='9.5px "Amiri",serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
    const lbl = node.label.length > 7 ? node.label.slice(0,6)+'…' : node.label;
    ctx.fillText(lbl, node.x, node.y);
    ctx.restore();
}

function mmWrapText(ctx, text, x, y, maxWidth, font, lineH) {
    ctx.font = font;
    if (ctx.measureText(text).width <= maxWidth) { ctx.fillText(text,x,y); return; }
    const words = text.split(' ');
    const lines = []; let cur = '';
    for (const w of words) {
        const t = cur ? cur+' '+w : w;
        if (ctx.measureText(t).width <= maxWidth) cur = t;
        else { if (cur) lines.push(cur); cur = w; }
    }
    if (cur) lines.push(cur);
    const startY = y - (lines.length-1)*lineH/2;
    ctx.font = font;
    lines.forEach((l,i) => ctx.fillText(l, x, startY+i*lineH));
}

function mmHitTest(mm, clientX, clientY, canvas) {
    const rect = canvas.getBoundingClientRect();
    const px = clientX - rect.left, py = clientY - rect.top;
    const W = canvas.width, H = canvas.height;
    const tx = (px - W/2 - mm.pan.x) / mm.scale + W/2;
    const ty = (py - H/2 - mm.pan.y) / mm.scale + H/2;
    for (const bab of mm.nodes.abwab)
        for (const m of bab.masail) {
            const d = Math.hypot(tx-m.x, ty-m.y);
            if (d <= m.r+5) return m;
        }
    return null;
}

function attachMmEvents(canvas, mm, kitabNum) {
    canvas.addEventListener('mousedown', e => {
        mm.dragging = true; mm.hasDragged = false;
        mm.dragStart = {x:e.clientX,y:e.clientY};
        mm.panStart  = {x:mm.pan.x,y:mm.pan.y};
    });
    canvas.addEventListener('mousemove', e => {
        if (mm.dragging) {
            const dx = e.clientX-mm.dragStart.x, dy = e.clientY-mm.dragStart.y;
            if (Math.hypot(dx,dy) > 3) mm.hasDragged = true;
            mm.pan.x = mm.panStart.x + dx; mm.pan.y = mm.panStart.y + dy;
            drawMm(canvas, mm);
        } else {
            const hit = mmHitTest(mm, e.clientX, e.clientY, canvas);
            const tip = document.getElementById('mmTooltip');
            if (hit) {
                const r = canvas.getBoundingClientRect();
                tip.textContent = hit.label + (hit.hukm ? ' — ' + (MM_HUKM_COLOR[hit.hukm] ? hit.hukm : '') : '');
                tip.style.left = (e.clientX - r.left + 12) + 'px';
                tip.style.top  = (e.clientY - r.top  - 28) + 'px';
                tip.classList.add('visible');
                canvas.style.cursor = 'pointer';
            } else {
                tip.classList.remove('visible');
                canvas.style.cursor = 'grab';
            }
        }
    });
    canvas.addEventListener('mouseup', e => {
        if (!mm.hasDragged) {
            const hit = mmHitTest(mm, e.clientX, e.clientY, canvas);
            if (hit && hit.masalaId) {
                location.hash = `#/muwatta/kitab/${kitabNum}`;
                setTimeout(() => {
                    const el = document.getElementById(hit.masalaId);
                    if (el) { el.scrollIntoView({behavior:'smooth',block:'center'}); el.style.outline='2px solid var(--gold)'; setTimeout(()=>{el.style.outline='';},2000); }
                }, 400);
            }
        }
        mm.dragging = false;
    });
    canvas.addEventListener('mouseleave', () => { mm.dragging = false; });
    canvas.addEventListener('wheel', e => {
        e.preventDefault();
        mm.scale = Math.max(0.25, Math.min(4, mm.scale + (e.deltaY < 0 ? 0.1 : -0.1)));
        drawMm(canvas, mm);
    }, { passive: false });
    // Touch
    let tStart = null, tPanStart = null;
    canvas.addEventListener('touchstart', e => {
        if (e.touches.length===1) {
            tStart = {x:e.touches[0].clientX,y:e.touches[0].clientY};
            tPanStart = {x:mm.pan.x,y:mm.pan.y};
            mm.hasDragged = false;
        }
    }, {passive:true});
    canvas.addEventListener('touchmove', e => {
        e.preventDefault();
        if (e.touches.length===1 && tStart) {
            const dx=e.touches[0].clientX-tStart.x, dy=e.touches[0].clientY-tStart.y;
            if (Math.hypot(dx,dy)>5) mm.hasDragged=true;
            mm.pan.x=tPanStart.x+dx; mm.pan.y=tPanStart.y+dy;
            drawMm(canvas,mm);
        }
    }, {passive:false});
    canvas.addEventListener('touchend', () => { tStart = null; }, {passive:true});
}

function buildMmLegend() {
    const legendEl = document.getElementById('mmLegend');
    if (!legendEl) return;
    const items = [
        ['واجب/فرض','#2D7D46'], ['مندوب/سنة','#3A8DD4'],
        ['مباح','#5A6A5A'],    ['مكروه','#C87A20'], ['حرام','#C0392B'],
    ];
    legendEl.innerHTML = items.map(([lbl,col]) =>
        `<div class="mindmap-legend-item"><div class="mindmap-legend-dot" style="background:${col}"></div>${lbl}</div>`
    ).join('');
}

window.mmZoom = function(d) {
    const mm=window._mm, c=window._mmCanvas;
    if (!mm||!c) return;
    mm.scale=Math.max(0.25,Math.min(4,mm.scale+d));
    drawMm(c,mm);
};
window.mmReset = function() {
    const mm=window._mm, c=window._mmCanvas;
    if (!mm||!c) return;
    mm.scale=1; mm.pan={x:0,y:0};
    drawMm(c,mm);
};

async function viewMasailHome() {
    setActiveNav('nav-masail');
    setBreadcrumb([{ label: 'المسائل' }]);
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    // Load all books in parallel
    const [muwatta, mudawwana, risala, khalil] = await Promise.all([
        loadMuwatta(),
        loadMudawwana().catch(() => null),
        loadRisala().catch(() => null),
        loadKhalil().catch(() => null),
    ]);

    function bookStats(data) {
        if (!data) return { masail: 0, abwab: 0 };
        let masail = 0, abwab = 0;
        for (const k of data.kutub) {
            abwab += k.abwab.length;
            for (const b of k.abwab) masail += b.masail.length;
        }
        return { masail, abwab };
    }

    const books = [
        { data: muwatta,   hash: '#/muwatta',   color: 'var(--gold)', title: 'الموطأ — رواية يحيى الليثي' },
        { data: mudawwana, hash: '#/mudawwana', color: '#4CAF50',     title: 'المدونة الكبرى' },
        { data: risala,    hash: '#/risala',    color: '#2196F3',     title: 'الرسالة' },
        { data: khalil,    hash: '#/khalil',    color: '#FF9800',     title: 'مختصر خليل' },
    ];

    let html = `<h2 class="page-title">المسائل الفقهية</h2>
    <div class="cards-grid">`;

    for (const b of books) {
        if (!b.data) continue;
        const s = bookStats(b.data);
        html += `
    <div class="card mw-source-card" onclick="location.hash='${b.hash}'" style="border:2px solid ${b.color};">
        <div class="card-title" style="color:${b.color};">${escHtml(b.title)}</div>
        <div style="color:var(--cream-dim);margin:.3rem 0;">${escHtml(b.data.author)}</div>
        <div class="card-stats">
            <span class="stat-pill ittifaq">${b.data.kutub.length} كتاب</span>
            <span class="stat-pill tafsilat">${s.abwab} باب</span>
            <span class="stat-pill ikhtilaf">${s.masail} مسألة</span>
        </div>
    </div>`;
    }

    html += '</div>';
    app.innerHTML = html;
}

// ===== Generic Book Views (المدونة، الرسالة، خليل) =====

const BOOK_ROUTES = {
    mudawwana: { loader: loadMudawwana, title: 'المدونة الكبرى', color: '#4CAF50' },
    risala:    { loader: loadRisala,    title: 'الرسالة',        color: '#2196F3' },
    khalil:    { loader: loadKhalil,    title: 'مختصر خليل',     color: '#FF9800' },
};

async function viewGenericBook(bookKey) {
    const cfg = BOOK_ROUTES[bookKey];
    if (!cfg) { app.innerHTML = '<div class="empty-state">المصنف غير موجود</div>'; return; }

    setActiveNav('nav-masail');
    setBreadcrumb([
        { label: 'المسائل', href: '#/masail-home' },
        { label: cfg.title },
    ]);
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const data = await cfg.loader();
    const kutub = data.kutub;

    let totalMasail = 0, totalAbwab = 0;
    for (const k of kutub) {
        totalAbwab += k.abwab.length;
        for (const b of k.abwab) totalMasail += b.masail.length;
    }

    let html = `
    <h2 class="page-title">مسائل ${escHtml(cfg.title)}</h2>
    <div style="text-align:center;color:var(--cream-dim);margin-bottom:1rem;">${escHtml(data.author)}</div>
    <div class="stats-bar" style="margin-bottom:1.5rem;">
        <div class="stat-item"><span class="stat-num">${kutub.length}</span><span class="stat-lbl">كتاب</span></div>
        <div class="stat-item"><span class="stat-num">${totalAbwab}</span><span class="stat-lbl">باب</span></div>
        <div class="stat-item"><span class="stat-num">${totalMasail}</span><span class="stat-lbl">مسألة</span></div>
    </div>
    <div class="cards-grid">`;

    for (const k of kutub) {
        const mc = k.masail_count || k.abwab.reduce((s, b) => s + b.masail.length, 0);
        html += `
        <div class="card" onclick="location.hash='#/${bookKey}/kitab/${k.kitab_num}'">
            <div class="card-title">${escHtml(k.kitab_name)}</div>
            <div class="card-stats">
                <span class="stat-pill tafsilat">${k.abwab.length} باب</span>
                <span class="stat-pill ittifaq">${mc} مسألة</span>
            </div>
        </div>`;
    }

    html += '</div>';
    app.innerHTML = html;
}

async function viewGenericBookKitab(bookKey, kitabNum) {
    const cfg = BOOK_ROUTES[bookKey];
    if (!cfg) return;

    setActiveNav('nav-masail');
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const data = await cfg.loader();
    const kitab = data.kutub.find(k => k.kitab_num == kitabNum);
    if (!kitab) { app.innerHTML = '<div class="empty-state">الكتاب غير موجود</div>'; return; }

    setBreadcrumb([
        { label: 'المسائل', href: '#/masail-home' },
        { label: cfg.title, href: `#/${bookKey}` },
        { label: kitab.kitab_name },
    ]);

    const totalMasail = kitab.abwab.reduce((s, b) => s + b.masail.length, 0);

    let html = `<div class="page-enter">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;margin-bottom:1.2rem;">
        <div>
            <h2 class="page-title" style="margin-bottom:0.25rem;">${escHtml(kitab.kitab_name)}</h2>
            <div style="color:var(--cream-dim);font-size:.9rem;">${totalMasail} مسألة — ${kitab.abwab.length} باب</div>
        </div>
    </div>

    <div class="mw-search-wrap">
        <span class="mw-search-icon">🔍</span>
        <input class="mw-search-input" id="mwSearch" type="search" placeholder="ابحث في المسائل..." dir="rtl" oninput="mwFilterMasail(this.value)">
    </div>

    <div id="mwMasailContainer">`;

    for (const bab of kitab.abwab) {
        const babId = 'bab-' + (bab.bab_num || '').toString().replace(/\s+/g, '-');
        html += `
        <div class="mw-bab-group" id="${escHtml(babId)}">
            <div class="mw-bab-group-header" onclick="toggleBabGroup('${escHtml(babId)}')">
                <div>
                    <span class="mw-bab-group-title">${escHtml(bab.bab_name || 'باب')}</span>
                </div>
                <div style="display:flex;align-items:center;gap:.6rem;">
                    <span class="mw-bab-group-count">${bab.masail.length} مسألة</span>
                    <span class="mw-bab-group-arrow">▼</span>
                </div>
            </div>
            <div class="mw-bab-group-body">`;
        for (const m of bab.masail) {
            html += renderMasalaCard(m, bab);
        }
        html += `</div></div>`;
    }

    html += `</div></div>`;
    app.innerHTML = html;
    applyMwReviewStates();
}

// ===== المقارنات (Comparison Views) =====

async function viewComparisonHome() {
    setActiveNav('nav-comparison');
    setBreadcrumb([{ label: 'المقارنات' }]);
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const data = await loadComparison();

    let html = `
    <h2 class="page-title">المقارنات بين المصنفات</h2>
    <div style="text-align:center;color:var(--cream-dim);margin-bottom:1rem;">
        ${escHtml(data.description)}
    </div>
    <div class="stats-bar" style="margin-bottom:1.5rem;">
        <div class="stat-item"><span class="stat-num">${data.total_comparisons}</span><span class="stat-lbl">مقارنة</span></div>
        <div class="stat-item"><span class="stat-num">${data.average_tawafoq.toFixed(1)}%</span><span class="stat-lbl">متوسط توافق</span></div>
        <div class="stat-item"><span class="stat-num">4</span><span class="stat-lbl">مصنف</span></div>
    </div>
    <div class="cards-grid">`;

    for (const kitab of data.kutub) {
        const abwabCount = kitab.abwab.length;
        html += `
        <div class="card" onclick="location.hash='#/comparison/${kitab.kitab_key}'" style="border:2px solid var(--gold);">
            <div class="card-title" style="color:var(--gold);">${escHtml(kitab.kitab_name)}</div>
            <div class="card-stats">
                <span class="stat-pill ittifaq">${abwabCount} باب (موضوع)</span>
            </div>
        </div>`;
    }

    html += '</div>';
    app.innerHTML = html;
}

async function viewComparisonKitab(kitabKey) {
    setActiveNav('nav-comparison');
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const data = await loadComparison();
    const kitab = data.kutub.find(k => k.kitab_key === kitabKey);
    if (!kitab) { app.innerHTML = '<div class="empty-state">الكتاب غير موجود</div>'; return; }

    setBreadcrumb([
        { label: 'المقارنات', href: '#/comparison' },
        { label: kitab.kitab_name },
    ]);

    let html = `<div class="page-enter">
    <h2 class="page-title">${escHtml(kitab.kitab_name)} — المقارنات</h2>
    <div style="color:var(--cream-dim);font-size:.9rem;margin-bottom:1.5rem;">${kitab.abwab.length} باب (موضوع)</div>

    <div class="cards-grid">`;

    for (const bab of kitab.abwab) {
        const m = bab.masail[0];
        if (!m) continue;
        const tawafoq = m.tawafoq_percentage || 0;
        const agreeType = m.agreement_type || 'خلاف';
        const booksCount = (m.books_covered || []).length;

        html += `
        <div class="card" onclick="location.hash='#/comparison/${kitabKey}/bab/${bab.bab_num}'" style="cursor:pointer;">
            <div class="card-title">${escHtml(bab.bab_name)}</div>
            <div class="card-stats" style="margin-top:.5rem;">
                <span style="background:${tawafoq >= 90 ? '#4CAF50' : tawafoq >= 70 ? '#FF9800' : '#f44336'}; color:white; padding:0.25rem 0.75rem; border-radius:12px; font-size:0.8rem; font-weight:bold;">${tawafoq.toFixed(1)}%</span>
                <span class="stat-pill tafsilat">${agreeType}</span>
                <span class="stat-pill ittifaq">${booksCount} مصنف</span>
            </div>
        </div>`;
    }

    html += '</div></div>';
    app.innerHTML = html;
}

async function viewComparisonBab(kitabKey, babNum) {
    setActiveNav('nav-comparison');
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const data = await loadComparison();
    const kitab = data.kutub.find(k => k.kitab_key === kitabKey);
    if (!kitab) { app.innerHTML = '<div class="empty-state">الكتاب غير موجود</div>'; return; }

    const bab = kitab.abwab.find(b => b.bab_num == babNum);
    if (!bab) { app.innerHTML = '<div class="empty-state">الباب غير موجود</div>'; return; }

    setBreadcrumb([
        { label: 'المقارنات', href: '#/comparison' },
        { label: kitab.kitab_name, href: `#/comparison/${kitabKey}` },
        { label: bab.bab_name },
    ]);

    let html = `<div class="page-enter">
    <h2 class="page-title">${escHtml(bab.bab_name)}</h2>`;

    for (const m of bab.masail) {
        const tawafoq = m.tawafoq_percentage || 0;
        const agreeType = m.agreement_type || 'خلاف';
        const books = (m.books_covered || []).join('، ');

        html += `
    <div style="background:${tawafoq >= 90 ? '#4CAF50' : tawafoq >= 70 ? '#FF9800' : '#f44336'}; color:white; padding:0.75rem 1rem; border-radius:8px; font-weight:bold; display:inline-block; margin-bottom:1rem;">
        ${agreeType} ${tawafoq.toFixed(1)}%
    </div>
    <div style="color:var(--cream-dim);font-size:.85rem;margin-bottom:1rem;">المصنفات: ${escHtml(books)} — ${m.entries_count || 0} مدخل</div>

    <section style="margin-top:1rem; padding:1rem; background:var(--dark-border); border-right:3px solid var(--gold);">
        <h3 style="color:var(--gold); margin-top:0;">ما اتفق عليه العلماء</h3>
        <p style="line-height:1.8; color:var(--cream); margin-bottom:0.75rem;">${escHtml(m.consensus_text || 'متفق عليه')}</p>
        <div style="color:var(--gold); font-size:0.9rem;"><strong>الحكم الموحد:</strong> ${hukmBadge(m.consensus_hukm)}</div>
    </section>`;

        // Khalif
        if (m.khalif && m.khalif.length > 0) {
            let khalifHtml = '';
            for (const k of m.khalif) {
                const scholars = (k.scholars || []).filter(s => s).join('، ') || 'غير محدد';
                khalifHtml += `<div style="margin:.5rem 0;"><strong>${hukmBadge(k.hukm)}</strong> — ${escHtml(scholars)} (${k.count || 0})</div>`;
            }
            html += `
    <section style="margin-top:1rem; padding:1rem; background:var(--dark-border); border-right:3px solid #f44336;">
        <h3 style="color:#f44336; margin-top:0;">نقاط الخلاف</h3>
        ${khalifHtml}
    </section>`;
        }

        // Tafsil
        if (m.tafsil && m.tafsil.length > 0) {
            let tafsilHtml = '';
            for (const t of m.tafsil) {
                const speaker = t.speaker || 'عالم';
                const conds = (t.conditions || []).join('، ');
                tafsilHtml += `<div style="margin:.5rem 0;"><strong>${escHtml(speaker)}</strong> (${escHtml(t.book || '')}): ${escHtml(conds)}</div>`;
            }
            html += `
    <section style="margin-top:1rem; padding:1rem; background:var(--dark-border); border-right:3px solid #FF9800;">
        <h3 style="color:#FF9800; margin-top:0;">التفصيلات والشروط</h3>
        ${tafsilHtml}
    </section>`;
        }

        // Scholar positions table
        html += `
    <section style="margin-top:1rem;">
        <h3 style="color:var(--gold);">مواقف العلماء</h3>
        <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; font-size:0.9rem; color:var(--cream);">
        <thead>
            <tr style="background:var(--darker-bg); border-bottom:2px solid var(--gold);">
                <th style="padding:0.75rem; text-align:right; color:var(--gold);">الكتاب</th>
                <th style="padding:0.75rem; text-align:right; color:var(--gold);">العالم</th>
                <th style="padding:0.75rem; text-align:right; color:var(--gold);">الحكم</th>
                <th style="padding:0.75rem; text-align:right; color:var(--gold);">الرابط</th>
            </tr>
        </thead>
        <tbody>`;

        for (const pos of m.positions || []) {
            const shamUrl = pos.shamela_link || '';
            const isLink = shamUrl && shamUrl.startsWith('http');
            html += `
            <tr style="border-bottom:1px solid var(--dark-border);">
                <td style="padding:0.75rem; color:var(--cream-dim);">${escHtml(pos.book || '')}</td>
                <td style="padding:0.75rem;">${escHtml(pos.speaker || '')}</td>
                <td style="padding:0.75rem;">${hukmBadge(pos.hukm)}</td>
                <td style="padding:0.75rem;">
                    ${isLink ? `<a href="${escAttr(shamUrl)}" target="_blank" style="color:var(--gold); text-decoration:none;">الشاملة ↗</a>` : '<span style="color:var(--cream-dim);">—</span>'}
                </td>
            </tr>`;
        }

        html += `</tbody></table></div></section>`;
    }

    html += '</div>';
    app.innerHTML = html;
}

// ===== Views =====

async function viewDashboard() {
    await viewMasailHome();
}

async function viewKitab(kitabKey) {
    setActiveNav('nav-masail');

    // Get kitab name from the dashboard data
    let kutub = [];
    try { const r = await api('/api/kutub'); if (Array.isArray(r)) kutub = r; } catch(e) {}
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
    setActiveNav('nav-masail');
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
    setActiveNav('nav-masail');
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

    const [stats, fbStats, mktStats] = await Promise.all([
        api('/api/stats'),
        api('/api/feedback/stats'),
        api('/api/maktaba/stats'),
    ]);
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
    let allKutub = [];
    try { const r = await api('/api/kutub'); if (Array.isArray(r)) allKutub = r; } catch(e) {}
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

    // Maktaba coverage section
    const mktBy = mktStats.by_status || {};
    html += `<div class="chart-container">
        <h3>تغطية المكتبة (مصنفات الفقه المالكي)</h3>
        <div class="stats-grid" style="margin-bottom:1rem;">
            <div class="stat-card"><div class="stat-number">${mktStats.total_books}</div><div class="stat-label">إجمالي الكتب</div></div>
            <div class="stat-card"><div class="stat-number" style="color:var(--ittifaq)">${mktStats.books_with_pdf}</div><div class="stat-label">متاح رقمياً</div></div>
            <div class="stat-card"><div class="stat-number" style="color:var(--tafsilat)">${mktStats.books_without_pdf}</div><div class="stat-label">غير متاح</div></div>
            <div class="stat-card"><div class="stat-number">${mktStats.reviewed_count}</div><div class="stat-label">كتاب مراجَع</div></div>
            <div class="stat-card"><div class="stat-number">${mktStats.total_reviews}</div><div class="stat-label">إجمالي المراجعات</div></div>
            <div class="stat-card"><div class="stat-number">${mktStats.volume_specific_reviews || 0}</div><div class="stat-label">مراجعات بمجلد محدد</div></div>
        </div>
        <div class="bar-chart">`;
    const statusOrder = [['correct','اتفاق','ittifaq'],['wrong_edition','طبعة خاطئة','tafsilat'],['wrong_book','كتاب مختلف','ikhtilaf'],['comment_only','تعليق','gold'],['pending','معلق','gold']];
    const maxMkt = Math.max(...statusOrder.map(([k]) => mktBy[k] || 0), 1);
    for (const [key, label, cls] of statusOrder) {
        const count = mktBy[key] || 0;
        if (!count) continue;
        const pct = Math.round((count / maxMkt) * 100);
        html += `<div class="bar-row">
            <div class="bar-label">${label}</div>
            <div class="bar-track"><div class="bar-fill ${cls}" style="width:${Math.max(pct,2)}%">${count}</div></div>
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
            await viewMasailHome();
        } else if (hash === '#/masail-home') {
            await viewMasailHome();
        } else if (hash === '#/muwatta') {
            await viewMuwatta();
        } else if (hash.match(/^#\/muwatta\/kitab\/(\d+)\/mindmap$/)) {
            const m = hash.match(/^#\/muwatta\/kitab\/(\d+)\/mindmap$/);
            await viewMuwattaKitabMindMap(parseInt(m[1]));
        } else if (hash.match(/^#\/muwatta\/kitab\/(\d+)$/)) {
            const m = hash.match(/^#\/muwatta\/kitab\/(\d+)$/);
            await viewMuwattaKitab(parseInt(m[1]));
        } else if (hash === '#/mudawwana') {
            await viewGenericBook('mudawwana');
        } else if (hash.match(/^#\/mudawwana\/kitab\/(\d+)$/)) {
            const m = hash.match(/^#\/mudawwana\/kitab\/(\d+)$/);
            await viewGenericBookKitab('mudawwana', parseInt(m[1]));
        } else if (hash === '#/risala') {
            await viewGenericBook('risala');
        } else if (hash.match(/^#\/risala\/kitab\/(\d+)$/)) {
            const m = hash.match(/^#\/risala\/kitab\/(\d+)$/);
            await viewGenericBookKitab('risala', parseInt(m[1]));
        } else if (hash === '#/khalil') {
            await viewGenericBook('khalil');
        } else if (hash.match(/^#\/khalil\/kitab\/(\d+)$/)) {
            const m = hash.match(/^#\/khalil\/kitab\/(\d+)$/);
            await viewGenericBookKitab('khalil', parseInt(m[1]));
        } else if (hash === '#/comparison') {
            await viewComparisonHome();
        } else if (hash.match(/^#\/comparison\/([^/]+)\/bab\/(\d+)$/)) {
            const m = hash.match(/^#\/comparison\/([^/]+)\/bab\/(\d+)$/);
            await viewComparisonBab(m[1], parseInt(m[2]));
        } else if (hash.match(/^#\/comparison\/([^/]+)$/)) {
            const m = hash.match(/^#\/comparison\/([^/]+)$/);
            await viewComparisonKitab(m[1]);
        } else if (hash === '#/maraji3') {
            await viewMaraji3();
        } else if (hash === '#/feedback') {
            await viewFeedback();
        } else if (hash === '#/stats') {
            await viewStats();
        } else if (hash === '#/maktaba') {
            await viewMaktaba();
        } else if (hash.match(/^#\/maktaba\/section\/(.+)$/)) {
            const m = hash.match(/^#\/maktaba\/section\/(.+)$/);
            await viewMaktabaSection(decodeURIComponent(m[1]));
        } else if (hash.match(/^#\/maktaba\/book\/(.+)$/)) {
            const m = hash.match(/^#\/maktaba\/book\/(.+)$/);
            await viewBook(decodeURIComponent(m[1]));
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

// ===== مكتبة المصنفات =====

const BOOK_STATUS_LABELS = {
    correct:       '✓ الكتاب صحيح',
    wrong_edition: '⚠ طبعة خاطئة',
    wrong_book:    '✗ كتاب مختلف',
    comment_only:  '💬 تعليق فقط',
    pending:       '— معلق',
};

async function viewMaktaba() {
    setActiveNav('nav-maktaba');
    setBreadcrumb([{ label: 'المكتبة', href: '#/maktaba' }]);
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const [sections, stats] = await Promise.all([
        api('/api/maktaba/sections'),
        api('/api/maktaba/stats'),
    ]);

    let html = `
    <h2 class="page-title">مكتبة مصنفات الفقه المالكي</h2>
    <div class="stats-bar" style="margin-bottom:1.5rem;">
        <div class="stat-item"><span class="stat-num">${stats.total_books}</span><span class="stat-lbl">كتاب</span></div>
        <div class="stat-item"><span class="stat-num" style="color:var(--green)">${stats.books_with_pdf}</span><span class="stat-lbl">متاح</span></div>
        <div class="stat-item"><span class="stat-num" style="color:var(--gold)">${stats.books_without_pdf}</span><span class="stat-lbl">غير متاح</span></div>
        <div class="stat-item"><span class="stat-num">${stats.reviewed_count}</span><span class="stat-lbl">مراجَع</span></div>
    </div>
    <div class="cards-grid">`;

    for (const s of sections) {
        const pct = Math.round(s.with_pdf / s.total * 100);
        html += `
        <div class="card" onclick="location.hash='#/maktaba/section/${encodeURIComponent(s.section)}'">
            <div class="card-title">${s.label}</div>
            <div style="color:var(--cream-dim);margin:.3rem 0;">${s.period}</div>
            <div style="color:var(--cream-dim);font-size:.85rem;">${s.total} كتاب &mdash; ${s.with_pdf} متاح</div>
            <div class="coverage-bar" style="margin-top:.6rem;">
                <div class="coverage-fill" style="width:${pct}%;background:${pct===100?'var(--green)':pct>50?'var(--gold)':'#c0392b'}"></div>
            </div>
        </div>`;
    }
    html += '</div>';
    app.innerHTML = html;
}

async function viewMaktabaSection(sectionName) {
    setActiveNav('nav-maktaba');
    setBreadcrumb([
        { label: 'المكتبة', href: '#/maktaba' },
        { label: sectionName.split(' - ').slice(1).join(' - ') || sectionName },
    ]);
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const books = await api('/api/maktaba/books');
    const filtered = books.filter(b => b.section === sectionName);

    let html = `<h2 class="page-title">${sectionName}</h2><div class="masail-list">`;
    for (const b of filtered) {
        const statusDot = b.review_count > 0
            ? '<span class="dot dot-green" title="تمت المراجعة"></span>'
            : '<span class="dot dot-gray" title="لم تتم المراجعة"></span>';
        const pdfBadge = b.has_pdf
            ? `<span class="badge badge-ittifaq" style="font-size:.75rem;">PDF ✓</span>`
            : b.book_key === 'book_08'
                ? `<span class="badge badge-ikhtilaf" style="font-size:.75rem;" title="النص المستقل مفقود — مدرجة في البيان والتحصيل">مفقود</span>`
                : `<span class="badge badge-none" style="font-size:.75rem;">غير متاح</span>`;
        html += `
        <div class="masala-item" onclick="location.hash='#/maktaba/book/${encodeURIComponent(b.book_key)}'">
            <div style="display:flex;align-items:center;gap:.5rem;">
                ${statusDot}
                <span class="masala-title">${b.num}. ${b.title}</span>
                ${pdfBadge}
            </div>
            <div style="color:var(--cream-dim);font-size:.85rem;margin-top:.2rem;">
                ${b.author} — ${b.death}
                ${b.review_count > 0 ? `<span style="color:var(--gold);margin-right:.5rem;">(${b.review_count} مراجعة)</span>` : ''}
            </div>
        </div>`;
    }
    html += '</div>';
    app.innerHTML = html;
}

async function viewBook(bookKey) {
    setActiveNav('nav-maktaba');
    app.innerHTML = '<div class="loading">جاري التحميل...</div>';

    const [b, reviews] = await Promise.all([
        api(`/api/maktaba/books/${bookKey}`),
        api(`/api/maktaba/reviews/${bookKey}`),
    ]);
    if (!b || b.error) { app.innerHTML = '<div class="empty-state">الكتاب غير موجود</div>'; return; }
    window._currentBookFiles = b.pdf_files || [];

    setBreadcrumb([
        { label: 'المكتبة', href: '#/maktaba' },
        { label: b.section_label, href: `#/maktaba/section/${encodeURIComponent(b.section)}` },
        { label: b.title },
    ]);

    let pdfBlock;
    if (b.has_pdf && b.pdf_files && b.pdf_files.length > 0) {
        const volRows = b.pdf_files.map((fname, idx) => {
            const url = `/fiqh/api/maktaba/pdf/${b.book_key}/${idx}`;
            const dlUrl = `${url}?dl=1`;
            const label = b.pdf_files.length === 1 ? 'عرض الكتاب' : `مجلد ${idx + 1}`;
            return `
            <div class="vol-row">
                <button onclick="toggleViewer('${url}', ${idx})" class="btn-primary" style="min-width:7rem;flex-shrink:0;">📖 ${label}</button>
                <a href="${dlUrl}" download="${escHtml(fname)}" class="btn-secondary" style="flex-shrink:0;">⬇ تحميل</a>
                <span class="vol-filename" title="${escHtml(fname)}">${escHtml(fname)}</span>
            </div>`;
        }).join('');
        pdfBlock = `
        <div class="book-pdf-block">
            ${b.pdf_files.length > 1 ? `<div style="color:var(--gold);font-size:.88rem;margin-bottom:.4rem;">📚 ${b.pdf_files.length} مجلدات</div>` : ''}
            ${volRows}
        </div>
        <div id="pdf-viewer-wrap" style="display:none;margin:.5rem 0 1.5rem;">
            <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.3rem;">
                <span id="pdf-viewer-label" style="color:var(--cream-dim);font-size:.82rem;"></span>
                <button onclick="closeViewer()" class="btn-secondary" style="font-size:.75rem;padding:.15rem .5rem;">✕ إغلاق</button>
            </div>
            <iframe id="pdf-iframe" src="" style="width:100%;height:82vh;border:1px solid rgba(200,169,110,0.2);border-radius:8px;background:#222;"></iframe>
        </div>`;
    } else {
        const notAvailMsg = b.book_key === 'book_08'
            ? `النص المستقل لهذا الكتاب <strong>مفقود</strong> — العتبية محفوظة مدرجةً ضمن
               <a href="#/maktaba/book/book_28" style="color:var(--gold);text-decoration:underline;">البيان والتحصيل</a>
               لابن رشد الجد (الكتاب رقم 28 في المكتبة — 20 مجلداً)`
            : `الملف غير متاح رقمياً — مخطوط نادر أو حقوق محفوظة`;
        pdfBlock = `
        <div class="book-pdf-block" style="color:var(--gold);">
            ⚠ ${notAvailMsg}
        </div>`;
    }

    let reviewsHtml = '';
    if (reviews.length > 0) {
        reviewsHtml = '<h3 style="color:var(--gold);margin:1.5rem 0 .8rem;">مراجعات العلماء</h3><div class="feedback-list">';
        for (let i = 0; i < reviews.length; i++) {
            const r = reviews[i];
            const volLabel = r.volume_index >= 0
                ? `<span style="color:var(--cream-dim);font-size:.78rem;margin-right:.4rem;">مجلد ${r.volume_index + 1}</span>`
                : '';
            const suggLabel = r.suggested_source
                ? `<div style="color:var(--cream-dim);font-size:.82rem;margin-top:.3rem;">📎 البديل المقترح: <code>${escHtml(r.suggested_source)}</code></div>`
                : '';
            reviewsHtml += `
            <div class="feedback-card">
                <div class="feedback-header">
                    <span class="scholar-name">${escHtml(r.scholar_name || 'مجهول')}</span>
                    ${volLabel}
                    <span class="badge badge-${r.status === 'correct' ? 'ittifaq' : r.status === 'wrong_book' ? 'ikhtilaf' : 'tafsilat'}" style="font-size:.8rem;">
                        ${escHtml(BOOK_STATUS_LABELS[r.status] || r.status)}
                    </span>
                    <span style="color:var(--cream-dim);font-size:.8rem;">${escHtml(r.created_at.split('T')[0])}</span>
                </div>
                ${r.comment ? `<div class="feedback-comment">${escHtml(r.comment)}</div>` : ''}
                ${suggLabel}
            </div>`;
        }
        reviewsHtml += '</div>';
    }

    const deathLine = b.death ? ` &nbsp;|&nbsp; <strong>الوفاة:</strong> ${escHtml(b.death)}` : '';
    const volOptions = b.pdf_files && b.pdf_files.length > 1
        ? `<option value="-1">الكتاب كاملاً</option>` +
          b.pdf_files.map((f, i) => `<option value="${i}">مجلد ${i + 1} — ${escHtml(f)}</option>`).join('')
        : '';
    const volSelector = b.pdf_files && b.pdf_files.length > 1
        ? `<select id="bk-volume" class="review-select">
               <option value="-1">— المجلد المعني (اختياري)</option>
               ${volOptions}
           </select>`
        : `<input type="hidden" id="bk-volume" value="-1">`;

    app.innerHTML = `
    <div class="masala-detail">
        <div class="masala-header">
            <h2>${escHtml(b.num)}. ${escHtml(b.title)}</h2>
            <div style="color:var(--cream-dim);margin:.4rem 0;">
                <strong>المؤلف:</strong> ${escHtml(b.author)}${deathLine} &nbsp;|&nbsp;
                <strong>الحقبة:</strong> ${escHtml(b.period)}
            </div>
            <div style="color:var(--cream-dim);font-size:.85rem;">${escHtml(b.section)}</div>
        </div>

        ${pdfBlock}
        ${reviewsHtml}

        <h3 style="color:var(--gold);margin:1.5rem 0 .8rem;">إضافة مراجعة</h3>
        <div class="feedback-form">
            <input id="bk-scholar" class="review-input" type="text" placeholder="اسم العالم (اختياري)">
            ${volSelector}
            <select id="bk-status" class="review-select">
                <option value="pending">— اختر الحكم</option>
                <option value="correct">✓ الكتاب صحيح — النسخة مناسبة</option>
                <option value="wrong_edition">⚠ الكتاب صحيح لكن الطبعة خاطئة</option>
                <option value="wrong_book">✗ هذا ليس الكتاب المقصود</option>
                <option value="comment_only">💬 تعليق فقط</option>
            </select>
            <input id="bk-source" class="review-input" type="text" placeholder="مصدر بديل مقترح — رقم archive.org أو اسم الطبعة (اختياري)">
            <textarea id="bk-comment" class="review-input" rows="3" placeholder="ملاحظات تفصيلية (اختياري) — كالإشارة إلى طبعة أفضل أو تصحيح المعلومات..."></textarea>
            <button onclick="submitBookReview('${escHtml(bookKey)}')" class="btn-primary" style="margin-top:.5rem;">إرسال المراجعة</button>
        </div>
    </div>`;
}

function closeViewer() {
    const wrap = document.getElementById('pdf-viewer-wrap');
    const iframe = document.getElementById('pdf-iframe');
    if (!wrap) return;
    wrap.style.display = 'none';
    iframe.src = '';
}

function toggleViewer(url, idx) {
    const wrap = document.getElementById('pdf-viewer-wrap');
    const iframe = document.getElementById('pdf-iframe');
    const label = document.getElementById('pdf-viewer-label');
    if (!wrap) return;
    const isSameVol = iframe.getAttribute('data-url') === url;
    if (wrap.style.display === 'none' || !isSameVol) {
        iframe.src = url;
        iframe.setAttribute('data-url', url);
        if (label && idx !== undefined) label.textContent = `مجلد ${idx + 1}`;
        else if (label) label.textContent = '';
        wrap.style.display = 'block';
        wrap.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        wrap.style.display = 'none';
        iframe.src = '';
        iframe.removeAttribute('data-url');
    }
}

async function submitBookReview(bookKey) {
    const scholar  = $('#bk-scholar').value.trim();
    const status   = $('#bk-status').value;
    const comment  = $('#bk-comment').value.trim();
    const source   = ($('#bk-source') || {value: ''}).value.trim();
    const volEl    = $('#bk-volume');
    const volIdx   = volEl ? parseInt(volEl.value, 10) : -1;
    const volFiles = (window._currentBookFiles || []);
    const volFilename = volIdx >= 0 && volFiles[volIdx] ? volFiles[volIdx] : '';

    if (status === 'pending' && !comment) {
        alert('الرجاء اختيار حكم أو كتابة تعليق');
        return;
    }
    try {
        const url = '/api/maktaba/reviews'.replace('/api/', '/fiqh/api/');
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                book_key: bookKey,
                scholar_name: scholar,
                status,
                comment,
                volume_index: volIdx,
                volume_filename: volFilename,
                suggested_source: source,
            }),
        });
        if (res.ok) {
            await viewBook(bookKey);
        } else {
            alert('حدث خطأ أثناء الإرسال');
        }
    } catch (e) { alert('خطأ: ' + e.message); }
}

window.addEventListener('hashchange', route);
window.addEventListener('DOMContentLoaded', () => {
    route();
    // Create dalil popup modal
    const modal = document.createElement('div');
    modal.id = 'dalilModal';
    modal.className = 'dalil-modal-overlay';
    modal.innerHTML = `
        <div class="dalil-modal">
            <div class="dalil-modal-header">
                <span id="dalilModalTitle"></span>
                <button class="dalil-modal-close" onclick="closeDalilPopup()">&times;</button>
            </div>
            <div class="dalil-modal-body" id="dalilModalBody"></div>
            <div class="dalil-modal-footer" id="dalilModalFooter"></div>
        </div>`;
    modal.addEventListener('click', (e) => { if (e.target === modal) closeDalilPopup(); });
    document.body.appendChild(modal);
});

function fixArabicDisplay(text) {
    // Fix ﵎ (Unicode ligature for تبارك وتعالى) display
    return (text || '').replace(/﵎/g, 'تبارك وتعالى').replace(/﵇/g, 'صلى الله عليه وسلم');
}

function showSourcePopup(el) {
    const fullText = el.dataset.fullText || '';
    const shamelaUrl = el.dataset.shamelaUrl || '';
    const pageStart = el.dataset.pageStart || '';
    const pageEnd = el.dataset.pageEnd || '';
    const topic = el.dataset.topic || '';

    const pageInfo = pageStart === pageEnd ? `ص ${pageStart}` : `ص ${pageStart} — ${pageEnd}`;
    document.getElementById('dalilModalTitle').textContent = `${topic} (${pageInfo})`;
    document.getElementById('dalilModalBody').textContent = fixArabicDisplay(fullText);

    const footer = document.getElementById('dalilModalFooter');
    if (shamelaUrl) {
        footer.innerHTML = `<a href="${escAttr(shamelaUrl)}" target="_blank" rel="noopener" class="dalil-shamela-link">📖 عرض في المكتبة الشاملة</a>`;
    } else {
        footer.innerHTML = '';
    }

    document.getElementById('dalilModal').classList.add('active');
}

function showDalilPopup(el) {
    const fullText = el.dataset.fullText || '';
    const shamelaUrl = el.dataset.shamelaUrl || '';
    const type = el.dataset.type || '';
    const num = el.dataset.num || '';
    const grade = el.dataset.hadithGrade || '';

    document.getElementById('dalilModalTitle').textContent = `${type} ${num}`;
    document.getElementById('dalilModalBody').textContent = fixArabicDisplay(fullText);

    const footer = document.getElementById('dalilModalFooter');
    let footerHtml = '';
    if (grade) {
        const gradeColor = grade === 'صحيح' ? '#4CAF50' : grade === 'حسن' ? '#FF9800' : grade === 'ضعيف' ? '#f44336' : 'var(--gold)';
        footerHtml += `<div style="margin-bottom:.5rem;"><span style="background:${gradeColor};color:#fff;padding:.2rem .6rem;border-radius:.3rem;font-size:.85rem;">حكم الحديث: ${escHtml(grade)}</span></div>`;
    }
    if (shamelaUrl) {
        footerHtml += `<a href="${escAttr(shamelaUrl)}" target="_blank" rel="noopener" class="dalil-shamela-link">📖 عرض في المكتبة الشاملة</a>`;
    }
    footer.innerHTML = footerHtml;

    document.getElementById('dalilModal').classList.add('active');
}

function closeDalilPopup() {
    document.getElementById('dalilModal').classList.remove('active');
}

// Scroll-to-top button
window.addEventListener('scroll', () => {
    const btn = document.getElementById('scrollTop');
    if (window.scrollY > 300) {
        btn.style.display = 'flex';
    } else {
        btn.style.display = 'none';
    }
});
