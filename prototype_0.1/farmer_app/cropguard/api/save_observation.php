<?php
// =====================================================================
// POST /api/save_observation.php
// -----------------------------------------------------------------
// Standalone JSON API. Knows nothing about PHP sessions or the
// existing diagnose/report pages — it only accepts a JSON body and
// returns a JSON response. This is the boundary an external caller
// (curl, a future JS fetch(), a future mobile app) talks to.
//
// Internally it calls ObservationRepository::save() — the exact same
// class analyze.php calls directly for the in-app flow.
//
// Request:
//   { "farmer_id": "001", "disease": "Tomato Early Blight", "confidence": 0.94 }
//
// Success (200):
//   { "success": true, "observation_id": "OBS-000001", "message": "Observation saved successfully" }
//
// Validation error (422):
//   { "success": false, "error": "confidence must be a number between 0.0 and 1.0." }
//
// Malformed request (400):
//   { "success": false, "error": "Invalid or empty JSON body." }
//
// Server/storage failure (500):
//   { "success": false, "error": "Server error while saving observation." }
//   (never leaks file paths or stack traces)
// =====================================================================

header('Content-Type: application/json');
require_once __DIR__ . '/../includes/ObservationRepository.php';

function respond(int $httpCode, array $body): void
{
    http_response_code($httpCode);
    echo json_encode($body);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(400, ['success' => false, 'error' => 'Only POST is supported.']);
}

$raw  = file_get_contents('php://input');
$data = json_decode($raw, true);

if ($raw === '' || $data === null || !is_array($data)) {
    respond(400, ['success' => false, 'error' => 'Invalid or empty JSON body.']);
}

if (!isset($data['farmer_id']) || !isset($data['disease']) || !isset($data['confidence'])) {
    respond(422, ['success' => false, 'error' => 'farmer_id, disease and confidence are all required.']);
}

if (!is_numeric($data['confidence'])) {
    respond(422, ['success' => false, 'error' => 'confidence must be numeric.']);
}

// Pass through any recognised optional fields; the repository itself
// filters this again, so the allow-list only has to live in one place.
$extra = [];
foreach (['crop', 'image_path', 'field_id', 'latitude', 'longitude', 'crop_stage'] as $key) {
    if (isset($data[$key])) {
        $extra[$key] = $data[$key];
    }
}

try {
    $repo   = new ObservationRepository();
    $record = $repo->save(
        (string) $data['farmer_id'],
        (string) $data['disease'],
        (float) $data['confidence'],
        $extra
    );

    respond(200, [
        'success'        => true,
        'observation_id' => $record['observation_id'],
        'message'        => 'Observation saved successfully',
    ]);
} catch (InvalidArgumentException $e) {
    respond(422, ['success' => false, 'error' => $e->getMessage()]);
} catch (Throwable $e) {
    error_log('save_observation.php: ' . $e->getMessage());
    respond(500, ['success' => false, 'error' => 'Server error while saving observation.']);
}
