---
applyTo: 'data/cache_manager.py,data/jira/cache_*.py,data/metrics_cache.py,data/persistence/sqlite/issues_cache.py'
description: 'Enforce safe cache management patterns'
---

# Cache Management Instructions

Apply these rules when changing cache logic, invalidation, or cache-related persistence.

## Cache architecture overview

The app uses a **multi-layer caching system**:

1. **SQLite database cache** (primary): `profiles/burndown.db` → `jira_issues` table
   - Normalized storage per profile/query
   - Indexed for fast lookups
   - ACID guarantees

2. **Metrics cache**: `data/metrics_cache.py`
   - In-memory cache of calculated metrics
   - Keyed by (profile_id, query_id, config_hash)
   - Invalidated on config changes

3. **Legacy hash-based cache** (deprecated): `cache/{md5}.json`
   - Being phased out in favor of database

## Core principles

- Cache invalidation is hard: be explicit and conservative
- Always log cache hits/misses for observability
- Never cache sensitive data without sanitization
- Keep cache keys deterministic (no timestamps)
- Validate cached data before use (schema/version checks)

## Cache key patterns

### Database cache

```python
# ✓ GOOD: Composite key (profile_id + query_id)
SELECT * FROM jira_issues
WHERE profile_id = ? AND query_id = ?

# Cache invalidation on query change
DELETE FROM jira_issues WHERE query_id = ?
```

### Metrics cache

```python
# ✓ GOOD: Include config in cache key
config_hash = hashlib.md5(
    json.dumps(config, sort_keys=True).encode()
).hexdigest()
cache_key = f"{profile_id}_{query_id}_{config_hash}"

# ❌ BAD: Exclude config (stale results after config change)
cache_key = f"{profile_id}_{query_id}"
```

## Invalidation rules

### When to invalidate

1. **JQL query changes** → Delete cached issues for that query
2. **Time period changes** → Recalculate metrics, keep raw issues
3. **Field mapping changes** → Recalculate metrics, keep raw issues
4. **Cache age > 24 hours** → Re-fetch from JIRA
5. **Force refresh** → Delete all cached data for active query
6. **Profile deleted** → Cascade delete all cached data

### How to invalidate

```python
# ✓ GOOD: Explicit invalidation with logging
def invalidate_query_cache(query_id: int) -> None:
    """Invalidate cached issues for a specific query."""
    logger.info(f"Invalidating cache for query_id={query_id}")
    execute_query(
        "DELETE FROM jira_issues WHERE query_id = ?",
        (query_id,)
    )
    logger.info(f"Cache invalidated for query_id={query_id}")

# ❌ BAD: Silent invalidation without logging
execute_query("DELETE FROM jira_issues WHERE query_id = ?", (query_id,))
```

## Observability

### Cache hit/miss logging

```python
# ✓ GOOD: Log cache decisions
cached_data = get_from_cache(cache_key)
if cached_data:
    logger.debug(f"Cache HIT: {cache_key[:16]}...")
    return cached_data
else:
    logger.debug(f"Cache MISS: {cache_key[:16]}... (fetching)")
    data = fetch_from_source()
    save_to_cache(cache_key, data)
    return data
```

### Cache metrics

Track and expose:

- Hit rate (hits / total requests)
- Miss reasons (expired, not found, invalidated)
- Cache size (rows in DB, memory usage)
- Last refresh timestamp per query

## Performance considerations

### Indexing

```sql
-- ✓ GOOD: Index on cache lookup keys
CREATE INDEX idx_jira_issues_lookup
ON jira_issues(profile_id, query_id);

-- ✓ GOOD: Index on age checks
CREATE INDEX idx_jira_issues_age
ON jira_issues(fetched_at);
```

### Bulk operations

```python
# ✓ GOOD: Bulk insert for cache population
with transaction():
    cursor.executemany(
        "INSERT INTO jira_issues (...) VALUES (...)",
        issue_batch
    )

# ❌ BAD: Individual inserts (slow)
for issue in issues:
    cursor.execute("INSERT INTO jira_issues ...")
```

## Safety checks

### Cache corruption recovery

```python
# ✓ GOOD: Validate cached data structure
cached_data = get_from_cache(cache_key)
if cached_data:
    try:
        validate_schema(cached_data)  # Check structure
        return cached_data
    except ValidationError:
        logger.warning(f"Cache corrupted for {cache_key}, invalidating")
        invalidate_cache(cache_key)
        # Fall through to fetch fresh data

# ❌ BAD: Assume cached data is always valid
return get_from_cache(cache_key)  # May crash later
```

### Concurrent access

```python
# ✓ GOOD: Use database transactions for consistency
with transaction():
    # Check cache
    data = fetch_cached()
    if not data:
        # Fetch and cache atomically
        data = fetch_from_jira()
        save_to_cache(data)
    return data

# ❌ BAD: Race condition (multiple fetches)
if not cache_exists():
    fetch_and_cache()  # Multiple threads may fetch simultaneously
```

## Before completion

1. Verify invalidation logic handles all trigger cases
2. Confirm cache keys are deterministic and include all relevant config
3. Check logging covers cache hits, misses, and invalidation
4. Test cache performance improvement (before/after metrics)
5. Verify no sensitive data cached without sanitization
6. Run `get_errors` on changed files
7. Test with cold cache (empty DB) and warm cache scenarios

## Related artifacts

- `docs/caching_system.md` - Complete cache architecture
- `.github/skills/sqlite-persistence-safety/SKILL.md` - Database safety
- `.github/skills/jira-integration-reliability/SKILL.md` - JIRA cache coordination
