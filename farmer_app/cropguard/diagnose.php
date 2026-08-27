<?php
// ============================================================
// diagnose.php — Upload / drop a leaf photo, then Analyze.
// Supports Voice Input, GPS, Field Selection, Multilingual UI,
// and Follow-up Recovery Submissions.
// ============================================================
session_start();

if (!isset($_SESSION['farmer'])) {
    header('Location: index.php');
    exit;
}

require_once __DIR__ . '/includes/DatabaseManager.php';
$db = new DatabaseManager();

$farmer     = $_SESSION['farmer'];
$farmerId   = $farmer['farmer_id'];
$firstName  = explode(' ', trim($farmer['full_name']))[0];
$initials   = strtoupper(substr($farmer['full_name'], 0, 1));

// Load farmer fields
$fields = $db->findWhere('fields', 'farmer_id', $farmerId);

// Check for active surveillance alert in local call log database
$callLogFile = __DIR__ . '/data/call_log.json';
$hasActiveAlert = false;
$activeDisease = '';
if (file_exists($callLogFile)) {
    $callLog = json_decode(file_get_contents($callLogFile), true) ?: [];
    for ($i = count($callLog) - 1; $i >= 0; $i--) {
        if (($callLog[$i]['farmer_id'] ?? '') === $farmerId) {
            $hasActiveAlert = true;
            $activeDisease = $callLog[$i]['disease'];
            break;
        }
    }
}

$region = 'Kerala Sector — North';
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CropGuard — Diagnose Crop</title>
<link rel="stylesheet" href="css/style.css">
<style>
.top-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.lang-select {
  background: var(--surface-1, #f1f5f9);
  border: 1px solid var(--border, #cbd5e1);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dark, #0f172a);
}
.notification-banner {
  background: #fef2f2;
  border: 1.5px solid #dc2626;
  border-radius: 12px;
  padding: 10px 14px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #1e293b;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.12);
}
.notification-text strong {
  color: #dc2626;
}
.form-group-custom {
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}
.form-group-custom label {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}
.form-control-custom {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 13px;
  background: #ffffff;
  color: #0f172a;
}
.aux-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.btn-aux {
  flex: 1;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.btn-aux:hover {
  background: #e2e8f0;
}
.voice-active {
  background: #fee2e2 !important;
  border-color: #ef4444 !important;
  color: #dc2626 !important;
  animation: pulse 1s infinite;
}
@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); }
}
.followup-box {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #475569;
  margin-top: 8px;
  padding: 6px 10px;
  background: #f8fafc;
  border-radius: 6px;
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
    <div class="top-actions">
      <div class="region-pill">📍 <?php echo htmlspecialchars($region); ?></div>
      <select id="langSwitcher" class="lang-select" onchange="applyLanguage(this.value)">
        <option value="en">🇬🇧 English</option>
        <option value="hi">🇮🇳 हिन्दी (Hindi)</option>
        <option value="ta">🇮🇳 தமிழ் (Tamil)</option>
        <option value="ml">🇮🇳 മലയാളം (Malayalam)</option>
      </select>
    </div>

    <div class="top-row" style="margin-bottom:12px;">
      <div class="greeting-block">
        <div class="greeting-avatar"><?php echo htmlspecialchars($initials); ?></div>
        <div>
          <div class="greeting-small" data-i18n="greeting_small">Good morning,</div>
          <div class="greeting-name"><?php echo htmlspecialchars($firstName); ?></div>
        </div>
      </div>
      <div>
        <a href="history.php" class="btn-aux" style="padding:6px 10px;font-size:10px;" data-i18n="history_link">📋 History</a>
      </div>
    </div>

    <?php if ($hasActiveAlert): ?>
      <a href="farmer_alert.php" class="notification-banner">
        <div class="notification-text">
          <strong data-i18n="active_alert_title">🚨 LOCAL SURVEILLANCE WARNING</strong><br>
          <span data-i18n="active_alert_sub">Risk of <?php echo htmlspecialchars($activeDisease); ?> in your area. Tap for action steps.</span>
        </div>
        <div style="font-size:16px;color:#dc2626;font-weight:bold;">➔</div>
      </a>
    <?php endif; ?>

    <h1 class="headline" data-i18n="diagnose_headline">Diagnose Crop</h1>
    <p class="subtext" data-i18n="diagnose_subtext">Upload a clear close-up photo of the affected plant leaf or stem to detect diseases in seconds.</p>

    <div class="aux-row">
      <button type="button" class="btn-aux" id="btnVoice" onclick="toggleVoiceInput()">
        <span data-i18n="btn_voice">🎙️ Voice Input</span>
      </button>
      <button type="button" class="btn-aux" id="btnGps" onclick="fetchGpsLocation()">
        <span data-i18n="btn_gps">📍 Auto GPS</span>
      </button>
    </div>

    <div id="voiceTranscriptBox" style="display:none;padding:8px 12px;background:#f1f5f9;border-radius:6px;font-size:11px;margin-bottom:12px;color:#0f172a;"></div>

    <form id="analyzeForm" action="analyze.php" method="POST" enctype="multipart/form-data">
      <div class="form-group-custom">
        <label data-i18n="field_label">Select Field / Plot:</label>
        <select name="field_id" id="fieldSelect" class="form-control-custom">
          <?php if (!empty($fields)): ?>
            <?php foreach ($fields as $fld): ?>
              <option value="<?php echo htmlspecialchars($fld['field_id']); ?>">
                <?php echo htmlspecialchars($fld['field_name'] . ' (' . $fld['crop'] . ')'); ?>
              </option>
            <?php endforeach; ?>
          <?php else: ?>
            <option value="FIELD-001">Main Farm — Field 1 (Tomato)</option>
          <?php endif; ?>
        </select>
      </div>

      <div class="form-group-custom">
        <label data-i18n="crop_label">Crop Type:</label>
        <select name="crop" id="cropSelect" class="form-control-custom">
          <option value="Tomato">Tomato (टमाटर / தக்காளி / തക്കാളി)</option>
          <option value="Apple">Apple (सेब / ஆப்பிள் / ആപ്പിൾ)</option>
          <option value="Corn">Corn / Maize (मक्का / சோளம் / ചോളം)</option>
          <option value="Cherry">Cherry (चेरी / செர்ரி / ചെറി)</option>
          <option value="Blueberry">Blueberry (ब्लूबेरी)</option>
        </select>
      </div>

      <input type="hidden" name="latitude" id="latInput" value="9.2712">
      <input type="hidden" name="longitude" id="lonInput" value="76.4721">

      <div id="dropzone" class="dropzone">
        <div class="cam-circle">📷</div>
        <h3 data-i18n="dropzone_title">Take or Upload Photo</h3>
        <p data-i18n="dropzone_sub">Tap to open camera or drag &amp; drop leaf picture here</p>
        <span class="warn-pill" data-i18n="warn_lighting">⚠️ Make sure lighting is bright</span>
      </div>
      <input type="file" id="fileInput" name="crop_image" accept="image/*" hidden>

      <div class="followup-box">
        <input type="checkbox" name="is_follow_up" id="chkFollowUp" value="1">
        <label for="chkFollowUp" data-i18n="followup_label">This is a follow-up recovery photo for a past case</label>
      </div>

      <div style="height:12px;"></div>

      <button type="submit" id="analyzeBtn" class="btn btn-primary" data-i18n="btn_analyze">⚙️ Analyze Crop Health</button>
    </form>

    <div style="display:flex;justify-content:space-between;margin-top:16px;font-size:12px;">
      <a href="expert_review.php" style="color:var(--text-secondary);text-decoration:none;">🔬 Expert Portal</a>
      <a href="dashboard/agri_disease_surveillance_dashboard.html" style="color:var(--text-secondary);text-decoration:none;">📊 Dashboard</a>
      <a href="logout.php" style="color:#ef4444;text-decoration:none;" data-i18n="logout">Log out</a>
    </div>
  </div>

  <div class="home-indicator"></div>
</div>

<script src="js/translations.js"></script>
<script src="js/main.js"></script>
<script>
// GPS Geolocation Auto-fetch
function fetchGpsLocation() {
  const btn = document.getElementById('btnGps');
  btn.innerHTML = '⌛ Fetching...';
  if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        document.getElementById('latInput').value = pos.coords.latitude.toFixed(4);
        document.getElementById('lonInput').value = pos.coords.longitude.toFixed(4);
        btn.innerHTML = `📍 GPS Set (${pos.coords.latitude.toFixed(2)}, ${pos.coords.longitude.toFixed(2)})`;
        btn.style.background = '#dcfce7';
        btn.style.color = '#15803d';
      },
      err => {
        btn.innerHTML = '📍 GPS: Chengannur (Default)';
      },
      { timeout: 5000 }
    );
  } else {
    btn.innerHTML = '📍 GPS Default';
  }
}

// Voice Assistant Input (Speech Recognition)
let recognition = null;
let isRecording = false;

function toggleVoiceInput() {
  const btn = document.getElementById('btnVoice');
  const transcriptBox = document.getElementById('voiceTranscriptBox');

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Speech recognition is not supported in this browser. You can type or select your crop directly.");
    return;
  }

  if (isRecording) {
    if (recognition) recognition.stop();
    isRecording = false;
    btn.classList.remove('voice-active');
    btn.innerHTML = '🎙️ Voice Input';
    return;
  }

  recognition = new SpeechRecognition();
  const currentLang = localStorage.getItem('cropguard_lang') || 'en';
  const langMap = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN', ml: 'ml-IN' };
  recognition.lang = langMap[currentLang] || 'en-IN';
  recognition.interimResults = false;

  recognition.onstart = () => {
    isRecording = true;
    btn.classList.add('voice-active');
    btn.innerHTML = '🔴 Listening...';
    transcriptBox.style.display = 'block';
    transcriptBox.textContent = 'Listening to your voice... Speak crop name or symptoms.';
  };

  recognition.onresult = (event) => {
    const speechResult = event.results[0][0].transcript.toLowerCase();
    transcriptBox.innerHTML = `<strong>Voice recognized:</strong> "${speechResult}"`;

    if (speechResult.includes('tomato') || speechResult.includes('टमाटर') || speechResult.includes('தக்காளி') || speechResult.includes('തക്കാളി')) {
      document.getElementById('cropSelect').value = 'Tomato';
    } else if (speechResult.includes('apple') || speechResult.includes('सेब') || speechResult.includes('ஆப்பிள்')) {
      document.getElementById('cropSelect').value = 'Apple';
    } else if (speechResult.includes('corn') || speechResult.includes('maize') || speechResult.includes('मक्का') || speechResult.includes('சோளம்')) {
      document.getElementById('cropSelect').value = 'Corn';
    }
  };

  recognition.onerror = (event) => {
    transcriptBox.textContent = 'Voice recognition ended: ' + event.error;
    isRecording = false;
    btn.classList.remove('voice-active');
    btn.innerHTML = '🎙️ Voice Input';
  };

  recognition.onend = () => {
    isRecording = false;
    btn.classList.remove('voice-active');
    btn.innerHTML = '🎙️ Voice Input';
  };

  recognition.start();
}
</script>
</body>
</html>
