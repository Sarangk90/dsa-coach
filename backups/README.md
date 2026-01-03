# Backup Files

This directory contains backup files from the V1 → V2 migration.

## Files

- `progress_v1_backup.json` - User progress data from V1 structure (Dec 24, 2024)
- `progress.backup.json` - Duplicate backup of V1 progress data
- `quests_v1_backup.json` - Quest definitions from V1 structure (Dec 24, 2024)

## V1 vs V2 Structure

### V1 (Deprecated)
- **Quest IDs**: Friendly names (e.g., `two_sum`, `sliding_window`)
- **Pattern IDs**: Friendly names (e.g., `hash_map`, `two_pointers`)
- **Storage**: JSON files (`progress.json`, `quests.json`)
- **Structure**: Flat quest list or day-based grouping

### V2 (Current)
- **Quest IDs**: Hierarchical codes (e.g., `ft_02_c1_p1`, `ft_04_c1_p2`)
- **Pattern IDs**: Curriculum codes (e.g., `ft_02`, `ft_04`)
- **Storage**: SQLite database (`coach.db`)
- **Structure**: Nested curriculum with patterns → concepts → problems

## Migration

The migration from V1 to V2 was completed on December 28, 2024.

**Migration scripts** (in project root):
- `migrate_v1_to_v2.py` - Main migration script
- `cleanup_v1_records.py` - Cleanup duplicate records
- `fix_quests_total.py` - Fix quests_total bug

## Usage

These backups are for reference only. **Do not** use them to restore data, as the V1 structure is no longer supported.

If you need to reference old quest data:
```python
import json

with open('backups/quests_v1_backup.json', 'r') as f:
    v1_quests = json.load(f)

# Access V1 quest data
for quest in v1_quests['quests']:
    print(f"{quest['id']}: {quest['title']}")
```
