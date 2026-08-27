<?php
// =====================================================================
// expert_review.php — Agricultural Expert & Pathologist Validation Portal
// -----------------------------------------------------------------
// Official verification gateway closing the AI -> Expert -> Farmer loop.
// =====================================================================
session_start();
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CropGuard — Agricultural Expert Validation Portal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@2.47.0/dist/tabler-icons.min.css">
<style>
:root {
  --bg-dark: #0f172a;
  --panel-bg: #1e293b;
  --card-bg: #273549;
  --border: rgba(255,255,255,0.08);
  --text-main: #f8fafc;
  --text-sub: #94a3b8;
  --accent-green: #10b981;
  --accent-red: #ef4444;
  --accent-amber: #f59e0b;
  --accent-blue: #3b82f6;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg-dark);
  color: var(--text-main);
  padding: 24px;
  min-height: 100vh;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 16px;
}
.logo-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-green);
  display: flex;
  align-items: center;
  gap: 8px;
}
.badge-portal {
  background: rgba(16,185,129,0.15);
  color: var(--accent-green);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  border: 1px solid rgba(16,185,129,0.3);
}
.nav-links {
  display: flex;
  gap: 12px;
}
.btn-link {
  background: var(--panel-bg);
  color: var(--text-main);
  text-decoration: none;
  font-size: 12px;
  padding: 8px 14px;
  border-radius: 6px;
  border: 1px solid var(--border);
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-link:hover {
  background: var(--card-bg);
  border-color: var(--accent-green);
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
}
.stat-val {
  font-size: 28px;
  font-weight: 700;
  margin-top: 4px;
}
.stat-label {
  font-size: 11px;
  color: var(--text-sub);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.grid-main {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 20px;
}
.card-table {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
th, td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
th {
  background: rgba(0,0,0,0.15);
  color: var(--text-sub);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
}
tr:hover {
  background: rgba(255,255,255,0.02);
}
.img-thumb {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  object-fit: cover;
  border: 1px solid var(--border);
  cursor: pointer;
}
.status-pill {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}
.status-pending { background: rgba(245,158,11,0.2); color: var(--accent-amber); }
.status-confirmed { background: rgba(16,185,129,0.2); color: var(--accent-green); }
.status-rejected { background: rgba(239,68,68,0.2); color: var(--accent-red); }

.review-panel {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.preview-img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #000;
}
.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  border-bottom: 1px dashed rgba(255,255,255,0.05);
  padding-bottom: 6px;
}
.info-key { color: var(--text-sub); }
.info-val { font-weight: 600; }
.actions-row {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.btn-action {
  flex: 1;
  padding: 10px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: opacity 0.2s;
}
.btn-confirm { background: var(--accent-green); color: #fff; }
.btn-reject { background: var(--accent-red); color: #fff; }
.btn-action:hover { opacity: 0.9; }
textarea.notes-box {
  width: 100%;
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: #fff;
  border-radius: 6px;
  padding: 8px;
  font-size: 12px;
  font-family: inherit;
  resize: vertical;
  height: 60px;
}
</style>
</head>
<body>

<div class="header">
  <div class="logo-title">
    <i class="ti ti-microscope"></i> CropGuard Expert Validation Portal
    <span class="badge-portal">PATHOLOGY GATEWAY</span>
  </div>
  <div class="nav-links">
    <a href="diagnose.php" class="btn-link"><i class="ti ti-device-mobile"></i> Farmer App</a>
    <a href="dashboard/agri_disease_surveillance_dashboard.html" class="btn-link"><i class="ti ti-dashboard"></i> Official Dashboard</a>
  </div>
</div>

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-label">Pending Reviews</div>
    <div class="stat-val" id="statPending" style="color:var(--accent-amber)">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Confirmed Outbreaks</div>
    <div class="stat-val" id="statConfirmed" style="color:var(--accent-green)">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Total Observations</div>
    <div class="stat-val" id="statTotal">0</div>
  </div>
</div>

<div class="grid-main">
  <div class="card-table">
    <div class="card-header">
      <span class="card-title">Live Field Observations Queue</span>
      <button class="btn-link" onclick="loadData()"><i class="ti ti-refresh"></i> Refresh</button>
    </div>
    <table>
      <thead>
        <tr>
          <th>Photo</th>
          <th>ID</th>
          <th>Farmer</th>
          <th>Crop</th>
          <th>YOLO Disease</th>
          <th>Confidence</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody id="obsTableBody">
        <tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-sub)">Loading observation queue...</td></tr>
      </tbody>
    </table>
  </div>

  <div class="review-panel" id="reviewPanel">
    <div style="font-size:13px;font-weight:600;border-bottom:1px solid var(--border);padding-bottom:8px">
      Inspection & Decision Panel
    </div>
    <img id="selectedImg" class="preview-img" src="" alt="Selected leaf specimen">
    
    <div class="info-row"><span class="info-key">Observation ID</span><span class="info-val" id="pObsId">—</span></div>
    <div class="info-row"><span class="info-key">Farmer</span><span class="info-val" id="pFarmer">—</span></div>
    <div class="info-row"><span class="info-key">Target Crop</span><span class="info-val" id="pCrop">—</span></div>
    <div class="info-row"><span class="info-key">YOLO Diagnosis</span><span class="info-val" id="pDisease" style="color:var(--accent-amber)">—</span></div>
    <div class="info-row"><span class="info-key">AI Confidence</span><span class="info-val" id="pConfidence">—</span></div>
    <div class="info-row"><span class="info-key">Location</span><span class="info-val" id="pLocation">—</span></div>

    <div>
      <label style="font-size:11px;color:var(--text-sub);display:block;margin-bottom:4px">Expert Agronomic Notes & Instructions:</label>
      <textarea id="expertNotes" class="notes-box" placeholder="Enter biological confirmation notes or specific treatment guidance..."></textarea>
    </div>

    <div class="actions-row">
      <button class="btn-action btn-confirm" onclick="submitDecision('CONFIRM')"><i class="ti ti-check"></i> CONFIRM</button>
      <button class="btn-action btn-reject" onclick="submitDecision('REJECT')"><i class="ti ti-x"></i> REJECT</button>
    </div>
  </div>
</div>

<script>
let currentObs = null;
let allObservations = [];

function loadData() {
  fetch('api/get_observations.php')
    .then(r => r.json())
    .then(data => {
      if (!data.success) return;
      allObservations = data.observations || [];
      renderTable(allObservations);
      updateStats(allObservations);
      if (allObservations.length > 0 && !currentObs) {
        selectObs(allObservations[0]);
      }
    });
}

function updateStats(list) {
  let pending = list.filter(o => (o.validation_status || 'PENDING') === 'PENDING').length;
  let confirmed = list.filter(o => (o.validation_status || 'PENDING') === 'CONFIRMED').length;
  document.getElementById('statPending').textContent = pending;
  document.getElementById('statConfirmed').textContent = confirmed;
  document.getElementById('statTotal').textContent = list.length;
}

function renderTable(list) {
  const tbody = document.getElementById('obsTableBody');
  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:24px;color:var(--text-sub)">No observations found.</td></tr>';
    return;
  }

  tbody.innerHTML = list.slice().reverse().map(obs => {
    const status = obs.validation_status || 'PENDING';
    const statusClass = status === 'CONFIRMED' ? 'status-confirmed' : (status === 'REJECTED' ? 'status-rejected' : 'status-pending');
    const confStr = Math.round((obs.confidence || 0) * 100) + '%';
    const imgPath = obs.image_path || 'uploads/sample_leaf.jpg';

    return `
      <tr onclick="selectObsById('${obs.observation_id}')" style="cursor:pointer">
        <td><img src="${imgPath}" class="img-thumb" alt="specimen"></td>
        <td><strong>${obs.observation_id}</strong></td>
        <td>${obs.farmer_name || obs.farmer_id}</td>
        <td>${obs.crop || 'Tomato'}</td>
        <td>${obs.disease}</td>
        <td>${confStr}</td>
        <td><span class="status-pill ${statusClass}">${status}</span></td>
        <td><button class="btn-link" style="padding:4px 8px">Inspect</button></td>
      </tr>
    `;
  }).join('');
}

function selectObsById(id) {
  const found = allObservations.find(o => o.observation_id === id);
  if (found) selectObs(found);
}

function selectObs(obs) {
  currentObs = obs;
  document.getElementById('selectedImg').src = obs.image_path || '';
  document.getElementById('pObsId').textContent = obs.observation_id;
  document.getElementById('pFarmer').textContent = (obs.farmer_name || 'Farmer') + ' (' + obs.farmer_id + ')';
  document.getElementById('pCrop').textContent = obs.crop || 'Tomato';
  document.getElementById('pDisease').textContent = obs.disease;
  document.getElementById('pConfidence').textContent = Math.round((obs.confidence || 0) * 100) + '% Accuracy';
  document.getElementById('pLocation').textContent = (obs.latitude ? obs.latitude.toFixed(4) : '9.2712') + ', ' + (obs.longitude ? obs.longitude.toFixed(4) : '76.4721');
  document.getElementById('expertNotes').value = obs.expert_notes || (obs.disease + ' confirmed. Proceed with targeted bio-fungicide treatment.');
}

function submitDecision(action) {
  if (!currentObs) {
    alert('Please select an observation first.');
    return;
  }
  const notes = document.getElementById('expertNotes').value;

  fetch('api/expert_review.php', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      observation_id: currentObs.observation_id,
      action: action,
      expert_name: 'Dr. Ananya Sharma (Lead Pathologist)',
      expert_notes: notes
    })
  })
  .then(r => r.json())
  .then(res => {
    if (res.success) {
      alert(`Decision recorded successfully: [${action}] for ${currentObs.observation_id}. Advisory dispatched to farmer.`);
      loadData();
    } else {
      alert('Error: ' + res.error);
    }
  })
  .catch(err => alert('Failed to record decision: ' + err.message));
}

loadData();
setInterval(loadData, 5000);
</script>

</body>
</html>
