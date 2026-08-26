<?php
// ============================================================
// report.php — Diagnosis Report page.
// Reads the diagnosis + image path that analyze.php put into
// the session and displays them.
// ============================================================
session_start();

if (!isset($_SESSION['farmer'])) {
    header('Location: index.php');
    exit;
}
if (!isset($_SESSION['diagnosis'])) {
    header('Location: diagnose.php');
    exit;
}

$d = $_SESSION['diagnosis'];
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CropGuard — Diagnosis Report</title>
<link rel="stylesheet" href="css/style.css">
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
      <h2>Diagnosis Report</h2>
    </div>

    <img class="report-photo" src="<?php echo htmlspecialchars($d['image_path']); ?>" alt="Uploaded leaf photo">

    <span class="severity-pill"><?php echo htmlspecialchars(strtoupper($d['severity'])); ?> SEVERITY</span>
    <div class="disease-label">DETECTED DISEASE</div>
    <div class="disease-name"><?php echo htmlspecialchars($d['disease']); ?></div>

    <div class="meta-row"><span class="k">Target Crop: </span><span class="v"><?php echo htmlspecialchars($d['crop']); ?></span></div>
    <div class="meta-row"><span class="k">Confidence Level: </span><span class="v"><?php echo htmlspecialchars($d['confidence']); ?>% Accuracy</span></div>

    <hr class="divider">

    <div class="section-title">🛡️ Recommended Precautions</div>

    <div class="stub-note">
      Placeholder content — the disease info and precautions above are dummy stub data from analyze.php. Swap in real output from your diagnosis architecture once it's ready.
    </div>

    <p class="description-text"><?php echo htmlspecialchars($d['description']); ?></p>

    <?php foreach ($d['precautions'] as $p): ?>
      <div class="precaution-card">
        <div class="precaution-icon"><?php echo htmlspecialchars($p['icon']); ?></div>
        <div>
          <h4><?php echo htmlspecialchars($p['title']); ?></h4>
          <p><?php echo htmlspecialchars($p['text']); ?></p>
        </div>
      </div>
    <?php endforeach; ?>

    <a href="diagnose.php" class="btn btn-primary">📷 Diagnose Another Crop</a>
  </div>

  <div class="home-indicator"></div>
</div>

</body>
</html>
