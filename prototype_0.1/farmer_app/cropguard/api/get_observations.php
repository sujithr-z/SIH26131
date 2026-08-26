<?php
// =====================================================================
// GET /api/get_observations.php
// -----------------------------------------------------------------
// Authoritative JSON API endpoint returning all live observations
// directly from data/observations.json via ObservationRepository.
//
// Enriched with farmer information from data/farmers.json and
// dynamic statistical aggregates.
// =====================================================================

header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-cache, must-revalidate');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

require_once __DIR__ . '/../includes/ObservationRepository.php';

try {
    $repo = new ObservationRepository();
    $rawObservations = $repo->all();
    $stats = $repo->stats();

    // Load farmers for enrichment
    $farmersFile = __DIR__ . '/../data/farmers.json';
    $farmersMap = [];
    if (file_exists($farmersFile)) {
        $farmersRaw = file_get_contents($farmersFile);
        $farmersList = json_decode($farmersRaw, true);
        if (is_array($farmersList)) {
            foreach ($farmersList as $f) {
                if (isset($f['farmer_id'])) {
                    $farmersMap[$f['farmer_id']] = $f;
                }
            }
        }
    }

    // Default Kerala locations pool to provide consistent map pins for prototype observations
    $defaultLocations = [
        ['name' => 'Chengannur',   'lat' => 9.2712, 'lon' => 76.4721],
        ['name' => 'Thiruvalla',   'lat' => 9.2645, 'lon' => 76.4600],
        ['name' => 'Aranmula',     'lat' => 9.2801, 'lon' => 76.4815],
        ['name' => 'Pandalam',     'lat' => 9.2723, 'lon' => 76.4710],
        ['name' => 'Kozhencherry', 'lat' => 9.2660, 'lon' => 76.4640],
        ['name' => 'Mavelikkara',  'lat' => 9.3150, 'lon' => 76.5160],
        ['name' => 'Pathanamthitta','lat' => 9.3280, 'lon' => 76.5280],
    ];

    $enriched = [];
    foreach ($rawObservations as $idx => $obs) {
        $fid = $obs['farmer_id'] ?? '?';
        $farmer = $farmersMap[$fid] ?? null;

        // Assign latitude/longitude if not explicitly given
        $locIndex = $idx % count($defaultLocations);
        $lat = isset($obs['latitude']) ? (float)$obs['latitude'] : $defaultLocations[$locIndex]['lat'];
        $lon = isset($obs['longitude']) ? (float)$obs['longitude'] : $defaultLocations[$locIndex]['lon'];
        $place = $obs['place'] ?? $defaultLocations[$locIndex]['name'];

        $enriched[] = [
            'observation_id' => $obs['observation_id'] ?? ('OBS-' . ($idx + 1)),
            'farmer_id'      => $fid,
            'farmer_name'    => $farmer ? ($farmer['full_name'] ?? ('Farmer ' . $fid)) : ('Farmer ' . $fid),
            'farmer_phone'   => $farmer ? ($farmer['phone'] ?? '') : '',
            'crop'           => $obs['crop'] ?? 'Tomato',
            'disease'        => $obs['disease'] ?? 'Unknown',
            'confidence'     => (float)($obs['confidence'] ?? 0.0),
            'timestamp'      => $obs['timestamp'] ?? date('c'),
            'image_path'     => $obs['image_path'] ?? null,
            'latitude'       => $lat,
            'longitude'      => $lon,
            'place'          => $place,
        ];
    }

    // Check if latest report exists
    $reportFile = __DIR__ . '/../reports/latest_report.json';
    $latestReport = null;
    if (file_exists($reportFile)) {
        $repRaw = file_get_contents($reportFile);
        $latestReport = json_decode($repRaw, true);
    }

    echo json_encode([
        'success'            => true,
        'total_observations' => $stats['total_observations'],
        'unique_farmers'     => $stats['unique_farmers'],
        'average_confidence' => $stats['average_confidence'],
        'disease_counts'     => $stats['disease_counts'],
        'latest_observation' => $stats['latest_observation'],
        'observations'       => $enriched,
        'latest_report'      => $latestReport,
    ], JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);

} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error'   => 'Failed to load observations: ' . $e->getMessage(),
    ]);
}
