<?php
// =====================================================================
// POST /api/trigger_alert.php
// -----------------------------------------------------------------
// Receives official decisions from the dashboard, logs them to
// data/decisions.json, and triggers the calling simulator if alert is confirmed.
// =====================================================================

header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit;
}

$rawInput = file_get_contents('php://input');
$input = json_decode($rawInput, true);

if (!$input) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Invalid JSON input']);
    exit;
}

$action = $input['action'] ?? 'DISMISS';
$eventId = $input['event_id'] ?? 'UNKNOWN';
$disease = $input['disease'] ?? 'UNKNOWN';
$riskLabel = $input['risk_label'] ?? 'UNKNOWN';
$officer = $input['officer'] ?? 'Agri. Officer';
$timestamp = $input['timestamp'] ?? date('c');

$dataDir = __DIR__ . '/../data';
if (!file_exists($dataDir)) {
    mkdir($dataDir, 0777, true);
}

// 1. Save Decision
$decisionsFile = $dataDir . '/decisions.json';
$decisions = [];
if (file_exists($decisionsFile)) {
    $decisions = json_decode(file_get_contents($decisionsFile), true) ?: [];
}

$decisionRecord = [
    'decision_id' => 'DEC-' . time() . '-' . rand(1000, 9999),
    'event_id' => $eventId,
    'action' => $action,
    'disease' => $disease,
    'risk_label' => $riskLabel,
    'officer' => $officer,
    'timestamp' => $timestamp
];
$decisions[] = $decisionRecord;
file_put_contents($decisionsFile, json_encode($decisions, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));

// 2. Trigger Calling Simulator if ALERT
$callsInitiated = 0;
if ($action === 'ALERT') {
    $farmersFile = $dataDir . '/farmers.json';
    $farmers = [];
    if (file_exists($farmersFile)) {
        $farmers = json_decode(file_get_contents($farmersFile), true) ?: [];
    }

    $callLogFile = $dataDir . '/call_log.json';
    $callLog = [];
    if (file_exists($callLogFile)) {
        $callLog = json_decode(file_get_contents($callLogFile), true) ?: [];
    }

    // Generate call simulation logs for all farmers
    foreach ($farmers as $farmer) {
        $callLog[] = [
            'call_id' => 'CALL-' . time() . '-' . $farmer['farmer_id'],
            'event_id' => $eventId,
            'farmer_id' => $farmer['farmer_id'],
            'farmer_name' => $farmer['full_name'],
            'phone' => $farmer['phone'],
            'disease' => $disease,
            'risk_label' => $riskLabel,
            'status' => 'PENDING', // PENDING -> CALLING -> COMPLETED
            'timestamp' => date('Y-m-d H:i:s'),
            'duration_sec' => 0
        ];
        $callsInitiated++;
    }

    file_put_contents($callLogFile, json_encode($callLog, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));

    // Optional: Start background simulator process (Phase 5)
    // For now we do it directly in PHP or we trigger it asynchronously. Let's call a simulator script.
    $simScript = __DIR__ . '/call_simulator.php';
    if (file_exists($simScript)) {
        // Run simulator asynchronously without waiting
        if (substr(php_uname(), 0, 7) == "Windows") {
            pclose(popen("start /B php " . escapeshellarg($simScript) . " > NUL 2>&1", "r"));
        } else {
            exec("php " . escapeshellarg($simScript) . " > /dev/null 2>&1 &");
        }
    }
}

echo json_encode([
    'success' => true,
    'decision' => $decisionRecord,
    'calls_initiated' => $callsInitiated
], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
