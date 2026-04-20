import { initializeApp }        from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider, onAuthStateChanged, signOut }
                                from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import { getFirestore, doc, setDoc, updateDoc, arrayUnion, getDoc }
                                from "https://www.gstatic.com/firebasejs/10.8.1/firebase-firestore.js";

const firebaseConfig = {
    apiKey:            "AIzaSyCBMqN6yUgi-Vjeoe8DHD7n3-O4U8sc21M",
    authDomain:        "paper-slave-db.firebaseapp.com",
    projectId:         "paper-slave-db",
    storageBucket:     "paper-slave-db.firebasestorage.app",
    messagingSenderId: "1042849603597",
    appId:             "1:1042849603597:web:918810d4fa172cf3153544",
    measurementId:     "G-922MP7E2NT"
};

const app      = initializeApp(firebaseConfig);
const auth     = getAuth(app);
const db       = getFirestore(app);
const provider = new GoogleAuthProvider();

let currentUser      = null;
let reportData       = null;
let currentTier      = 'Free';
let graphInstance    = null;
let graphInitialized = false;

// ── 登入狀態監聽 ───────────────────────────────────────────────────
onAuthStateChanged(auth, async (user) => {
    if (user) {
        currentUser = user;
        document.getElementById('login-btn').classList.add('hidden');
        document.getElementById('user-info').classList.remove('hidden');
        document.getElementById('user-name').textContent = user.displayName;
        document.getElementById('guest-cta').classList.add('hidden');
        document.getElementById('guest-landing').classList.add('hidden');
        document.getElementById('logged-in-content').classList.remove('hidden');

        const userRef  = doc(db, "users", user.uid);
        const userSnap = await getDoc(userRef);

        if (userSnap.exists()) {
            const data = userSnap.data();
            currentTier = data.tier || 'Free';
            updateTierBadge(currentTier);
            highlightTierCard(currentTier);
            
            // 同步使用者的領域偏好至 UI 複選標籤
            const prefs = data.domain_preferences || [];
            document.querySelectorAll('.pb-domain-checkbox').forEach(cb => {
                cb.checked = prefs.includes(cb.value);
            });
            
            await fetchReport();
            applyTierView(currentTier);
        } else {
            await setDoc(userRef, {
                email:        user.email,
                name:         user.displayName,
                tier:         'Free',
                liked_papers: [],
                created_at:   new Date()
            });
            await fetchReport();
            applyTierView('Free');
        }
    } else {
        currentUser = null;
        document.getElementById('login-btn').classList.remove('hidden');
        document.getElementById('user-info').classList.add('hidden');
        document.getElementById('guest-cta').classList.remove('hidden');
        document.getElementById('guest-landing').classList.remove('hidden');
        document.getElementById('logged-in-content').classList.add('hidden');
    }
});

// 綁定按鈕事件
document.getElementById('login-btn').addEventListener('click',        () => signInWithPopup(auth, provider));
document.getElementById('hero-login-btn').addEventListener('click',   () => signInWithPopup(auth, provider));
document.getElementById('bottom-login-btn').addEventListener('click', () => signInWithPopup(auth, provider));
document.getElementById('logout-btn').addEventListener('click',        () => signOut(auth));

// ── 領域偏好選擇 ───────────────────────────────────────────────────
document.querySelectorAll('.pb-domain-checkbox').forEach(cb => {
    cb.addEventListener('change', async () => {
        if (!currentUser) return;
        const checkedValues = Array.from(document.querySelectorAll('.pb-domain-checkbox'))
            .filter(box => box.checked)
            .map(box => box.value);
        
        try {
            await updateDoc(doc(db, "users", currentUser.uid), {
                domain_preferences: checkedValues
            });
        } catch (err) {
            console.error("更新領域偏好失敗", err);
            cb.checked = !cb.checked; // 發生錯誤則還原 UI 狀態
        }
    });
});

// ── 讀取 JSON ──────────────────────────────────────────────────────
async function fetchReport() {
    try {
        const res = await fetch('./archive/report_latest.json');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        reportData = await res.json();
    } catch (err) {
        console.error("【開發者提示】無法讀取 report_latest.json。詳細原因：", err);
        console.error("請檢查 GitHub Actions 是否成功執行並 Push 了 archive/ 資料夾。");
        document.getElementById('paper-container').innerHTML =
            `<div class="carousel-item py-20 text-center text-red-400 text-sm">
                無法讀取報告，請確認伺服器已啟動且 JSON 存在。
            </div>`;
    }
}

// ── Tier 視圖總控制 ────────────────────────────────────────────────
function applyTierView(tier) {
    currentTier = tier;
    const labels = { Free: 'Free · 基礎摘要', Pro: 'Pro · AI 深度解析', Ultra: 'Ultra · 完整圖譜' };
    document.getElementById('radar-tier-label').textContent = labels[tier] || '';

    if (reportData) renderCards(reportData.nodes, tier);

    const ultraSec  = document.getElementById('ultra-section');
    const lockedSec = document.getElementById('locked-graph');

    if (tier === 'Ultra') {
        lockedSec.classList.add('hidden');
        ultraSec.style.display = 'block';
        setTimeout(() => ultraSec.classList.remove('hidden-state'), 20);
        renderGraph();
    } else {
        lockedSec.classList.remove('hidden');
        ultraSec.classList.add('hidden-state');
        setTimeout(() => { ultraSec.style.display = 'none'; }, 800);
    }
}

// ── 卡片渲染與輪播指示器 ───────────────────────────────────────────
function renderCards(nodes, tier) {
    const container = document.getElementById('paper-container');
    const dotsContainer = document.getElementById('carousel-dots-container');
    const showPro   = tier === 'Pro' || tier === 'Ultra';

    // 渲染卡片
    container.innerHTML = nodes.map(node => {
        const proBlock = showPro ? `
            <div class="mt-6 pt-6 border-t border-gray-100">
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">核心貢獻</p>
                <p class="text-sm font-semibold text-gray-800 leading-relaxed mb-4">${node.contribution || '—'}</p>
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">研究方向</p>
                <div class="flex flex-col gap-2">
                    ${(node.directions || []).map(d => `<span class="direction-tag">${d}</span>`).join('')}
                </div>
            </div>` : '';

        return `
        <div class="carousel-item bg-white p-8 md:p-10 rounded-3xl border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-300">
            <div class="flex items-center justify-between mb-8">
                <span class="px-2.5 py-1 bg-gray-50 text-gray-500 rounded-lg font-bold text-[10px] uppercase tracking-wider">
                    ${node.group}
                </span>
                <button
                    onclick="likePaper('${node.title.replace(/'/g, "\\'")}', '${node.group}')"
                    class="text-gray-300 hover:text-red-400 transition transform hover:scale-110 active:scale-95"
                    title="加入偏好模型">
                    <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                    </svg>
                </button>
            </div>
            <h4 class="text-xl font-bold tracking-tight leading-snug text-[#1d1d1f] mb-3">${node.title}</h4>
            <p class="text-slate-500 leading-relaxed text-sm">${node.summary}</p>
            ${proBlock}
        </div>`;
    }).join('');

    // 渲染指示點
    dotsContainer.innerHTML = nodes.map((_, i) => 
        `<div class="carousel-dot ${i === 0 ? 'active' : ''}" onclick="scrollToCard(${i})"></div>`
    ).join('');

    // 監聽滾動更新指示點
    container.addEventListener('scroll', () => {
        const scrollLeft = container.scrollLeft;
        const cardWidth = container.querySelector('.carousel-item').offsetWidth + 24; 
        const activeIndex = Math.round(scrollLeft / cardWidth);
        
        const dots = dotsContainer.querySelectorAll('.carousel-dot');
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === activeIndex);
        });
    });
}

window.scrollToCard = (index) => {
    const container = document.getElementById('paper-container');
    const cardWidth = container.querySelector('.carousel-item').offsetWidth + 24;
    container.scrollTo({ left: index * cardWidth, behavior: 'smooth' });
};

// ── Force-Graph 渲染 (無限白板 + 聚類算法) ────────────────────────────
function renderGraph() {
    if (graphInitialized || !reportData) return;
    const container = document.getElementById('graph-container');
    
    // 專業色系定義 (類似 Data Science 視覺化配色)
    const groupColors = {
        'cs.LG': '#4f46e5', // Indigo (機器學習)
        'cs.CR': '#dc2626', // Red (資安)
        'cs.AI': '#059669', // Emerald (人工智慧)
        'default': '#8b5cf6' // Purple
    };

    graphInstance = ForceGraph()(document.getElementById('force-graph-element'))
        .width(container.clientWidth)
        .height(700)
        .backgroundColor('rgba(0,0,0,0)') // 透明背景，露出後方的點陣網格
        .graphData(reportData)
        .nodeId('id')
        
        // 1. 自訂節點繪製：實心資料點 + 微弱光圈
        .nodeCanvasObject((node, ctx, globalScale) => {
            const color = groupColors[node.group] || groupColors['default'];
            const r = 5; 
            
            // 外圍淡淡的光暈
            ctx.beginPath();
            ctx.arc(node.x, node.y, r + 4, 0, 2 * Math.PI, false);
            ctx.fillStyle = color;
            ctx.globalAlpha = 0.15;
            ctx.fill();

            // 核心實心點
            ctx.beginPath();
            ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
            ctx.fillStyle = color;
            ctx.globalAlpha = 1;
            ctx.fill();
            
            // 增加銳利的白色邊線提升立體感
            ctx.lineWidth = 1;
            ctx.strokeStyle = '#ffffff';
            ctx.stroke();
        })
        
        // 2. 懸浮提示框 (玻璃卡片，由 CSS .graph-tooltip 控管外觀)
        .nodeLabel(node => `
            <div style="padding:16px 20px; font-family:system-ui; width: 280px; white-space: normal;">
                <strong style="color:${groupColors[node.group] || '#9ca3af'}; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">${node.group}</strong>
                <span style="color:#ffffff; font-weight:700; font-size:14px; line-height:1.4; display:block; margin-bottom:8px;">${node.title}</span>
                <span style="color:#cbd5e1; font-size:12px; line-height:1.5; display:block;">${node.summary || ''}</span>
            </div>`)
            
        // 3. 連線基礎樣式 (科技感光束設定)
        .linkColor(link => link.is_cross_domain ? 'rgba(168, 85, 247, 0.4)' : 'rgba(100, 116, 139, 0.15)')
        .linkWidth(link => link.is_cross_domain ? 1.5 : 0.8)
        .linkDirectionalParticles(link => link.is_cross_domain ? 3 : 0) // 加入傳輸光點
        .linkDirectionalParticleSpeed(0.008)
        .linkDirectionalParticleWidth(3)
        .linkLineDash(link => link.is_cross_domain ? [4, 4] : null) // 跨域虛線
        
        // 4. 繪製跨域問號徽章 (完全依賴 Canvas 繪圖 API，無 Emoji)
        .linkCanvasObjectMode(() => 'after')
        .linkCanvasObject((link, ctx) => {
            if (!link.is_cross_domain) return;
            const start = link.source;
            const end = link.target;
            if (typeof start !== 'object' || typeof end !== 'object') return;

            // 計算線段中點
            const textPos = {
                x: start.x + (end.x - start.x) / 2,
                y: start.y + (end.y - start.y) / 2
            };

            // 畫白色圓形底色
            ctx.beginPath();
            ctx.arc(textPos.x, textPos.y, 7, 0, 2 * Math.PI, false);
            ctx.fillStyle = '#ffffff';
            ctx.fill();
            
            // 畫紫色邊框
            ctx.lineWidth = 1;
            ctx.strokeStyle = '#a855f7';
            ctx.stroke();

            // 畫上原生的 '?' 文字符號
            ctx.font = 'bold 9px Sans-Serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#a855f7';
            ctx.fillText('?', textPos.x, textPos.y + 0.5); // 微調垂直置中
        })

        // 互動事件
        .onNodeClick(node => {
            graphInstance.centerAt(node.x, node.y, 1000);
            graphInstance.zoom(6, 2000);
        })
        .onLinkClick(link => {
            if (link.is_cross_domain && link.hidden_insight) {
                // 將物件名稱傳給 Modal 顯示
                const sourceTitle = typeof link.source === 'object' ? link.source.id : link.source;
                const targetTitle = typeof link.target === 'object' ? link.target.id : link.target;
                window.openModal(sourceTitle, targetTitle, link.hidden_insight);
            }
        });
        
    // 5. 核心：調整 D3 物理引擎達到「同類相吸、異類相斥」的聚類效果
    // 增強整體節點間的排斥力
    graphInstance.d3Force('charge').strength(-300); 
    // 設定連線距離：跨域線很長(分開領域)，同領域線很短(聚集)
    graphInstance.d3Force('link').distance(link => link.is_cross_domain ? 250 : 30);
    
    graphInitialized = true;
    window.addEventListener('resize', () => graphInstance.width(container.clientWidth));
}

// ── Modals 控制 ────────────────────────────────────────────────────
window.openTierModal = () => {
    const modal = document.getElementById('tier-modal');
    const box   = document.getElementById('tier-modal-content');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    highlightTierCard(currentTier);
    setTimeout(() => {
        box.classList.replace('scale-95',  'scale-100');
        box.classList.replace('opacity-0', 'opacity-100');
    }, 10);
};

window.closeTierModal = () => {
    const box = document.getElementById('tier-modal-content');
    box.classList.replace('scale-100', 'scale-95');
    box.classList.replace('opacity-100', 'opacity-0');
    setTimeout(() => document.getElementById('tier-modal').classList.replace('flex', 'hidden'), 300);
};

window.openModal = (sourceId, targetId, insight) => {
    document.getElementById('modal-nodes').innerText = `${sourceId}  <->  ${targetId}`;
    document.getElementById('modal-text').innerText  = insight;
    const modal = document.getElementById('insight-modal');
    const box   = document.getElementById('modal-content-container');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    setTimeout(() => {
        box.classList.replace('scale-95',  'scale-100');
        box.classList.replace('opacity-0', 'opacity-100');
    }, 10);
}

window.closeModal = () => {
    const box = document.getElementById('modal-content-container');
    box.classList.replace('scale-100', 'scale-95');
    box.classList.replace('opacity-100', 'opacity-0');
    setTimeout(() => document.getElementById('insight-modal').classList.replace('flex', 'hidden'), 300);
};

// ── 方案切換與模擬金流 ──────────────────────────────────────────────
window.setTier = async (tier) => {
    if (!currentUser) { alert("請先登入才能選擇 Agent 方案！"); return; }
    
    // 如果跟目前方案一樣就不做處理
    if (tier === currentTier) {
        alert(`您目前已經是 ${tier} 方案了！`);
        return;
    }

    const cardElement = document.getElementById(`modal-card-${tier}`);
    const originalHTML = cardElement.innerHTML;
    
    try {
        // 1. 切換至 Loading 狀態
        cardElement.style.pointerEvents = 'none';
        cardElement.style.opacity = '0.7';
        cardElement.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full min-h-[160px]">
                <svg class="animate-spin w-8 h-8 text-gray-500 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <p class="font-bold text-gray-800 tracking-tight">🔒 連線安全金流中...</p>
                <p class="text-xs text-gray-400 mt-1">Mocking Gateway</p>
            </div>
        `;

        // 2. 呼叫虛擬金流 Adapter
        const paymentResult = await processMockPayment(tier);
        
        // 3. 金流成功，寫入 Firebase 綁定權限
        if (paymentResult.status === 'success') {
            await updateDoc(doc(db, "users", currentUser.uid), { tier: paymentResult.tier });
            alert(`🎉 升級成功！\n處理序號：${paymentResult.transactionId}\n頁面將重新整理以載入全新權限。`);
            window.location.reload();
        }
    } catch (e) {
        console.error("切換方案或金流失敗", e);
        alert("❌ 升級時發生網路異常或交易失敗。");
        // 4. 錯誤還原
        cardElement.style.pointerEvents = 'auto';
        cardElement.style.opacity = '1';
        cardElement.innerHTML = originalHTML;
    }
};

/**
 * 虛擬金流轉接器 (Mock Payment Adapter)
 * 預留給未來真實 Stripe API 的隔離函數
 */
async function processMockPayment(targetTier) {
    return new Promise((resolve, reject) => {
        // 模擬 2.5 秒的網路處理與授權等待
        setTimeout(() => {
            const randomTxId = 'pi_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36).slice(-4);
            resolve({
                status: 'success',
                tier: targetTier,
                transactionId: randomTxId
            });
        }, 2500);
    });
}

// ── 按讚 ───────────────────────────────────────────────────────────
window.likePaper = async (paperTitle, domain) => {
    if (!currentUser) { alert("請先登入，Agent 才能記住您的偏好！"); return; }
    try {
        await updateDoc(doc(db, "users", currentUser.uid), {
            liked_papers: arrayUnion({ title: paperTitle, domain, timestamp: new Date() })
        });
        alert(`已將《${paperTitle}》加入您的偏好模型。`);
    } catch (e) { console.error("按讚失敗", e); }
};

// ── Badge & Card 高亮 ──────────────────────────────────────────────
function updateTierBadge(tier) {
    const badge = document.getElementById('user-tier-badge');
    badge.textContent = `方案: ${tier}`;
    
    badge.classList.remove('bg-gray-100', 'text-gray-600', 'bg-emerald-100', 'text-emerald-700', 'bg-purple-100', 'text-purple-700', 'border-gray-200', 'border-emerald-200', 'border-purple-200');
    
    if      (tier === 'Pro')   badge.classList.add('bg-emerald-100', 'text-emerald-700', 'border-emerald-200');
    else if (tier === 'Ultra') badge.classList.add('bg-purple-100', 'text-purple-700', 'border-purple-200');
    else                       badge.classList.add('bg-gray-100', 'text-gray-600', 'border-gray-200');
}

function highlightTierCard(tier) {
    const rings = { Free: 'ring-gray-300', Pro: 'ring-emerald-400', Ultra: 'ring-purple-500' };
    ['Free', 'Pro', 'Ultra'].forEach(t => {
        const card = document.getElementById(`modal-card-${t}`);
        if (!card) return;
        card.classList.remove('ring-2', 'ring-offset-2', 'ring-gray-300', 'ring-emerald-400', 'ring-purple-500');
        if (t === tier) card.classList.add('ring-2', 'ring-offset-2', rings[t]);
    });
}

// ── 時鐘 ───────────────────────────────────────────────────────────
setInterval(() => {
    const n = new Date();
    document.getElementById('mac-clock').textContent =
        n.getHours().toString().padStart(2,'0') + ':' + n.getMinutes().toString().padStart(2,'0');
}, 1000);