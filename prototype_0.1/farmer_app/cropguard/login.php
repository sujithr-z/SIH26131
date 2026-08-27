<?php
// ============================================================
// login.php — Handles the login form submission.
//
// This is the "database" for the prototype: farmers.json.
// Each record looks like:
//   { "farmer_id": "001", "full_name": "John Doe", "phone": "+1 555 123 4567", "created_at": "..." }
//
// Farmer IDs are just the record's position, zero-padded to 3
// digits: 001, 002, 003, ...
//
// Logic: if the phone number already exists in the file, we log
// that farmer back in (and refresh their name). Otherwise we
// create a brand new record with the next farmer_id.
// ============================================================
session_start();

$fullName = isset($_POST['full_name']) ? trim($_POST['full_name']) : '';
$phone    = isset($_POST['phone']) ? trim($_POST['phone']) : '';

if ($fullName === '' || $phone === '') {
    header('Location: index.php?error=1');
    exit;
}

$dbFile = __DIR__ . '/data/farmers.json';

// Make sure the data folder + file exist (fresh checkout safety net)
if (!file_exists(dirname($dbFile))) {
    mkdir(dirname($dbFile), 0777, true);
}
if (!file_exists($dbFile)) {
    file_put_contents($dbFile, '[]');
}

$raw     = file_get_contents($dbFile);
$farmers = json_decode($raw, true);
if (!is_array($farmers)) {
    $farmers = [];
}

// Look for an existing farmer with this phone number
$existingIndex = null;
foreach ($farmers as $i => $f) {
    if (isset($f['phone']) && $f['phone'] === $phone) {
        $existingIndex = $i;
        break;
    }
}

if ($existingIndex !== null) {
    // Returning farmer — just refresh their name and log them in
    $farmers[$existingIndex]['full_name'] = $fullName;
    $currentFarmer = $farmers[$existingIndex];
} else {
    // New farmer — assign the next ID: 001, 002, 003, ...
    $nextId = str_pad((string) (count($farmers) + 1), 3, '0', STR_PAD_LEFT);

    $currentFarmer = [
        'farmer_id'  => $nextId,
        'full_name'  => $fullName,
        'phone'      => $phone,
        'created_at' => date('Y-m-d H:i:s'),
    ];

    $farmers[] = $currentFarmer;
}

// Save the updated "database" back to disk
file_put_contents($dbFile, json_encode($farmers, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));

// Log the farmer into the session so other pages know who they are
$_SESSION['farmer'] = $currentFarmer;

header('Location: diagnose.php');
exit;
