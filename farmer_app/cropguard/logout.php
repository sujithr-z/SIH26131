<?php
// ============================================================
// logout.php — Clears the session and sends the farmer back
// to the login page.
// ============================================================
session_start();
session_unset();
session_destroy();
header('Location: index.php');
exit;
