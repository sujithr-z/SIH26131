<?php
// ============================================================
// index.php — Login / Sign up page
// If a farmer is already logged in, skip straight to Diagnose.
// ============================================================
session_start();

if (isset($_SESSION['farmer'])) {
    header('Location: diagnose.php');
    exit;
}

$error = '';
if (isset($_GET['error']) && $_GET['error'] === '1') {
    $error = 'Please enter both your full name and phone number.';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CropGuard — Login</title>
<link rel="stylesheet" href="css/style.css">
</head>
<body>

<div class="phone">
  <div class="status-bar">
    <span>9:41</span>
    <span class="icons">📶 📡 🔋</span>
  </div>

  <div class="screen">
    <div class="login-logo">🌱</div>
    <p class="brand">CropGuard</p>
    <p class="brand-sub">AI DISEASE ANALYST</p>

    <h1 class="headline">Welcome, Farmer</h1>
    <p class="subtext">Sign in to instantly diagnose crop health and access localized prevention guides.</p>

    <?php if ($error): ?>
      <div class="error-banner"><?php echo htmlspecialchars($error); ?></div>
    <?php endif; ?>

    <form action="login.php" method="POST" novalidate>
      <div class="field">
        <label for="full_name">Full Name</label>
        <div class="input-wrap">
          <span>👤</span>
          <input type="text" id="full_name" name="full_name" placeholder="e.g. John Doe" required>
        </div>
      </div>

      <div class="field">
        <label for="phone">Phone Number</label>
        <div class="input-wrap">
          <span>📞</span>
          <input type="tel" id="phone" name="phone" placeholder="e.g. +1 555 123 4567" required>
        </div>
      </div>

      <button type="submit" class="btn btn-primary">Login to CropGuard</button>
    </form>

    <p class="helper-link">Need help joining? <a href="#">Contact Support</a></p>
  </div>

  <div class="home-indicator"></div>
</div>

</body>
</html>
