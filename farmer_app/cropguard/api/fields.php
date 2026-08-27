<?php
// =====================================================================
// API: /api/fields.php
// GET: Query fields (optionally by farmer_id)
// POST: Register a new field
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
$db = new DatabaseManager();

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $farmerId = $_GET['farmer_id'] ?? null;
    if ($farmerId !== null) {
        $fields = $db->findWhere('fields', 'farmer_id', $farmerId);
    } else {
        $fields = $db->readCollection('fields');
    }
    echo json_encode(['success' => true, 'fields' => $fields], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $raw = file_get_contents('php://input');
    $input = json_decode($raw, true) ?: $_POST;

    if (!isset($input['farmer_id']) || !isset($input['field_name']) || !isset($input['crop'])) {
        http_response_code(422);
        echo json_encode(['success' => false, 'error' => 'farmer_id, field_name, and crop are required.']);
        exit;
    }

    $allFields = $db->readCollection('fields');
    $nextId = 'FIELD-' . str_pad((string)(count($allFields) + 1), 3, '0', STR_PAD_LEFT);

    $newField = [
        'field_id'    => $nextId,
        'farmer_id'   => trim($input['farmer_id']),
        'field_name'  => trim($input['field_name']),
        'crop'        => trim($input['crop']),
        'area_acres'  => isset($input['area_acres']) ? (float)$input['area_acres'] : 1.0,
        'latitude'    => isset($input['latitude']) ? (float)$input['latitude'] : 9.2712,
        'longitude'   => isset($input['longitude']) ? (float)$input['longitude'] : 76.4721,
        'sowing_date' => $input['sowing_date'] ?? date('Y-m-d'),
    ];

    $db->insert('fields', $newField);

    echo json_encode(['success' => true, 'field' => $newField], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}
