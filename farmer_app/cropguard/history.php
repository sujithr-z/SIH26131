<?php
// ============================================================
// history.php — Farmer Personal Observation & Treatment History
// ============================================================
session_start();

if (!isset($_SESSION['farmer'])) {
    header('Location: index.php');
    exit;
}

require_once __DIR__ . '/includes/ObservationRepository.php';
$repo = new ObservationRepository();

$farmer   = $_SESSION['farmer'];
$farmerId = $farmer['farmer_id'];
$observations = $repo->findByFarmer($farmerId);
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CropGuard — My Observations History</title>
<link rel="stylesheet" href="css/style.css">
<style>
.history-item {
  background: var(--surface-1, #f8fafc);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
  display: flex;
  gap: 12px;
  align-items: center;
}
.history-thumb {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid #cbd5e1;
}
.history-info {
  flex: 1;
  text-align: left;
}
.history-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}
.history-meta {
  font-size: 11px;
  color: #64748b;
  margin: 2px 0;
}
.val-badge {
  display: inline-block;
  font-size: 9px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}
.val-confirmed { background: #dcfce7; color: #15803d; }
.val-pending { background: #fef3c7; color: #b45309; }
.val-rejected { background: #fee2e2; color: #b91c1c; }
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
      <h2>Observation History</h2>
    </div>

    <p class="subtext" style="text-align:left; margin-bottom:16px;">
      Logged observations for <strong><?php echo htmlspecialchars($farmer['full_name']); ?></strong> (ID: <?php echo htmlspecialchars($farmerId); ?>).
    </p>

    <?php if (empty($observations)): ?>
      <div style="text-align:center; padding:40px 10px; color:#94a3b8;">
        <span style="font-size:36px; display:block; margin-bottom:8px;">📷</span>
        No crop observations recorded yet. Take your first photo to diagnose your crops!
      </div>
    <?php else: ?>
      <?php foreach (array_reverse($observations) as $obs): ?>
        <?php
          $vStatus = $obs['validation_status'] ?? 'PENDING';
          $badgeClass = $vStatus === 'CONFIRMED' ? 'val-confirmed' : ($vStatus === 'REJECTED' ? 'val-rejected' : 'val-pending');
          $confPct = round((float)($obs['confidence'] ?? 0.0) * 100);
          $img = $obs['image_path'] ?? 'uploads/sample_leaf.jpg';
        ?>
        <div class="history-item">
          <img src="<?php echo htmlspecialchars($img); ?>" class="history-thumb" alt="specimen">
          <div class="history-info">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="history-title"><?php echo htmlspecialchars($obs['disease']); ?></span>
              <span class="val-badge <?php echo $badgeClass; ?>"><?php echo htmlspecialchars($vStatus); ?></span>
            </div>
            <div class="history-meta">
              <strong><?php echo htmlspecialchars($obs['crop'] ?? 'Crop'); ?></strong> · <?php echo $confPct; ?>% AI confidence
            </div>
            <div class="history-meta" style="font-size:10px;">
              📅 <?php echo htmlspecialchars(date('M d, Y H:i', strtotime($obs['timestamp'] ?? 'now'))); ?>
            </div>
            <?php if (!empty($obs['expert_notes'])): ?>
              <div style="font-size:10px; color:#0f766e; background:#f0fdfa; padding:4px 6px; border-radius:4px; margin-top:4px;">
                💬 <strong>Expert:</strong> <?php echo htmlspecialchars($obs['expert_notes']); ?>
              </div>
            <?php endif; ?>
          </div>
        </div>
      <?php endforeach; ?>
    <?php endif; ?>

    <div style="margin-top: 24px;">
      <a href="diagnose.php" class="btn btn-primary">📷 New Diagnosis</a>
    </div>
  </div>

  <div class="home-indicator"></div>
</div>

</body>
</html>
