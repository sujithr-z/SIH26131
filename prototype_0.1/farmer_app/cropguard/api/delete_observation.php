<?php
// =====================================================================
// POST/DELETE /api/delete_observation.php
// -----------------------------------------------------------------
// Deletes an observation by observation_id from data/observations.json.
// =====================================================================

header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require_once __DIR__ . '/../includes/ObservationRepository.php';

$raw = file_get_contents('php://input');
$data = json_decode($raw, true) ?? [];
$observationId = $_GET['id'] ?? $_POST['id'] ?? $data['observation_id'] ?? $data['id'] ?? '';

if (empty($observationId)) {
    http_response_code(422);
    echo json_encode(['success' => false, 'error' => 'observation_id is required.']);
    exit;
}

try {
    $repo = new ObservationRepository();
    $deleted = $repo->delete($observationId);

    if ($deleted) {
        echo json_encode([
            'success' => true,
            'message' => "Observation {$observationId} deleted successfully.",
            'remaining_count' => count($repo->all()),
        ]);
    } else {
        http_response_code(404);
        echo json_encode([
            'success' => false,
            'error'   => "Observation {$observationId} not found.",
        ]);
    }
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
