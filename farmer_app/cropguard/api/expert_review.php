<?php
// =====================================================================
// API: /api/expert_review.php
// GET: Query observations requiring expert validation
// POST: Submit expert validation decision (CONFIRM / REJECT / REQUEST_REVIEW)
// =====================================================================

header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require_once __DIR__ . '/../includes/DatabaseManager.php';
require_once __DIR__ . '/../includes/ObservationRepository.php';

$db = new DatabaseManager();
$repo = new ObservationRepository();

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $observations = $repo->all();
    $farmers = $db->readCollection('farmers');
    $farmersMap = [];
    foreach ($farmers as $f) {
        if (isset($f['farmer_id'])) $farmersMap[$f['farmer_id']] = $f;
    }

    $pending = [];
    $reviewed = [];

    foreach ($observations as $obs) {
        $fid = $obs['farmer_id'] ?? '?';
        $obs['farmer_name'] = $farmersMap[$fid]['full_name'] ?? ('Farmer ' . $fid);
        $obs['farmer_phone'] = $farmersMap[$fid]['phone'] ?? '';
        
        $vStatus = $obs['validation_status'] ?? 'PENDING';
        if ($vStatus === 'PENDING') {
            $pending[] = $obs;
        } else {
            $reviewed[] = $obs;
        }
    }

    $validations = $db->readCollection('expert_validations');

    echo json_encode([
        'success'             => true,
        'pending_count'       => count($pending),
        'reviewed_count'      => count($reviewed),
        'pending_reviews'     => array_values($pending),
        'recent_validations'  => array_values(array_slice($validations, -20)),
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $raw = file_get_contents('php://input');
    $input = json_decode($raw, true) ?: $_POST;

    $obsId = trim($input['observation_id'] ?? '');
    $action = strtoupper(trim($input['action'] ?? 'CONFIRM')); // CONFIRM | REJECT | REQUEST_REVIEW | MARK_UNCERTAIN
    $expertName = trim($input['expert_name'] ?? 'Dr. Ananya Sharma (Pathologist)');
    $notes = trim($input['expert_notes'] ?? 'Diagnosis verified by agricultural expert.');

    if ($obsId === '') {
        http_response_code(422);
        echo json_encode(['success' => false, 'error' => 'observation_id is required.']);
        exit;
    }

    // 1. Update observation validation_status
    $statusMap = [
        'CONFIRM'        => 'CONFIRMED',
        'REJECT'         => 'REJECTED',
        'REQUEST_REVIEW' => 'PENDING',
        'MARK_UNCERTAIN' => 'UNCERTAIN',
    ];
    $newStatus = $statusMap[$action] ?? 'CONFIRMED';

    $updatedObs = $repo->update($obsId, [
        'validation_status' => $newStatus,
        'expert_id'         => $expertName,
        'expert_notes'      => $notes,
    ]);

    if (!$updatedObs) {
        http_response_code(404);
        echo json_encode(['success' => false, 'error' => "Observation {$obsId} not found."]);
        exit;
    }

    // 2. Persist validation event
    $valRecord = [
        'validation_id'     => 'VAL-' . time() . '-' . rand(100, 999),
        'observation_id'    => $obsId,
        'action'            => $action,
        'validation_status' => $newStatus,
        'crop'              => $updatedObs['crop'] ?? 'Crop',
        'disease'           => $updatedObs['disease'] ?? 'Unknown',
        'expert_name'       => $expertName,
        'expert_notes'      => $notes,
        'timestamp'         => date('c'),
    ];
    $db->insert('expert_validations', $valRecord);

    // 3. If CONFIRMED, update any triggered surveillance events and trigger notifications
    $dispatchedAlerts = 0;
    if ($newStatus === 'CONFIRMED') {
        $events = $db->readCollection('priority_events');
        $eventUpdated = false;
        if (is_array($events)) {
            foreach ($events as &$ev) {
                if (is_array($ev) && isset($ev['status']) && ($ev['status'] === 'TRIGGERED' || $ev['status'] === 'WATCH')) {
                    $ev['status'] = 'CONFIRMED';
                    $ev['confirmed_by'] = $expertName;
                    $ev['confirmed_at'] = date('c');
                    $eventUpdated = true;
                }
            }
            if ($eventUpdated) {
                $db->writeCollection('priority_events', $events, true);
            }
        }

        // Send alert notification to the farmer
        $fid = $updatedObs['farmer_id'];
        $farmer = $db->findOne('farmers', 'farmer_id', $fid);
        $phone = $farmer['phone'] ?? '';
        $fName = $farmer['full_name'] ?? "Farmer {$fid}";

        $notif = [
            'notification_id' => 'NOTIF-' . time() . '-' . rand(100, 999),
            'farmer_id'       => $fid,
            'farmer_name'     => $fName,
            'phone'           => $phone,
            'disease'         => $updatedObs['disease'],
            'channel'         => 'SMS & In-App',
            'message'         => "CropGuard Advisory: {$updatedObs['disease']} has been CONFIRMED by {$expertName}. Recommended immediate action: Apply protective bio-fungicide and isolate affected rows.",
            'status'          => 'SENT',
            'timestamp'       => date('c'),
        ];
        $db->insert('notifications', $notif);

        // Also add to call_log for IVR call simulator
        $callLog = $db->readCollection('call_log');
        $callLog[] = [
            'call_id'      => 'CALL-' . time() . '-' . $fid,
            'event_id'     => 'EVENT-EXPERT',
            'farmer_id'    => $fid,
            'farmer_name'  => $fName,
            'phone'        => $phone,
            'disease'      => $updatedObs['disease'],
            'risk_label'   => 'CONFIRMED CASE',
            'status'       => 'PENDING',
            'timestamp'    => date('Y-m-d H:i:s'),
            'duration_sec' => 0,
        ];
        $db->writeCollection('call_log', $callLog);
        $dispatchedAlerts = 1;
    }

    echo json_encode([
        'success'            => true,
        'validation'         => $valRecord,
        'updated_observation'=> $updatedObs,
        'alerts_dispatched'  => $dispatchedAlerts,
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}
