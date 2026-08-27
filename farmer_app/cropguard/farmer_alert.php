<?php
// ============================================================
// farmer_alert.php — Farmer Disease Alert Warning Screen
// Shows urgent local surveillance risk alerts and details.
// ============================================================
session_start();

if (!isset($_SESSION['farmer'])) {
    header('Location: index.php');
    exit;
}

$farmer = $_SESSION['farmer'];
$farmerId = $farmer['farmer_id'];

// Check if there is an active alert for this farmer in the call logs
$callLogFile = __DIR__ . '/data/call_log.json';
$activeAlert = null;

if (file_exists($callLogFile)) {
    $callLog = json_decode(file_get_contents($callLogFile), true) ?: [];
    // Search backwards to find the latest alert for this farmer
    for ($i = count($callLog) - 1; $i >= 0; $i--) {
        if ($callLog[$i]['farmer_id'] === $farmerId) {
            $activeAlert = $callLog[$i];
            break;
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CropGuard — Surveillance Warning</title>
<link rel="stylesheet" href="css/style.css">
<style>
.alert-box {
  background: var(--red-bg);
  border: 1.5px solid var(--red-text);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin: 15px 0;
  color: var(--text-dark);
}
.alert-title {
  color: var(--red-text);
  font-weight: 700;
  font-size: 18px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.alert-meta {
  font-size: 13px;
  margin-bottom: 12px;
  border-bottom: 1px dashed var(--border);
  padding-bottom: 10px;
}
.warning-icon {
  font-size: 28px;
  text-align: center;
  margin: 10px 0;
}
.emergency-text {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 15px;
}
.precautions-list {
  background: var(--white);
  border-radius: var(--radius-md);
  padding: 15px;
  margin-top: 15px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
.precaution-item {
  display: flex;
  gap: 10px;
  font-size: 13px;
  margin-bottom: 10px;
  line-height: 1.4;
}
.precaution-item:last-child {
  margin-bottom: 0;
}
.badge-severe {
  background: var(--red-text);
  color: var(--white);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
</style>
</head>
<body>

<div class="phone">
  <div class="status-bar">
    <span>9:41</span>
    <span class="icons">📶 📡 🔋</span>
  </div>

  <div class="screen">
    <div class="back-row">
      <a href="diagnose.php" class="back-circle">←</a>
      <h2>Surveillance Warning</h2>
    </div>

    <?php if ($activeAlert): ?>
      <div class="warning-icon">🚨</div>
      
      <div class="alert-box">
        <div class="alert-title">
          <span>⚠️</span> URGENT DISEASE ALERT
        </div>
        <div class="alert-meta">
          <strong>Disease:</strong> <?php echo htmlspecialchars($activeAlert['disease']); ?><br>
          <strong>Risk Level:</strong> <span class="badge-severe"><?php echo htmlspecialchars($activeAlert['risk_label']); ?></span><br>
          <strong>Date:</strong> <?php echo htmlspecialchars($activeAlert['timestamp']); ?>
        </div>
        
        <div class="emergency-text">
          Attention, <strong><?php echo htmlspecialchars($farmer['full_name']); ?></strong>. 
          A high concentration of <strong><?php echo htmlspecialchars($activeAlert['disease']); ?></strong> 
          has been geospatial-analysed and confirmed in your immediate agricultural sector.
        </div>
      </div>

      <button type="button" class="btn btn-aux" id="btnTts" onclick="playVoiceAdvisory()" style="width:100%; margin-top:14px; padding:12px; font-size:13px; background:#f0fdf4; border:1px solid #86efac; color:#15803d;">
        🔊 Listen to Voice Advisory (Audio Broadcast)
      </button>

      <div class="precautions-list">
        <h3>🛡️ Required Actions</h3>
        <div style="height: 10px;"></div>
        <div class="precaution-item">
          <span>🚫</span>
          <div><strong>Isolate Crops:</strong> Do not move plant matter, tools or soil between infected fields.</div>
        </div>
        <div class="precaution-item">
          <span>🧴</span>
          <div><strong>Fungicide Treatment:</strong> Apply preventive organic spray (copper-based) to adjacent crops immediately.</div>
        </div>
        <div class="precaution-item">
          <span>👀</span>
          <div><strong>Continuous Inspection:</strong> Monitor leaves daily for lesions and upload photos using CropGuard to update agricultural officers.</div>
        </div>
      </div>
      
    <?php else: ?>
      <div style="text-align: center; margin-top: 50px;">
        <span style="font-size: 48px;">💚</span>
        <h3 style="margin-top: 20px;">No Active Alerts</h3>
        <p style="font-size: 14px; color: var(--text-muted); padding: 0 20px; line-height: 1.5;">
          There are currently no priority disease alerts active in your local sector. Keep monitoring your crops regularly!
        </p>
      </div>
    <?php endif; ?>

    <div style="margin-top: 30px;">
      <a href="diagnose.php" class="btn btn-primary">📷 Back to Diagnose</a>
    </div>
  </div>

  <div class="home-indicator"></div>
</div>

<script>
function playVoiceAdvisory() {
  if (!('speechSynthesis' in window)) {
    alert("Text-to-Speech is not supported in this browser.");
    return;
  }
  window.speechSynthesis.cancel();
  const text = "Urgent Agricultural Disease Warning for <?php echo addslashes($farmer['full_name']); ?>. A confirmed risk of <?php echo addslashes($activeAlert['disease'] ?? 'Crop disease'); ?> has been detected in your agricultural sector. Required actions: Apply protective organic fungicide spray immediately, isolate infected plant debris, and inspect your crops daily.";
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 0.95;
  utter.pitch = 1.0;
  window.speechSynthesis.speak(utter);
}
</script>
</body>
</html>
