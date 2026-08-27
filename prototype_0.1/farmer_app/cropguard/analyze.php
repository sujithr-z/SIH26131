<?php
// ============================================================
// analyze.php — Handles the "Analyze Crop Health" submission.
//
// What it does for real:
//   1. Saves the uploaded photo into /uploads
//   2. Stores its path + a diagnosis result in the session
//   3. Redirects to report.php to display it
//
// What is FAKE (for now):
//   The diagnosis result itself. There is no real image-analysis
//   model wired up yet. Everything between the STUB markers below
//   is hardcoded placeholder data. See the comment block for
//   exactly what to replace once your detection architecture is
//   ready.
// ============================================================
session_start();

if (!isset($_SESSION['farmer'])) {
    header('Location: index.php');
    exit;
}

if (!isset($_FILES['crop_image']) || $_FILES['crop_image']['error'] !== UPLOAD_ERR_OK) {
    header('Location: diagnose.php?error=upload');
    exit;
}

$file = $_FILES['crop_image'];

// Basic image-type check without requiring the optional Fileinfo extension.
$allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
$imageInfo = @getimagesize($file['tmp_name']);
$mime = $imageInfo['mime'] ?? '';

if ($imageInfo === false || !in_array($mime, $allowed, true)) {
    header('Location: diagnose.php?error=filetype');
    exit;
}

// Make sure the uploads folder exists
$uploadDir = __DIR__ . '/uploads';
if (!file_exists($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}

$ext          = pathinfo($file['name'], PATHINFO_EXTENSION);
$safeExt      = preg_replace('/[^a-zA-Z0-9]/', '', $ext);
$farmerId     = $_SESSION['farmer']['farmer_id'];
$fileName     = 'farmer' . $farmerId . '_' . time() . '.' . $safeExt;
$destination  = $uploadDir . '/' . $fileName;

if (!move_uploaded_file($file['tmp_name'], $destination)) {
    header('Location: diagnose.php?error=save');
    exit;
}

// =====================================================================
// STUB — DISEASE DIAGNOSIS DATA
// -----------------------------------------------------------------
// TODO: Replace everything inside $diagnosis with a real call to your
// disease-detection architecture once it exists, e.g.:
//
//   $diagnosis = callDiseaseModel($destination);
//
// Whatever you build should return an array shaped exactly like this
// one (same keys) so report.php keeps working without any changes.
// The values below are only placeholders for wiring the UI together.
// =====================================================================
$diagnosis = [
    'crop'        => 'Tomato',        // TODO: predicted crop type
    'disease'     => 'Early Blight',  // TODO: predicted disease name
    'severity'    => 'High',          // TODO: 'Low' | 'Medium' | 'High'
    'confidence'  => 94.2,            // TODO: model confidence, 0-100

    // TODO: model/knowledge-base generated explanation of the disease
    'description' => 'Early Blight is caused by the fungus Alternaria solani. '
                    . 'It initiates brown spots on older leaves. Follow these immediate '
                    . 'biological and chemical treatment steps to protect your total harvest yield.',

    // TODO: precaution list generated per-disease. icon is just an emoji stand-in.
    'precautions' => [
        [
            'icon'  => '✂️',
            'title' => 'Prune Infected Foliage',
            'text'  => 'Cut away lower affected leaves carefully. Clean shears with alcohol between cuts to prevent spreading spores.',
        ],
        [
            'icon'  => '💧',
            'title' => 'Apply Organic Fungicide',
            'text'  => 'Spray copper-based organic fungicides or Bacillus subtilis thoroughly on both sides of remaining healthy leaves.',
        ],
        [
            'icon'  => '🌱',
            'title' => 'Improve Soil & Watering',
            'text'  => 'Switch to drip irrigation. Avoid overhead watering completely to keep foliage dry. Mulch around stem base.',
        ],
    ],
];
// =====================================================================
// END STUB
// =====================================================================

$diagnosis['image_path'] = 'uploads/' . $fileName;

// =====================================================================
// BACKEND DATA PIPELINE — persist this detection as an observation
// -----------------------------------------------------------------
// This is the single insertion point: farmer_id, disease, confidence,
// crop and image_path are all finalized right here. We call the same
// ObservationRepository that api/save_observation.php uses, so both
// paths write through one storage implementation.
//
// Confidence conversion: the diagnosis stub above uses a 0-100 scale
// (for the "94.2% Accuracy" label on the report page). The repository
// stores confidence as 0.0-1.0, so we divide by 100 here.
//
// Wrapped in try/catch on purpose: a storage hiccup here must never
// break the existing UI flow the farmer is in the middle of — it's
// logged and the report page still renders normally either way.
// =====================================================================
require_once __DIR__ . '/includes/ObservationRepository.php';
try {
    $repo = new ObservationRepository();
    $repo->save(
        $farmerId,
        $diagnosis['disease'],
        $diagnosis['confidence'] / 100,
        [
            'crop'       => $diagnosis['crop'],
            'image_path' => $diagnosis['image_path'],
        ]
    );
} catch (Throwable $e) {
    error_log('Failed to save observation: ' . $e->getMessage());
}
// =====================================================================
// END BACKEND DATA PIPELINE
// =====================================================================

$_SESSION['diagnosis'] = $diagnosis;

header('Location: report.php');
exit;
