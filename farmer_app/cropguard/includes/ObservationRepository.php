<?php
// =====================================================================
// ObservationRepository.php
// -----------------------------------------------------------------
// Authoritative single read/write boundary for observations.json.
// =====================================================================

class ObservationRepository
{
    private string $dataFile;
    private string $lockFile;

    /** Fields we allow through as optional extensions to the core schema. */
    private const ALLOWED_EXTRA_FIELDS = [
        'crop', 'image_path', 'field_id', 'latitude', 'longitude',
        'crop_stage', 'severity', 'affected_area_percentage',
        'validation_status', 'expert_id', 'expert_notes', 'follow_up_to',
        'model_version', 'detections', 'place'
    ];

    public function __construct(?string $dataFile = null)
    {
        $this->dataFile = $dataFile ?? __DIR__ . '/../data/observations.json';
        $this->lockFile = $this->dataFile . '.lock';

        if (!file_exists(dirname($this->dataFile))) {
            mkdir(dirname($this->dataFile), 0777, true);
        }
        if (!file_exists($this->dataFile)) {
            file_put_contents($this->dataFile, json_encode(['observations' => []], JSON_PRETTY_PRINT));
        }
    }

    /**
     * Validate and persist one observation.
     */
    public function save(string $farmerId, string $disease, float $confidence, array $extra = []): array
    {
        $farmerId = trim($farmerId);
        $disease  = trim($disease);

        if ($farmerId === '') {
            throw new InvalidArgumentException('farmer_id is required.');
        }
        if ($disease === '') {
            throw new InvalidArgumentException('disease is required.');
        }
        if (!is_finite($confidence) || $confidence < 0.0 || $confidence > 1.0) {
            throw new InvalidArgumentException('confidence must be a number between 0.0 and 1.0.');
        }

        $safeExtra = [];
        foreach ($extra as $key => $value) {
            if (in_array($key, self::ALLOWED_EXTRA_FIELDS, true)) {
                $safeExtra[$key] = $value;
            }
        }

        // Set default validation status if not supplied
        if (!isset($safeExtra['validation_status'])) {
            $safeExtra['validation_status'] = 'PENDING';
        }

        $lock = $this->acquireLock(LOCK_EX);
        try {
            $db = $this->readUnlocked();

            $record = array_merge([
                'observation_id'    => $this->nextObservationId($db['observations']),
                'farmer_id'         => $farmerId,
                'disease'           => $disease,
                'confidence'        => round($confidence, 4),
                'timestamp'         => (new DateTime())->format(DateTime::ATOM),
                'validation_status' => $safeExtra['validation_status'],
            ], $safeExtra);

            $db['observations'][] = $record;

            $this->writeAtomic($db);

            return $record;
        } finally {
            $this->releaseLock($lock);
        }
    }

    /** Read every observation. */
    public function all(): array
    {
        $lock = $this->acquireLock(LOCK_SH);
        try {
            return $this->readUnlocked()['observations'];
        } finally {
            $this->releaseLock($lock);
        }
    }

    /** Find a single observation by observation_id. */
    public function find(string $observationId): ?array
    {
        $observationId = trim($observationId);
        $observations = $this->all();
        foreach ($observations as $obs) {
            if (isset($obs['observation_id']) && $obs['observation_id'] === $observationId) {
                return $obs;
            }
        }
        return null;
    }

    /**
     * Find observations belonging to a specific farmer.
     */
    public function findByFarmer(string $farmerId): array
    {
        $farmerId = trim($farmerId);
        $observations = $this->all();
        $results = [];
        foreach ($observations as $obs) {
            if (isset($obs['farmer_id']) && $obs['farmer_id'] === $farmerId) {
                $results[] = $obs;
            }
        }
        return $results;
    }

    /**
     * Update an existing observation record.
     */
    public function update(string $observationId, array $updates): ?array
    {
        $observationId = trim($observationId);
        if ($observationId === '') {
            throw new InvalidArgumentException('observation_id is required.');
        }

        $lock = $this->acquireLock(LOCK_EX);
        try {
            $db = $this->readUnlocked();
            $foundIndex = null;

            foreach ($db['observations'] as $idx => $obs) {
                if (isset($obs['observation_id']) && $obs['observation_id'] === $observationId) {
                    $foundIndex = $idx;
                    break;
                }
            }

            if ($foundIndex === null) {
                return null;
            }

            if (isset($updates['confidence'])) {
                $conf = (float)$updates['confidence'];
                if ($conf < 0.0 || $conf > 1.0) {
                    throw new InvalidArgumentException('confidence must be between 0.0 and 1.0.');
                }
                $db['observations'][$foundIndex]['confidence'] = round($conf, 4);
            }

            if (isset($updates['disease']) && trim($updates['disease']) !== '') {
                $db['observations'][$foundIndex]['disease'] = trim($updates['disease']);
            }

            if (isset($updates['farmer_id']) && trim($updates['farmer_id']) !== '') {
                $db['observations'][$foundIndex]['farmer_id'] = trim($updates['farmer_id']);
            }

            foreach (self::ALLOWED_EXTRA_FIELDS as $field) {
                if (array_key_exists($field, $updates)) {
                    $db['observations'][$foundIndex][$field] = $updates[$field];
                }
            }

            $this->writeAtomic($db);
            return $db['observations'][$foundIndex];
        } finally {
            $this->releaseLock($lock);
        }
    }

    /**
     * Delete an observation by observation_id.
     */
    public function delete(string $observationId): bool
    {
        $observationId = trim($observationId);
        if ($observationId === '') {
            return false;
        }

        $lock = $this->acquireLock(LOCK_EX);
        try {
            $db = $this->readUnlocked();
            $initialCount = count($db['observations']);
            $db['observations'] = array_values(array_filter(
                $db['observations'],
                fn($obs) => !isset($obs['observation_id']) || $obs['observation_id'] !== $observationId
            ));

            if (count($db['observations']) < $initialCount) {
                $this->writeAtomic($db);
                return true;
            }
            return false;
        } finally {
            $this->releaseLock($lock);
        }
    }

    /** Summary statistics. */
    public function stats(): array
    {
        $observations = $this->all();
        $total = count($observations);
        if ($total === 0) {
            return [
                'total_observations' => 0,
                'unique_farmers'     => 0,
                'average_confidence' => 0.0,
                'disease_counts'     => [],
                'pending_validation' => 0,
                'confirmed_cases'    => 0,
                'latest_observation' => null,
            ];
        }

        $farmers = [];
        $confSum = 0.0;
        $diseaseCounts = [];
        $pendingVal = 0;
        $confirmedCases = 0;

        foreach ($observations as $obs) {
            if (isset($obs['farmer_id'])) {
                $farmers[$obs['farmer_id']] = true;
            }
            $confSum += (float)($obs['confidence'] ?? 0.0);
            $d = $obs['disease'] ?? 'Unknown';
            $diseaseCounts[$d] = ($diseaseCounts[$d] ?? 0) + 1;

            $vStatus = $obs['validation_status'] ?? 'PENDING';
            if ($vStatus === 'CONFIRMED') {
                $confirmedCases++;
            } elseif ($vStatus === 'PENDING') {
                $pendingVal++;
            }
        }

        return [
            'total_observations' => $total,
            'unique_farmers'     => count($farmers),
            'average_confidence' => round($confSum / $total, 4),
            'disease_counts'     => $diseaseCounts,
            'pending_validation' => $pendingVal,
            'confirmed_cases'    => $confirmedCases,
            'latest_observation' => end($observations) ?: null,
        ];
    }

    /** Clear all observations. */
    public function clear(): void
    {
        $lock = $this->acquireLock(LOCK_EX);
        try {
            $this->writeAtomic(['observations' => []]);
        } finally {
            $this->releaseLock($lock);
        }
    }

    private function nextObservationId(array $observations): string
    {
        $max = 0;
        foreach ($observations as $obs) {
            if (isset($obs['observation_id']) && preg_match('/OBS-(\d+)/', $obs['observation_id'], $m)) {
                $max = max($max, (int) $m[1]);
            }
        }
        return 'OBS-' . str_pad((string) ($max + 1), 6, '0', STR_PAD_LEFT);
    }

    private function readUnlocked(): array
    {
        $raw = file_get_contents($this->dataFile);
        $db  = json_decode($raw, true);
        if (!is_array($db) || !isset($db['observations']) || !is_array($db['observations'])) {
            $db = ['observations' => []];
        }
        return $db;
    }

    private function writeAtomic(array $db): void
    {
        $tmpFile = $this->dataFile . '.tmp_' . uniqid('', true);
        $json = json_encode($db, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        if ($json === false) {
            throw new RuntimeException('Failed to encode observations database.');
        }
        if (file_put_contents($tmpFile, $json) === false) {
            throw new RuntimeException('Failed to write temporary observations file.');
        }
        if (!rename($tmpFile, $this->dataFile)) {
            @unlink($tmpFile);
            throw new RuntimeException('Failed to save observations database.');
        }
    }

    private function acquireLock(int $mode)
    {
        $handle = fopen($this->lockFile, 'c');
        if ($handle === false) {
            throw new RuntimeException('Failed to open database lock file.');
        }
        if (!flock($handle, $mode)) {
            fclose($handle);
            throw new RuntimeException('Failed to acquire database lock.');
        }
        return $handle;
    }

    private function releaseLock($handle): void
    {
        if ($handle) {
            flock($handle, LOCK_UN);
            fclose($handle);
        }
    }
}
