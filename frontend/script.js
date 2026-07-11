 // ── Landmark indices (MediaPipe Pose) ──
const LM = {
  NOSE: 0,
  L_SHOULDER: 11, R_SHOULDER: 12,
  L_ELBOW: 13,    R_ELBOW: 14,
  L_WRIST: 15,    R_WRIST: 16,
  L_HIP: 23,      R_HIP: 24,
  L_KNEE: 25,     R_KNEE: 26,
  L_ANKLE: 27,    R_ANKLE: 28,
};

// ── Angle math ──
function angle(a, b, c) {
  // Angle at point b, formed by a-b-c
  const ab = { x: a.x - b.x, y: a.y - b.y };
  const cb = { x: c.x - b.x, y: c.y - b.y };
  const dot = ab.x * cb.x + ab.y * cb.y;
  const mag = Math.sqrt(ab.x**2 + ab.y**2) * Math.sqrt(cb.x**2 + cb.y**2);
  if (mag === 0) return 0;
  return Math.round(Math.acos(Math.max(-1, Math.min(1, dot / mag))) * 180 / Math.PI);
}

function midpoint(a, b) {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
}

// ── Analysis engine ──
/* function analyzeGait(lm) { 
  const weights = {
  'Knee Drive Angle': 1.2,
  'Trunk Lean': 1.0,
  'Hip Drop': 1.3,
  'Arm Angle': 0.9,
  'Stride Symmetry': 1.4
};

  let weightedScore = 0;
  let totalWeight = 0;
  const metrics = [];
  let totalScore = 0;
  let count = 0;

  // Helper: visibility check
  function vis(idx) {
    return lm[idx] && lm[idx].visibility > 0.5;
  }

  // 1. Knee Drive (left) — angle at knee: hip-knee-ankle, ideal 85-110° at drive phase
  if (vis(LM.L_HIP) && vis(LM.L_KNEE) && vis(LM.L_ANKLE)) {
    const kneeAngle = angle(lm[LM.L_HIP], lm[LM.L_KNEE], lm[LM.L_ANKLE]);
    let status, feedback, score;
    if (kneeAngle >= 80 && kneeAngle <= 115) {
      status = 'good'; feedback = 'Excellent knee drive — optimal power generation range.'; score = 95;
    } else if (kneeAngle < 80) {
      status = 'warn'; feedback = 'Knee over-flexed. May indicate fatigue or overstriding.'; score = 65;
    } else {
      status = 'warn'; feedback = 'Knee under-flexed. Try driving the knee higher for better propulsion.'; score = 60;
    }
    metrics.push({ name: 'Knee Drive Angle', value: `${kneeAngle}°`, ideal: '80–115°', status, feedback, score, bar: Math.min(100, (kneeAngle / 130) * 100) });
    const w = weights['Knee Drive Angle']; // or correct metric name
    weightedScore += score * w;
    totalWeight += w;
  }

  // 2. Trunk Lean — angle of torso from vertical (shoulder to hip vs vertical)
  if (vis(LM.L_SHOULDER) && vis(LM.L_HIP)) {
    const dx = lm[LM.L_SHOULDER].x - lm[LM.L_HIP].x;
    const dy = lm[LM.L_SHOULDER].y - lm[LM.L_HIP].y;
    const leanAngle = Math.round(Math.abs(Math.atan2(dx, -dy) * 180 / Math.PI));
    let status, feedback, score;
    if (leanAngle >= 5 && leanAngle <= 15) {
      status = 'good'; feedback = 'Ideal forward lean. Gravity is working with you.'; score = 95;
    } else if (leanAngle < 5) {
      status = 'warn'; feedback = 'Too upright. A slight forward lean improves efficiency.'; score = 70;
    } else if (leanAngle <= 25) {
      status = 'warn'; feedback = 'Slightly excessive lean. Risk of losing balance at pace.'; score = 65;
    } else {
      status = 'bad'; feedback = 'Excessive trunk lean detected — high injury risk to lower back.'; score = 30;
    }
    metrics.push({ name: 'Trunk Lean', value: `${leanAngle}°`, ideal: '5–15°', status, feedback, score, bar: Math.min(100, 100 - Math.max(0, leanAngle - 15) * 3) });
    const w = weights['Trunk Lean']; // or correct metric name
    weightedScore += score * w;
    totalWeight += w;
  }

  // 3. Hip Drop (Trendelenburg) — difference in hip heights, ideal < 5% of height
  if (vis(LM.L_HIP) && vis(LM.R_HIP)) {
    const hipDiff = Math.abs(lm[LM.L_HIP].y - lm[LM.R_HIP].y);
    const hipDrop = Math.round((hipDiff / 0.25) * 100);
    const hipDropClamped = Math.min(100, hipDrop);
    let status, feedback, score;
    if (hipDrop <= 3) {
      status = 'good'; feedback = 'Hips are level — strong glute medius activation.'; score = 95;
    } else if (hipDrop <= 7) {
      status = 'warn'; feedback = 'Mild hip drop. Glute strengthening exercises recommended.'; score = 65;
    } else {
      status = 'bad'; feedback = 'Significant hip drop (Trendelenburg sign). High IT band and knee injury risk.'; score = 30;
    }
    metrics.push({ name: 'Hip Drop', value: `${hipDrop}%`, ideal: '<3%', status, feedback, score, bar: Math.max(0, 100 - hipDrop * 8) });
    const w = weights['Hip Drop']; // or correct metric name
    weightedScore += score * w;
    totalWeight += w;
  }

  // 4. Arm Angle — elbow flexion during sprint, ideal 85-100°
  if (vis(LM.L_SHOULDER) && vis(LM.L_ELBOW) && vis(LM.L_WRIST)) {
    const armAngle = angle(lm[LM.L_SHOULDER], lm[LM.L_ELBOW], lm[LM.L_WRIST]);
    let status, feedback, score;
    if (armAngle >= 80 && armAngle <= 105) {
      status = 'good'; feedback = 'Optimal arm carriage. ~90° elbow bend maximizes arm drive efficiency.'; score = 95;
    } else if (armAngle < 80) {
      status = 'warn'; feedback = 'Arms too tight. Relax and allow a natural 90° bend.'; score = 70;
    } else {
      status = 'warn'; feedback = 'Arms too extended. Tighten elbow angle for better power transfer.'; score = 65;
    }
    metrics.push({ name: 'Arm Angle', value: `${armAngle}°`, ideal: '80–105°', status, feedback, score, bar: Math.min(100, (armAngle / 120) * 100) });
    const w = weights['Arm Angle']; // or correct metric name
    weightedScore += score * w;
    totalWeight += w;
  }

  // 5. Stride Symmetry — compare left vs right knee angles
  if (vis(LM.L_HIP) && vis(LM.L_KNEE) && vis(LM.L_ANKLE) &&
      vis(LM.R_HIP) && vis(LM.R_KNEE) && vis(LM.R_ANKLE)) {
    const leftKnee = angle(lm[LM.L_HIP], lm[LM.L_KNEE], lm[LM.L_ANKLE]);
    const rightKnee = angle(lm[LM.R_HIP], lm[LM.R_KNEE], lm[LM.R_ANKLE]);
    const diff = Math.abs(leftKnee - rightKnee);
    const symmetry = Math.round(100 - (diff / 1.8));
    let status, feedback, score;
    if (diff <= 10) {
      status = 'good'; feedback = `Left/right stride well-matched (${diff}° difference). Low asymmetry injury risk.`; score = 95;
    } else if (diff <= 20) {
      status = 'warn'; feedback = `Moderate asymmetry (${diff}° difference). May indicate muscle imbalance.`; score = 65;
    } else {
      status = 'bad'; feedback = `High asymmetry (${diff}° difference). Consult a physio — compensation pattern detected.`; score = 35;
    }
    metrics.push({ name: 'Stride Symmetry', value: `${Math.max(0, symmetry)}%`, ideal: '>90%', status, feedback, score, bar: Math.max(0, symmetry) });
    const w = weights['Stride Symmetry']; // or correct metric name
    weightedScore += score * w;
    totalWeight += w;
  }

  const overall = totalWeight > 0 
    ? Math.round(weightedScore / totalWeight) 
    : null;
  return { metrics, overall };
} */

// ── Generate coaching feedback bullets ──
/* function generateFeedback(metrics) {
  const items = [];
  const bad = metrics.filter(m => m.status === 'bad');
  const warn = metrics.filter(m => m.status === 'warn');
  const good = metrics.filter(m => m.status === 'good');

  bad.forEach(m => items.push({ icon: '🔴', text: m.feedback }));
  warn.forEach(m => items.push({ icon: '🟡', text: m.feedback }));
  if (good.length === metrics.length) items.push({ icon: '🟢', text: 'Outstanding form across all measured metrics. Focus on maintaining this at race pace.' });
  else if (good.length > 0) good.slice(0, 2).forEach(m => items.push({ icon: '🟢', text: m.feedback }));
  if (items.length === 0) items.push({ icon: '⚪', text: 'Not enough landmarks visible. Try a clearer full-body image.' });

  return items;
} */

// ── DOM refs ──
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const statusBar = document.getElementById('statusBar');
const statusText = document.getElementById('statusText');
const errorMsg = document.getElementById('errorMsg');
const analysisWrap = document.getElementById('analysisWrap');
const outputCanvas = document.getElementById('outputCanvas');
const overallScore = document.getElementById('overallScore');
const overallDesc = document.getElementById('overallDesc');
const metricsContainer = document.getElementById('metricsContainer');
const feedbackContainer = document.getElementById('feedbackContainer');
const resetBtn = document.getElementById('resetBtn');
const backendSummary = document.getElementById('backendSummary');

let poseModel = null;
let modelLoading = false;

function showStatus(text) {
  statusBar.classList.add('show');
  statusText.textContent = text;
  dropzone.classList.add('scanning');
}

function hideStatus() {
  statusBar.classList.remove('show');
  dropzone.classList.remove('scanning');
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.add('show');
  hideStatus();
}

function clearError() {
  errorMsg.classList.remove('show');
}

/* function renderResults(metrics, overall) {
  // Overall score
  const scoreClass = overall >= 80 ? 'good' : overall >= 60 ? 'warn' : 'bad';
  const scoreLabel = overall >= 80 ? 'Excellent form' : overall >= 60 ? 'Needs improvement' : 'High injury risk';
  overallScore.textContent = overall !== null ? overall : '—';
  overallScore.className = `score-value ${scoreClass}`;
  overallDesc.textContent = overall !== null ? scoreLabel : 'Not enough landmarks visible';

  // Metric rows
  metricsContainer.innerHTML = metrics.map(m => `
    <div class="metric-row">
      <div class="metric-top">
        <span class="metric-name">${m.name}</span>
        <span class="metric-val ${m.status}">${m.value} <span style="color:var(--muted);font-size:11px">(${m.ideal})</span></span>
      </div>
      <div class="metric-bar-track">
        <div class="metric-bar-fill ${m.status}" style="width:${m.bar}%"></div>
      </div>
      <div class="metric-feedback">${m.feedback}</div>
    </div>
  `).join('');

  if (metrics.length === 0) {
    metricsContainer.innerHTML = '<div class="metric-row" style="color:var(--muted);font-size:13px">No metrics could be calculated. Ensure the full body is visible.</div>';
  }

  // Coaching feedback
  const feedbackItems = generateFeedback(metrics);
  feedbackContainer.innerHTML = feedbackItems.map(f => `
    <div class="feedback-item">
      <span class="feedback-icon">${f.icon}</span>
      <span>${f.text}</span>
    </div>
  `).join('');
} */

// ── File handling ──

function renderBackendSummary(summary) {

    if (!summary) return;

    backendSummary.innerHTML = `

    <div class="metric-row">
        <div class="metric-top">
            <span class="metric-name">
                Left Knee Average
            </span>

            <span class="metric-val good">
                ${summary.left_knee.average.toFixed(1)}°
            </span>
        </div>
    </div>


    <div class="metric-row">
        <div class="metric-top">
            <span class="metric-name">
                Left Knee Range
            </span>

            <span class="metric-val">
                ${summary.left_knee.minimum.toFixed(1)}°
                -
                ${summary.left_knee.maximum.toFixed(1)}°
            </span>
        </div>
    </div>


    <div class="metric-row">
        <div class="metric-top">
            <span class="metric-name">
                Right Knee Average
            </span>

            <span class="metric-val good">
                ${summary.right_knee.average.toFixed(1)}°
            </span>
        </div>
    </div>


    <div class="metric-row">
        <div class="metric-top">
            <span class="metric-name">
                Right Knee Range
            </span>

            <span class="metric-val">
                ${summary.right_knee.minimum.toFixed(1)}°
                -
                ${summary.right_knee.maximum.toFixed(1)}°
            </span>
        </div>
    </div>

    `;
}

function renderBackendScore(score) {

    overallScore.textContent = score;

    const scoreClass =
        score >= 80 ? "good" :
        score >= 60 ? "warn" :
        "bad";

    overallScore.className = `score-value ${scoreClass}`;

    overallDesc.textContent =
        score >= 80
            ? "Excellent form"
            : score >= 60
            ? "Needs improvement"
            : "High injury risk";
}

function renderBackendFeedback(feedback) {

    feedbackContainer.innerHTML = feedback.map(item => `
        <div class="feedback-item">
            <span class="feedback-icon">•</span>
            <span>${item}</span>
        </div>
    `).join("");

}

async function handleFile(file) {

    const formData = new FormData();

    formData.append("file", file);

    showStatus("Uploading video...");

    const response = await fetch(
        "http://127.0.0.1:8000/upload",
        {
            method: "POST",
            body: formData
        }
    );

    const data = await response.json();
    hideStatus();

    analysisWrap.classList.add("show");

    const canvasPanel = document.querySelector(".canvas-panel");

    canvasPanel.innerHTML = `
    <div class="canvas-panel-header">
        <span class="mono">ANALYZED VIDEO</span>
        <span class="live-dot mono">PROCESSED</span>
    </div>

    <video
        controls
        autoplay
        style="width:100%;display:block"
    >
        <source src="${data.video}" type="video/mp4">
    </video>
    `;

    renderBackendSummary(data.analysis.summary);
    renderBackendScore(data.analysis.score);
    renderBackendFeedback(data.analysis.feedback);

    console.log(data);
}

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); } });
fileInput.addEventListener('change', e => handleFile(e.target.files[0]));

['dragenter', 'dragover'].forEach(evt => dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.add('drag'); }));
['dragleave', 'drop'].forEach(evt => dropzone.addEventListener(evt, e => { e.preventDefault(); dropzone.classList.remove('drag'); }));
dropzone.addEventListener('drop', e => handleFile(e.dataTransfer.files[0]));

resetBtn.addEventListener('click', () => {
    backendSummary.innerHTML = '';
    analysisWrap.classList.remove('show');
    fileInput.value = '';
    clearError();
    overallScore.textContent = '—';
    metricsContainer.innerHTML = '';
    feedbackContainer.innerHTML = '';
});

// Preload model in background after 2s
setTimeout(() => loadModel().catch(() => {}), 2000);