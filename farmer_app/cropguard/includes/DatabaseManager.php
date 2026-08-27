<?php
// =====================================================================
// DatabaseManager.php — Unified Central Data Platform Access Layer
// -----------------------------------------------------------------
// Single authoritative transactional file repository with atomic locks
// for all CropGuard entities:
//   - Farmers (data/farmers.json)
//   - Fields (data/fields.json)
//   - Observations (data/observations.json)
//   - Weather Observations (data/weather_observations.json)
//   - Surveillance Events (data/priority_events.json)
//   - Expert Validations (data/expert_validations.json)
//   - Notifications / Calls (data/notifications.json, data/call_log.json)
//   - Decisions (data/decisions.json)
// =====================================================================

class DatabaseManager
{
    private string $dataDir;

    public function __construct(?string $dataDir = null)
    {
        $this->dataDir = $dataDir ?? __DIR__ . '/../data';
        if (!file_exists($this->dataDir)) {
            mkdir($this->dataDir, 0777, true);
        }
    }

    public function getDataDir(): string
    {
        return $this->dataDir;
    }

    public function getFilePath(string $entityName): string
    {
        return $this->dataDir . '/' . $entityName . '.json';
    }

    /**
     * Read an entire JSON collection safely.
     */
    public function readCollection(string $entityName): array
    {
        $file = $this->getFilePath($entityName);
        if (!file_exists($file)) {
            return [];
        }
        $raw = file_get_contents($file);
        $data = json_decode($raw, true);
        if (!is_array($data)) {
            return [];
        }
        // Handle wrapper structures if present (e.g. {'observations': [...]}, {'events': [...]})
        if (isset($data[$entityName]) && is_array($data[$entityName])) {
            return $data[$entityName];
        }
        if ($entityName === 'priority_events' && isset($data['events']) && is_array($data['events'])) {
            return $data['events'];
        }
        return $data;
    }

    /**
     * Atomic write with exclusive lock.
     */
    public function writeCollection(string $entityName, array $items, bool $wrapKey = false): void
    {
        $file = $this->getFilePath($entityName);
        $lockFile = $file . '.lock';

        $handle = fopen($lockFile, 'c');
        if (!$handle || !flock($handle, LOCK_EX)) {
            throw new RuntimeException("Could not acquire lock for entity: {$entityName}");
        }

        try {
            $payload = $wrapKey ? [$entityName => array_values($items)] : array_values($items);
            $json = json_encode($payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
            if ($json === false) {
                throw new RuntimeException("JSON encode failed for entity: {$entityName}");
            }

            $tmp = $file . '.tmp_' . uniqid('', true);
            if (file_put_contents($tmp, $json) === false) {
                throw new RuntimeException("Failed to write temporary file for: {$entityName}");
            }
            if (!rename($tmp, $file)) {
                @unlink($tmp);
                throw new RuntimeException("Failed to commit atomic rename for: {$entityName}");
            }
        } finally {
            flock($handle, LOCK_UN);
            fclose($handle);
        }
    }

    /**
     * Find single item in a collection matching a key => value.
     */
    public function findOne(string $entityName, string $key, $value): ?array
    {
        $items = $this->readCollection($entityName);
        foreach ($items as $item) {
            if (isset($item[$key]) && $item[$key] == $value) {
                return $item;
            }
        }
        return null;
    }

    /**
     * Find all items matching a key => value.
     */
    public function findWhere(string $entityName, string $key, $value): array
    {
        $items = $this->readCollection($entityName);
        $results = [];
        foreach ($items as $item) {
            if (isset($item[$key]) && $item[$key] == $value) {
                $results[] = $item;
            }
        }
        return $results;
    }

    /**
     * Insert an item into collection.
     */
    public function insert(string $entityName, array $item, bool $wrapKey = false): array
    {
        $items = $this->readCollection($entityName);
        $items[] = $item;
        $this->writeCollection($entityName, $items, $wrapKey);
        return $item;
    }

    /**
     * Update an item in collection by key => value.
     */
    public function updateWhere(string $entityName, string $key, $value, array $updates, bool $wrapKey = false): ?array
    {
        $items = $this->readCollection($entityName);
        $found = null;
        foreach ($items as $idx => $item) {
            if (isset($item[$key]) && $item[$key] == $value) {
                $items[$idx] = array_merge($item, $updates);
                $found = $items[$idx];
                break;
            }
        }
        if ($found !== null) {
            $this->writeCollection($entityName, $items, $wrapKey);
        }
        return $found;
    }
}
