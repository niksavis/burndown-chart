# SQL Architecture Guidelines (SQLite3)

**Purpose**: Create efficient, maintainable database schemas and queries that ensure data integrity and performance. These guidelines enforce:
- **Data integrity**: Foreign keys, constraints, and transactions protect data consistency
- **Query efficiency**: Indexes, query optimization, and complexity limits ensure performance
- **Maintainability**: Clear query structure and parameterization enable safe modifications
- **Scalability**: Designs that perform well as data grows
- **Security**: Parameterized queries prevent SQL injection
- **AI collaboration**: Structured patterns optimized for AI-assisted development

## Query Complexity Limits

**CRITICAL RULES**:
- **Query length**: < 50 lines per query (hard limit)
- **Subqueries**: Maximum 2 levels deep
- **JOINs**: Maximum 5 tables per query
- **Warning threshold**: 30 lines → consider refactoring

## Schema Organization

### File Structure

```
data/persistence/
├── schema/
│   ├── 01_core_tables.sql       # Core tables (< 200 lines)
│   ├── 02_lookup_tables.sql     # Lookup/reference tables (< 150 lines)
│   ├── 03_indexes.sql           # All indexes (< 100 lines)
│   ├── 04_views.sql             # Views (< 200 lines)
│   └── 05_triggers.sql          # Triggers (< 150 lines)
└── migrations/
    ├── 001_initial_schema.sql
    ├── 002_add_sprint_tracking.sql
    └── 003_add_indexes.sql
```

### Schema Version Control

```sql
-- Version tracking table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- Record migrations
INSERT INTO schema_version (version, description)
VALUES (1, 'Initial schema');
```

## Table Design Best Practices

### Naming Conventions

```sql
-- GOOD: Lowercase with underscores
CREATE TABLE sprint_issues (
    id INTEGER PRIMARY KEY,
    sprint_id INTEGER NOT NULL,
    issue_key TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- GOOD: Plural for tables, singular for columns
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL
);

-- BAD: Mixed case, unclear
CREATE TABLE SprintIssue (
    Id INTEGER PRIMARY KEY,
    SprintID INTEGER
);
```

### Primary Keys

```sql
-- GOOD: Auto-increment integer primary key
CREATE TABLE profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- GOOD: Composite key when appropriate
CREATE TABLE sprint_issues (
    sprint_id INTEGER NOT NULL,
    issue_key TEXT NOT NULL,
    points INTEGER,
    PRIMARY KEY (sprint_id, issue_key),
    FOREIGN KEY (sprint_id) REFERENCES sprints(sprint_id)
);

-- GOOD: Natural key for lookup tables
CREATE TABLE issue_status (
    status_code TEXT PRIMARY KEY,  -- 'todo', 'in_progress', 'done'
    status_name TEXT NOT NULL,
    sort_order INTEGER
);
```

### Foreign Keys

```sql
-- GOOD: Enable foreign keys (critical for referential integrity)
PRAGMA foreign_keys = ON;

-- GOOD: Explicit foreign key constraints
CREATE TABLE issues (
    issue_id INTEGER PRIMARY KEY,
    sprint_id INTEGER,
    project_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    
    FOREIGN KEY (sprint_id) 
        REFERENCES sprints(sprint_id) 
        ON DELETE SET NULL,
    
    FOREIGN KEY (project_id) 
        REFERENCES projects(project_id) 
        ON DELETE CASCADE,
    
    FOREIGN KEY (status) 
        REFERENCES issue_status(status_code)
        ON UPDATE CASCADE
);

-- BAD: No foreign keys (data integrity risk)
CREATE TABLE issues (
    issue_id INTEGER PRIMARY KEY,
    sprint_id INTEGER,  -- No FK constraint
    project_id INTEGER
);
```

### Indexes

```sql
-- GOOD: Index foreign keys
CREATE INDEX idx_issues_sprint_id ON issues(sprint_id);
CREATE INDEX idx_issues_project_id ON issues(project_id);

-- GOOD: Index frequently queried columns
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_issues_created_at ON issues(created_at);

-- GOOD: Composite index for common queries
CREATE INDEX idx_issues_sprint_status 
    ON issues(sprint_id, status);

-- GOOD: Unique index for business constraints
CREATE UNIQUE INDEX idx_issues_key 
    ON issues(issue_key);

-- GOOD: Partial index for filtered queries
CREATE INDEX idx_issues_active 
    ON issues(status, created_at) 
    WHERE status != 'done';
```

### Data Types

```sql
-- GOOD: Appropriate types
CREATE TABLE metrics (
    metric_id INTEGER PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value REAL,              -- Decimal values
    is_active INTEGER DEFAULT 1,    -- Boolean (0/1)
    created_at TEXT DEFAULT (datetime('now')),  -- ISO8601 timestamp
    data_blob BLOB                  -- Binary data
);

-- GOOD: Check constraints for data validation
CREATE TABLE sprints (
    sprint_id INTEGER PRIMARY KEY,
    sprint_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    velocity REAL CHECK (velocity >= 0),
    status TEXT CHECK (status IN ('planning', 'active', 'completed'))
);

-- GOOD: Default values
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT
);
```

## Query Patterns

### SELECT Best Practices

```sql
-- GOOD: Specific columns, clear formatting
SELECT 
    i.issue_key,
    i.summary,
    i.status,
    i.points,
    s.sprint_name,
    p.project_name
FROM issues i
INNER JOIN sprints s ON i.sprint_id = s.sprint_id
INNER JOIN projects p ON i.project_id = p.project_id
WHERE i.status != 'done'
    AND s.end_date >= date('now')
ORDER BY i.created_at DESC
LIMIT 100;

-- BAD: SELECT *, unclear structure
SELECT * FROM issues, sprints, projects 
WHERE issues.sprint_id = sprints.sprint_id 
AND issues.project_id = projects.project_id;
```

### JOIN Patterns

```sql
-- GOOD: Explicit JOIN types with aliases
SELECT 
    s.sprint_name,
    COUNT(i.issue_id) AS issue_count,
    SUM(i.points) AS total_points,
    AVG(i.points) AS avg_points
FROM sprints s
LEFT JOIN issues i ON s.sprint_id = i.sprint_id
WHERE s.status = 'active'
GROUP BY s.sprint_id, s.sprint_name
HAVING COUNT(i.issue_id) > 0
ORDER BY s.start_date DESC;

-- GOOD: Use subqueries for complex aggregations
SELECT 
    s.sprint_name,
    s.total_points,
    s.completed_points,
    ROUND(100.0 * s.completed_points / NULLIF(s.total_points, 0), 2) AS completion_pct
FROM (
    SELECT 
        s.sprint_id,
        s.sprint_name,
        SUM(i.points) AS total_points,
        SUM(CASE WHEN i.status = 'done' THEN i.points ELSE 0 END) AS completed_points
    FROM sprints s
    LEFT JOIN issues i ON s.sprint_id = i.sprint_id
    GROUP BY s.sprint_id, s.sprint_name
) s
WHERE s.total_points > 0;

-- BAD: Implicit joins (deprecated)
SELECT s.sprint_name, i.issue_key
FROM sprints s, issues i
WHERE s.sprint_id = i.sprint_id;
```

### Common Table Expressions (CTEs)

```sql
-- GOOD: Use CTEs for readability
WITH sprint_stats AS (
    SELECT 
        sprint_id,
        COUNT(*) AS total_issues,
        SUM(points) AS total_points
    FROM issues
    GROUP BY sprint_id
),
completed_stats AS (
    SELECT 
        sprint_id,
        COUNT(*) AS completed_issues,
        SUM(points) AS completed_points
    FROM issues
    WHERE status = 'done'
    GROUP BY sprint_id
)
SELECT 
    s.sprint_name,
    ss.total_issues,
    COALESCE(cs.completed_issues, 0) AS completed_issues,
    ss.total_points,
    COALESCE(cs.completed_points, 0) AS completed_points
FROM sprints s
LEFT JOIN sprint_stats ss ON s.sprint_id = ss.sprint_id
LEFT JOIN completed_stats cs ON s.sprint_id = cs.sprint_id
WHERE s.status = 'active';

-- Better than nested subqueries
```

### Window Functions

```sql
-- GOOD: Use window functions for running totals
SELECT 
    date,
    issues_completed,
    SUM(issues_completed) OVER (
        PARTITION BY sprint_id 
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_completed
FROM daily_progress
ORDER BY sprint_id, date;

-- GOOD: Ranking
SELECT 
    sprint_id,
    issue_key,
    points,
    ROW_NUMBER() OVER (
        PARTITION BY sprint_id 
        ORDER BY points DESC
    ) AS rank_in_sprint
FROM issues
WHERE status = 'done';
```

## INSERT/UPDATE/DELETE Patterns

### Bulk Inserts

```sql
-- GOOD: Use transactions for bulk operations
BEGIN TRANSACTION;

INSERT INTO issues (issue_key, summary, points, sprint_id)
VALUES 
    ('PROJ-1', 'Task 1', 3, 1),
    ('PROJ-2', 'Task 2', 5, 1),
    ('PROJ-3', 'Task 3', 2, 1);

COMMIT;

-- GOOD: Use ON CONFLICT for upserts
INSERT INTO issues (issue_key, summary, points, sprint_id)
VALUES ('PROJ-1', 'Updated Task 1', 5, 1)
ON CONFLICT (issue_key) 
DO UPDATE SET 
    summary = excluded.summary,
    points = excluded.points,
    updated_at = datetime('now');
```

### Safe Updates

```sql
-- GOOD: Always use WHERE clause
UPDATE issues 
SET status = 'done',
    completed_at = datetime('now')
WHERE issue_key = 'PROJ-1';

-- GOOD: Use transactions for safety
BEGIN TRANSACTION;

UPDATE sprints 
SET status = 'completed'
WHERE sprint_id = 1;

UPDATE issues
SET archived = 1
WHERE sprint_id = 1;

COMMIT;

-- BAD: No WHERE clause (updates ALL rows)
UPDATE issues SET status = 'done';
```

### Safe Deletes

```sql
-- GOOD: Soft delete (preferred)
UPDATE issues 
SET deleted_at = datetime('now')
WHERE issue_key = 'PROJ-1';

-- GOOD: Hard delete with WHERE
DELETE FROM issues 
WHERE issue_key = 'PROJ-1'
    AND deleted_at IS NOT NULL;

-- GOOD: Delete with subquery validation
DELETE FROM issues
WHERE sprint_id IN (
    SELECT sprint_id 
    FROM sprints 
    WHERE status = 'cancelled'
);
```

## Views

```sql
-- GOOD: Views for complex queries
CREATE VIEW v_sprint_summary AS
SELECT 
    s.sprint_id,
    s.sprint_name,
    s.start_date,
    s.end_date,
    COUNT(i.issue_id) AS total_issues,
    SUM(i.points) AS total_points,
    SUM(CASE WHEN i.status = 'done' THEN 1 ELSE 0 END) AS completed_issues,
    SUM(CASE WHEN i.status = 'done' THEN i.points ELSE 0 END) AS completed_points,
    ROUND(
        100.0 * SUM(CASE WHEN i.status = 'done' THEN i.points ELSE 0 END) / 
        NULLIF(SUM(i.points), 0), 
        2
    ) AS completion_pct
FROM sprints s
LEFT JOIN issues i ON s.sprint_id = i.sprint_id
GROUP BY s.sprint_id, s.sprint_name, s.start_date, s.end_date;

-- Usage
SELECT * FROM v_sprint_summary
WHERE sprint_name = 'Sprint 1';
```

## Performance Optimization

### EXPLAIN QUERY PLAN

```sql
-- GOOD: Analyze query performance
EXPLAIN QUERY PLAN
SELECT i.issue_key, i.summary, s.sprint_name
FROM issues i
INNER JOIN sprints s ON i.sprint_id = s.sprint_id
WHERE i.status = 'in_progress';

-- Look for:
-- - SCAN vs SEARCH (SEARCH is better with index)
-- - "USING INDEX" indicates index usage
-- - Avoid TEMP B-TREE (usually means missing index)
```

### Optimization Techniques

```sql
-- GOOD: Use EXISTS instead of IN for large datasets
SELECT i.issue_key
FROM issues i
WHERE EXISTS (
    SELECT 1 
    FROM sprints s 
    WHERE s.sprint_id = i.sprint_id 
        AND s.status = 'active'
);

-- vs IN (can be slower for large result sets)
SELECT i.issue_key
FROM issues i
WHERE i.sprint_id IN (
    SELECT sprint_id 
    FROM sprints 
    WHERE status = 'active'
);

-- GOOD: Use LIMIT for pagination
SELECT issue_key, summary
FROM issues
ORDER BY created_at DESC
LIMIT 20 OFFSET 40;  -- Page 3 (20 per page)

-- GOOD: Avoid SELECT * in production queries
SELECT issue_key, summary, status  -- Only needed columns
FROM issues;
```

### WAL Mode (Write-Ahead Logging)

```sql
-- GOOD: Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Benefits:
-- - Concurrent reads while writing
-- - Faster writes
-- - Better crash recovery

-- Check current mode
PRAGMA journal_mode;
```

### Analyze and Optimize

```sql
-- GOOD: Update statistics regularly
ANALYZE;

-- GOOD: Rebuild indexes if needed
REINDEX;

-- GOOD: Vacuum to reclaim space
VACUUM;

-- GOOD: Scheduled maintenance
PRAGMA optimize;
```

## Transactions

### Transaction Patterns

```sql
-- GOOD: Explicit transactions
BEGIN TRANSACTION;

INSERT INTO sprints (sprint_name, start_date, end_date)
VALUES ('Sprint 1', '2026-02-01', '2026-02-14');

INSERT INTO issues (issue_key, sprint_id, points)
VALUES ('PROJ-1', last_insert_rowid(), 5);

COMMIT;

-- GOOD: Rollback on error
BEGIN TRANSACTION;

-- Complex operations

-- If error detected:
ROLLBACK;

-- GOOD: Savepoints for nested transactions
BEGIN TRANSACTION;

SAVEPOINT before_issues;

INSERT INTO issues (...) VALUES (...);

-- If issue insert fails:
ROLLBACK TO SAVEPOINT before_issues;

-- Continue with other operations
COMMIT;
```

## Query Organization in Code

### Python Pattern (Burndown Chart)

```python
# data/persistence/queries.py (< 400 lines)
"""SQL queries for the application."""

# Use constants for reusable queries
GET_SPRINT_SUMMARY = """
    SELECT 
        s.sprint_id,
        s.sprint_name,
        COUNT(i.issue_id) AS issue_count,
        SUM(i.points) AS total_points
    FROM sprints s
    LEFT JOIN issues i ON s.sprint_id = i.sprint_id
    WHERE s.sprint_id = ?
    GROUP BY s.sprint_id, s.sprint_name
"""

LIST_ACTIVE_SPRINTS = """
    SELECT sprint_id, sprint_name, start_date, end_date
    FROM sprints
    WHERE status = 'active'
    ORDER BY start_date DESC
"""

INSERT_ISSUE = """
    INSERT INTO issues (
        issue_key, summary, points, sprint_id, status
    ) VALUES (?, ?, ?, ?, ?)
"""

UPDATE_ISSUE_STATUS = """
    UPDATE issues
    SET status = ?,
        updated_at = datetime('now')
    WHERE issue_key = ?
"""

# If queries exceed 400 lines, split by domain
# queries/sprint_queries.py
# queries/issue_queries.py
# queries/metric_queries.py
```

### Using Queries

```python
# data/persistence/database.py
from data.persistence.queries import GET_SPRINT_SUMMARY, LIST_ACTIVE_SPRINTS
import sqlite3

class Database:
    """Database operations."""
    
    def get_sprint_summary(self, sprint_id: int) -> dict:
        """Get sprint summary."""
        with self.conn:
            cursor = self.conn.execute(GET_SPRINT_SUMMARY, (sprint_id,))
            row = cursor.fetchone()
            return {
                'sprint_id': row[0],
                'sprint_name': row[1],
                'issue_count': row[2],
                'total_points': row[3]
            } if row else None
    
    def list_active_sprints(self) -> list[dict]:
        """List all active sprints."""
        with self.conn:
            cursor = self.conn.execute(LIST_ACTIVE_SPRINTS)
            return [
                {
                    'sprint_id': row[0],
                    'sprint_name': row[1],
                    'start_date': row[2],
                    'end_date': row[3]
                }
                for row in cursor.fetchall()
            ]
```

## Migration Pattern

```sql
-- migrations/002_add_sprint_tracking.sql

-- Add columns to existing table
ALTER TABLE issues ADD COLUMN epic_key TEXT;
ALTER TABLE issues ADD COLUMN priority INTEGER DEFAULT 3;

-- Create new index
CREATE INDEX idx_issues_epic_key ON issues(epic_key);

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES (2, 'Add sprint tracking fields');

-- Verify
SELECT COUNT(*) FROM issues;
```

## Common Pitfalls to Avoid

### 1. N+1 Query Problem

```python
# BAD: N+1 queries (1 + N queries)
sprints = db.execute("SELECT * FROM sprints").fetchall()
for sprint in sprints:
    issues = db.execute(
        "SELECT * FROM issues WHERE sprint_id = ?",
        (sprint['sprint_id'],)
    ).fetchall()

# GOOD: Single query with JOIN
results = db.execute("""
    SELECT s.*, i.*
    FROM sprints s
    LEFT JOIN issues i ON s.sprint_id = i.sprint_id
""").fetchall()
```

### 2. Missing Indexes

```sql
-- BAD: Full table scan
SELECT * FROM issues WHERE status = 'in_progress';

-- GOOD: Create index first
CREATE INDEX idx_issues_status ON issues(status);

-- Now query uses index
SELECT * FROM issues WHERE status = 'in_progress';
```

### 3. SQL Injection

```python
# BAD: String concatenation (SQL injection risk)
query = f"SELECT * FROM issues WHERE issue_key = '{user_input}'"
db.execute(query)

# GOOD: Parameterized queries
query = "SELECT * FROM issues WHERE issue_key = ?"
db.execute(query, (user_input,))
```

## Testing Queries

```python
# tests/test_database.py
import tempfile
import sqlite3
import pytest

@pytest.fixture
def test_db():
    """Create test database."""
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        conn = sqlite3.connect(f.name)
        # Load schema
        with open('schema.sql') as schema:
            conn.executescript(schema.read())
        yield conn
        conn.close()

def test_get_sprint_summary(test_db):
    """Test sprint summary query."""
    # Insert test data
    test_db.execute(
        "INSERT INTO sprints (sprint_name) VALUES ('Test Sprint')"
    )
    sprint_id = test_db.lastrowid
    
    # Test query
    result = test_db.execute(GET_SPRINT_SUMMARY, (sprint_id,)).fetchone()
    
    assert result[1] == 'Test Sprint'
```

## Summary

**Key Principles**:
1. Queries < 50 lines
2. Enable foreign keys
3. Index all foreign keys
4. Use parameterized queries (prevent SQL injection)
5. Enable WAL mode for concurrency
6. Use transactions for data integrity
7. CTEs for complex queries
8. Avoid SELECT *
9. EXPLAIN QUERY PLAN for optimization
10. Regular ANALYZE and VACUUM

**Performance**:
- Index frequently queried columns
- Use EXISTS over IN for large datasets
- Limit result sets with LIMIT/OFFSET
- Enable WAL mode
- Regular ANALYZE updates

**Organization**:
- Schema files < 200 lines each
- Query constants in separate file
- Split by domain if > 400 lines
- Version control migrations
