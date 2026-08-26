<?php
// ============================================================
// diagnose.php — Upload / drop a leaf photo, then Analyze.
// Requires a logged-in farmer (set by login.php).
// ============================================================
session_start();

if (!isset($_SESSION['farmer'])) {
    header('Location: index.php');
    exit;
}

$farmer     = $_SESSION['farmer'];
$farmerId   = $farmer['farmer_id'];
$firstName  = explode(' ', trim($farmer['full_name']))[0];
$initials   = strtoupper(substr($farmer['full_name'], 0, 1));

// Check for active surveillance alert in local call log database
$callLogFile = __DIR__ . '/data/call_log.json';
$hasActiveAlert = false;
$activeDisease = '';
if (file_exists($callLogFile)) {
    $callLog = json_decode(file_get_contents($callLogFile), true) ?: [];
    // Find if the farmer has an active alert
    for ($i = count($callLog) - 1; $i >= 0; $i--) {
        if ($callLog[$i]['farmer_id'] === $farmerId) {
            $hasActiveAlert = true;
            $activeDisease = $callLog[$i]['disease'];
            break;
        }
    }
}

// NOTE: "Region North" is a placeholder — wire this up to real
// location/region data whenever that's available.
$region = 'Region North';
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CropGuard — Diagnose Crop</title>
<link rel="stylesheet" href="css/style.css">
<style>
.notification-banner {
  background: var(--red-bg);
  border: 1.5px solid var(--red-text);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-dark);
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(192, 57, 43, 0.15);
}
.notification-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.notification-text strong {
  color: var(--red-text);
}
.notification-arrow {
  font-size: 18px;
  color: var(--red-text);
  font-weight: bold;
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
    <div class="top-row">
      <div class="greeting-block">
        <div class="greeting-avatar"><?php echo htmlspecialchars($initials); ?></div>
        <div>
          <div class="greeting-small">Good morning,</div>
          <div class="greeting-name"><?php echo htmlspecialchars($firstName); ?></div>
        </div>
      </div>
      <div>
        <div class="region-pill">📍 <?php echo htmlspecialchars($region); ?></div>
      </div>
    </div>

    <?php if ($hasActiveAlert): ?>
      <a href="farmer_alert.php" class="notification-banner">
        <div class="notification-text">
          <strong>🚨 LOCAL SURVEILLANCE WARNING</strong>
          <span>Risk of <?php echo htmlspecialchars($activeDisease); ?> in your area. Tap for action steps.</span>
        </div>
        <div class="notification-arrow">➔</div>
      </a>
    <?php endif; ?>

    <h1 class="headline">Diagnose Crop</h1>
    <p class="subtext">Upload a clear close-up photo of the affected plant leaf or stem to detect diseases in seconds.</p>

    <form id="analyzeForm" action="analyze.php" method="POST" enctype="multipart/form-data">
      <div id="dropzone" class="dropzone">
        <div class="cam-circle">📷</div>
        <h3>Take or Upload Photo</h3>
        <p>Tap to open camera or drag &amp; drop leaf picture here</p>
        <span class="warn-pill">⚠️ Make sure lighting is bright</span>
      </div>
      <input type="file" id="fileInput" name="crop_image" accept="image/*" hidden>

      <button type="submit" id="analyzeBtn" class="btn btn-primary">⚙️ Analyze Crop Health</button>
    </form>

    <p class="helper-link"><a href="logout.php">Log out</a></p>
  </div>

  <div class="home-indicator"></div>
</div>

<script src="js/main.js"></script>
</body>
</html>
