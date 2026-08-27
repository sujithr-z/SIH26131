<?php
// =====================================================================
// GET /api/get_report.php
// -----------------------------------------------------------------
// Serves reports/latest_report.json as a JSON API response.
// Called by the dashboard on page load to populate all panels
// with live data from the most recent pipeline run.
//
// Also serves the pipeline status so the dashboard knows which
// stages are complete.
//
// CORS headers are set so the dashboard HTML can fetch this
// even when opened as a local file (file:// scheme) during dev.
// =====================================================================

header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-cache, must-revalidate');
header('Access-Control-Allow-Origin: *');

$reportFile = __DIR__ . '/../reports/latest_report.json';

if (!file_exists($reportFile)) {
    http_response_code(404);
    echo json_encode([
        'success' => false,
        'error'   => 'Report not yet generated. Run the surveillance pipeline first.',
        'hint'    => 'python3 surveillance/monitor.py',
    ]);
    exit;
}

$raw = file_get_contents($reportFile);
$data = json_decode($raw, true);

if ($data === null) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error'   => 'Report file exists but contains invalid JSON.',
    ]);
    exit;
}

// Inject the map URL as a web-accessible path
$data['success'] = true;
$mapPath = __DIR__ . '/../gis/output/analyzed_map.png';
$data['map']['web_url'] = file_exists($mapPath)
    ? '../gis/output/analyzed_map.png'
    : null;

echo json_encode($data, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
