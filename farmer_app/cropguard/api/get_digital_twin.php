<?php
// =====================================================================
// API: /api/get_digital_twin.php
// GET: Returns the authoritative structured Agricultural Digital Twin State
// =====================================================================

header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require_once __DIR__ . '/../includes/DatabaseManager.php';
require_once __DIR__ . '/../includes/ObservationRepository.php';

$db = new DatabaseManager();
$repo = new ObservationRepository();

$farmers = $db->readCollection('farmers');
$fields = $db->readCollection('fields');
$observations = $repo->all();
$weather = $db->readCollection('weather_observations');
$events = $db->readCollection('priority_events');
$validations = $db->readCollection('expert_validations');
$notifications = $db->readCollection('notifications');
$callLogs = $db->readCollection('call_log');

// Build digital farm hierarchy
$farmsState = [];
foreach ($farmers as $f) {
    $fid = $f['farmer_id'];
    $farmerFields = array_values(array_filter($fields, fn($fld) => ($fld['farmer_id'] ?? '') === $fid));
    $farmerObs = array_values(array_filter($observations, fn($obs) => ($obs['farmer_id'] ?? '') === $fid));

    $farmsState[] = [
        'farmer_id'          => $fid,
        'full_name'          => $f['full_name'],
        'phone'              => $f['phone'],
        'fields_count'       => count($farmerFields),
        'fields'             => $farmerFields,
        'total_observations' => count($farmerObs),
        'active_diseases'    => array_unique(array_column($farmerObs, 'disease')),
        'latest_observation' => end($farmerObs) ?: null,
    ];
}

// Compute ecosystem health summary
$totalObs = count($observations);
$confirmedOutbreaks = count(array_filter($observations, fn($o) => ($o['validation_status'] ?? '') === 'CONFIRMED'));
$pendingReviews = count(array_filter($observations, fn($o) => ($o['validation_status'] ?? 'PENDING') === 'PENDING'));

$digitalTwinState = [
    'system_name' => 'CropGuard Agricultural Intelligence Digital Twin',
    'timestamp'   => date('c'),
    'state_version' => 'v1.0.0',

    'ecosystem_overview' => [
        'total_farmers'         => count($farmers),
        'total_fields'          => count($fields),
        'total_observations'    => $totalObs,
        'confirmed_outbreaks'   => $confirmedOutbreaks,
        'pending_expert_reviews'=> $pendingReviews,
        'active_surveillance_events' => count($events),
    ],

    'digital_farms' => $farmsState,

    'environmental_state' => [
        'active_stations' => count($weather),
        'current_weather' => $weather[0] ?? null,
    ],

    'surveillance_state' => [
        'events' => $events,
        'recent_expert_validations' => array_slice($validations, -10),
    ],

    'dissemination_state' => [
        'total_notifications_sent' => count($notifications),
        'recent_notifications'     => array_slice($notifications, -10),
        'ivr_call_queue_length'    => count($callLogs),
    ],
];

echo json_encode(['success' => true, 'digital_twin' => $digitalTwinState], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
