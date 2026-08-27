<?php
// =====================================================================
// api/call_simulator.php — Calling Simulator Backend Process
// -----------------------------------------------------------------
// Runs in the background (asynchronous) when triggered by trigger_alert.php.
// Loops through PENDING calls in data/call_log.json, updates their status
// to CALLING, then COMPLETED, simulating real-world calling intervals.
// =====================================================================

// Prevent execution via web browser if desired, but allow for CLI or async execution
ignore_user_abort(true);
set_time_limit(120);

$callLogFile = __DIR__ . '/../data/call_log.json';

if (!file_exists($callLogFile)) {
    exit("No call log file found.");
}

// Simple step-by-step simulation loop
for ($i = 0; $i < 5; $i++) {
    $raw = file_get_contents($callLogFile);
    $callLog = json_decode($raw, true) ?: [];
    $updated = false;

    foreach ($callLog as &$call) {
        if ($call['status'] === 'PENDING') {
            $call['status'] = 'CALLING';
            $call['timestamp'] = date('Y-m-d H:i:s');
            $updated = true;
            break; // Do one at a time for realism
        } elseif ($call['status'] === 'CALLING') {
            $call['status'] = 'COMPLETED';
            $call['duration_sec'] = rand(15, 45); // Simulated call length
            $call['timestamp'] = date('Y-m-d H:i:s');
            $updated = true;
            break;
        }
    }

    if ($updated) {
        file_put_contents($callLogFile, json_encode($callLog, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
        // Sleep to simulate time between steps
        sleep(2);
    } else {
        // If nothing was updated (all COMPLETED), we are done.
        break;
    }
}
