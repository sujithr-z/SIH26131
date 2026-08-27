<?php
// =====================================================================
// POST/PUT /api/update_observation.php
// -----------------------------------------------------------------
// Updates fields on an existing observation in data/observations.json.
// =====================================================================

header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, PUT, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require_once __DIR__ . '/../includes/ObservationRepository.php';

$raw = file_get_contents('php://input');
$data = json_decode($raw, true) ?? $_POST;
$observationId = $data['observation_id'] ?? $data['id'] ?? $_GET['id'] ?? '';

if (empty($observationId)) {
    http_response_code(422);
    echo json_encode(['success' => false, 'error' => 'observation_id is required.']);
    exit;
}

try {
    $repo = new ObservationRepository();
    $updated = $repo->update($observationId, $data);

    if ($updated !== null) {
        echo json_encode([
            'success' => true,
            'message' => "Observation {$observationId} updated successfully.",
            'observation' => $updated,
        ]);
    } else {
        http_response_code(404);
        echo json_encode([
            'success' => false,
            'error'   => "Observation {$observationId} not found.",
        ]);
    }
} catch (InvalidArgumentException $e) {
    http_response_code(422);
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
