# Feature 011: Workspace & Query Management - Implementation Concept

**Version**: 3.0.0  
**Status**: Concept - Optimized with Profile-Level Settings  
**Created**: 2025-11-13  
**Updated**: 2025-11-13  
**Author**: AI Agent (GitHub Copilot)

---

## Executive Summary

**Problem**: Users need to switch between different JIRA queries (e.g., different time periods, filters, teams) without losing cached data and recalculating metrics, which can take several minutes for each context switch.

**Current Limitation**: Switching JQL queries invalidates all cache files and requires fresh JIRA API calls + metric recalculation, making it impractical to analyze multiple query variations interactively.

**Proposed Solution**: Implement **two-level hierarchy (Profile → Query)** that isolates data and configuration strategically for easy comparison:

**Key Innovation - Settings Separation**: 
- **Profile** = Shared comparison settings (PERT factor, deadline, field mappings, JIRA config)
- **Query** = JQL variation with dedicated cache (jira_cache.json, project_data.json, metrics_snapshots.json)

**Why This Model?**
- **Easy Comparison**: Same PERT/deadline across queries = apples-to-apples comparison
- **Less Configuration**: Settings configured once per profile, inherited by all queries
- **Natural Workflow**: "Analyze Apache Kafka with these settings, try different time periods"
- **Simpler Implementation**: PERT/deadline move from app_settings → profile config

**Key Benefits**:
- **Instant query switching** within profile (< 50ms) - just swap cache files
- **Consistent comparison baseline** - all queries use same PERT factor and deadline
- **Fast profile switching** between teams/projects (< 100ms)
- **Configuration reuse** - field mappings, JIRA connection shared across queries
- **Multi-tenancy support** - analyze multiple JIRA instances, each with multiple query variations

**Implementation Complexity**: Medium (4-6 days) - Simpler than workspace model
- Minimal code changes (layered persistence architecture)
- No breaking changes to existing APIs
- Backward compatible with current single-workspace model

---

## Problem Analysis

### Current Architecture Pain Points

**1. Global State Model**
```
Current (Single Workspace):
├── app_settings.json          ← One global config
├── project_data.json          ← One global dataset
├── jira_cache.json            ← One global cache
├── jira_changelog_cache.json
├── jira_query_profiles.json   ← Just stores queries, not workspaces
├── metrics_snapshots.json
└── cache/*.json               ← All metrics cache mixed

Problem: No isolation between different queries/projects
```

**2. Cache Invalidation Cascade**

When user switches JQL query in UI:
1. `callbacks/settings.py` detects JQL change (line 305)
2. Invalidates **all** cache files: `glob.glob("cache/*.json")` → `os.remove()`
3. Forces fresh JIRA API fetch (2-5 minutes for large projects)
4. Recalculates all DORA/Flow metrics (30-60 seconds)
5. Regenerates statistics and forecasts

**Total context switch cost**: 3-6 minutes

**3. Configuration Entanglement**

`app_settings.json` contains:
- JIRA connection config (base_url, token)
- Field mappings (DORA/Flow customfield_* mappings)
- UI preferences (PERT factor, deadline)
- Active query (`jql_query`, `active_jql_profile_id`)

**Problem**: Changing query requires changing config, which triggers full cache invalidation.

### User Workflow Analysis

**Desired Workflow** (Currently Impossible):
```
1. User analyzes "Team A - Sprint 10" (KAFKA project, 12w)
   → Fetches data, calculates metrics (3 min)
   → Reviews dashboard, saves insights

2. User switches to "Team B - Q4 2025" (INFRA project, 52w)
   → Fetches data, calculates metrics (5 min)
   → Reviews dashboard

3. User switches back to "Team A - Sprint 10"
   → ❌ Current: Re-fetches data (3 min) - cache was invalidated
   → ✅ Desired: Instant load from profile cache (<1 sec)
```

**Current Workaround**: Users export data to separate folders manually, restart app with different configs. Not practical.

---

## Proposed Solution: Profile-Based Query Management

### Conceptual Model

**Two-Level Organization with Strategic Settings Placement**:

1. **Profile** = Shared comparison baseline settings
   - **Forecast Settings**: PERT factor, deadline (SAME for all queries)
   - **JIRA Connection**: base_url, token, API version
   - **Field Mappings**: DORA/Flow customfield_* mappings
   - **Project Classification**: devops_projects, development_projects
   - **Issue Type Mappings**: bug_types, task_types, flow_end_statuses
   - Multiple queries within profile

2. **Query** = JQL variation with dedicated cache (minimal config)
   - JQL query string ONLY
   - Dedicated cache files (jira_cache, project_data, metrics_snapshots)
   - Fast switching between queries in same profile

**Why Profile-Level Settings?**

✅ **Easy Comparison**: Same PERT factor + deadline across queries = apples-to-apples  
✅ **Less Configuration**: Set PERT/deadline once, applies to all queries in profile  
✅ **Natural Workflow**: "Analyze Team A with pert_factor=1.5, deadline=2025-12-31, try different time periods"  
✅ **Consistent Forecasting**: All queries use same forecast methodology  
✅ **Simpler Implementation**: PERT/deadline move from app_settings → profile config

**Why NOT Query-Level Settings?**

❌ **Harder Comparison**: Different PERT factors = comparing oranges to apples  
❌ **More Configuration**: Would need to set PERT/deadline for EVERY query  
❌ **Inconsistent Results**: Same data, different settings = confusing forecasts

**Example Hierarchy**:
```
Profile: "Apache Kafka Analysis" (pert_factor=1.5, deadline=2025-12-31)
├── Query: "Last 12 Weeks" (JQL: created >= -12w)
├── Query: "Last 52 Weeks" (JQL: created >= -52w)
├── Query: "Bugs Only" (JQL: type = Bug AND created >= -12w)
└── Query: "High Priority" (JQL: priority = High AND created >= -12w)
    → All queries use SAME PERT factor (1.5) and deadline (2025-12-31)
    → Easy to compare: "Which time period gives best velocity forecast?"

Profile: "Infrastructure Team" (pert_factor=2.0, deadline=2025-06-30)
├── Query: "Q4 2025 Delivery" (JQL: project = INFRA AND sprint = Q4)
└── Query: "Technical Debt" (JQL: project = INFRA AND type = Debt)
```

### Data Model

#### Profiles Registry (`profiles.json`)

**Location**: Repository root  
**Purpose**: Registry of all profiles and active selection  
**Format**: JSON

```json
{
  "version": "3.0",
  "active_profile_id": "profile-kafka",
  "active_query_id": "query-12w",
  "profiles": [
    {
      "id": "profile-kafka",
      "name": "Apache Kafka Analysis",
      "description": "Apache Kafka project analysis with 1.5x PERT factor",
      "created_at": "2025-11-08T18:15:35.030265",
      "last_used": "2025-11-13T10:22:15.123456",
      "jira_base_url": "https://issues.apache.org/jira",
      "pert_factor": 1.5,
      "deadline": "2025-12-31",
      "default_query_id": "query-12w",
      "query_count": 4
    },
    {
      "id": "profile-infra",
      "name": "Infrastructure Team",
      "description": "Infrastructure tracking with conservative 2.0x PERT",
      "created_at": "2025-11-09T22:08:11.823009",
      "last_used": "2025-11-13T09:45:30.987654",
      "jira_base_url": "https://jira.example.com",
      "pert_factor": 2.0,
      "deadline": "2025-06-30",
      "default_query_id": "query-q4",
      "query_count": 2
    }
  ]
}
```

#### Profile Configuration (`profiles/profile-kafka/profile.json`)

**Location**: `profiles/profile-kafka/profile.json`  
**Purpose**: Profile-level shared settings for consistent comparison  
**Format**: JSON

```json
{
  "id": "profile-kafka",
  "name": "Apache Kafka Analysis",
  "description": "Apache Kafka project analysis with 1.5x PERT factor",
  "created_at": "2025-11-08T18:15:35.030265",
  "last_used": "2025-11-13T10:22:15.123456",
  
  "forecast_settings": {
    "pert_factor": 1.5,
    "deadline": "2025-12-31",
    "data_points_count": 12  // Number of weeks to show/analyze in charts (independent of JQL time period)
  },
  
  "jira_config": {
    "base_url": "https://issues.apache.org/jira",
    "token": "***",
    "api_version": "v3",
    "points_field": "customfield_10016",
    "cache_size_mb": 100,
    "max_results_per_call": 100
  },
  
  "field_mappings": {
    "deployment_date": "customfield_10001",
    "deployment_successful": "customfield_10002",
    "work_started_date": "customfield_10003",
    "work_completed_date": "customfield_10004",
    "work_type": "customfield_10005",
    "work_item_size": "customfield_10016"
  },
  
  "project_config": {
    "devops_projects": [],
    "development_projects": ["KAFKA"],
    "devops_task_types": ["Task", "Sub-task"],
    "bug_types": ["Bug"],
    "story_types": ["Story"],
    "task_types": ["Task"]
  },
  
  "queries": [
    {
      "id": "query-12w",
      "name": "Sprint Retrospective (12w)",
      "jql_query": "project = KAFKA AND created >= -12w ORDER BY created DESC",
      "created_at": "2025-11-08T18:15:35",
      "last_used": "2025-11-13T10:22:15"
    },
    {
      "id": "query-52w",
      "name": "Yearly Analysis (52w)",
      "jql_query": "project = KAFKA AND created >= -52w ORDER BY created DESC",
      "created_at": "2025-11-09T10:00:00",
      "last_used": "2025-11-12T14:30:00"
    },
    {
      "id": "query-bugs",
      "name": "Bug Analysis Only",
      "jql_query": "project = KAFKA AND type = Bug AND created >= -12w",
      "created_at": "2025-11-10T11:00:00",
      "last_used": "2025-11-11T16:00:00"
    }
  ]
}
```

#### Query Configuration (`profiles/profile-kafka/queries/query-12w/query.json`)

**Location**: `profiles/profile-kafka/queries/query-12w/query.json`  
**Purpose**: Query-specific JQL and metadata (inherits settings from profile)  
**Format**: JSON

```json
{
  "id": "query-12w",
  "name": "Last 12 Weeks",
  "description": "Last 12 weeks for sprint retrospective analysis",
  "jql_query": "project = KAFKA AND created >= -12w ORDER BY created DESC",
  "created_at": "2025-11-08T18:15:35.030265",
  "last_used": "2025-11-13T10:22:15.123456"
}
```

**Note**: PERT factor (1.5) and deadline (2025-12-31) are inherited from parent `profile.json`, not stored per-query. This ensures consistent comparison across all queries in the profile.

#### Directory Structure

```
profiles/
├── profile-kafka/                           # Profile: Apache Kafka Analysis
│   ├── profile.json                         # Profile config (PERT=1.5, deadline=2025-12-31)
│   └── queries/
│       ├── query-12w/                       # Query: Last 12 Weeks
│       │   ├── query.json                   # Query metadata (JQL only)
│       │   ├── project_data.json            # Query-specific statistics
│       │   ├── jira_cache.json              # Query-specific JIRA cache
│       │   ├── jira_changelog_cache.json
│       │   ├── metrics_snapshots.json       # DORA/Flow metrics
│       │   └── cache/                       # Query-specific metric cache
│       │       ├── abc123.json
│       │       └── def456.json
│       ├── query-52w/                       # Query: Last 52 Weeks
│       │   └── ...                          # Same structure
│       ├── query-bugs/                      # Query: Bugs Only
│       │   └── ...
│       └── query-high-priority/             # Query: High Priority Items
│           └── ...
│
├── profile-infra/                           # Profile: Infrastructure Team
│   ├── profile.json                         # Profile config (PERT=2.0, deadline=2025-06-30)
│   └── queries/
│       ├── query-q4/                        # Query: Q4 2025 Delivery
│       │   └── ...
│       └── query-tech-debt/                 # Query: Technical Debt
│           └── ...
│
└── default/                                 # Backward compatibility
    ├── profile.json                         # Migrated from root app_settings.json
    └── queries/
        └── default/                         # Migrated from root files
            └── ...
```

**Benefits of Profile-Level Settings Model**:

✅ **Easier Comparison** - Same PERT/deadline across queries = apples-to-apples  
✅ **Less Configuration** - PERT/deadline set once per profile, not per query  
✅ **Consistent Forecasts** - All queries use same methodology  
✅ **Fast Query Creation** - Clone query = copy JQL string only  
✅ **Natural Workflow** - "Try different time periods with same forecast settings"  
✅ **Simpler Implementation** - PERT/deadline move from app_settings → profile.json  
✅ **Cache Efficiency** - Profile-level JIRA metadata, query-level issue cache  
✅ **Complete Isolation** - No cross-contamination between profiles

### Why This Model is Optimal

#### Comparison: v2.0 (Workspace → Query) vs v3.0 (Profile → Query)

| Aspect                   | v2.0 Workspace Model                        | **v3.0 Profile Model** (Optimal)                |
| ------------------------ | ------------------------------------------- | ----------------------------------------------- |
| **PERT Factor**          | Could be at query level                     | **Profile level** - same for all queries        |
| **Deadline**             | Could be at query level                     | **Profile level** - same baseline               |
| **Query Comparison**     | Harder if PERT differs per query            | **Easy** - same settings = fair comparison      |
| **Configuration Burden** | Set PERT/deadline per query                 | **Minimal** - set once per profile              |
| **Use Case**             | "Different teams, different JIRA instances" | **"Same team, different time periods/filters"** |
| **Implementation**       | Complex (workspace + query configs)         | **Simple** (profile config + query JQL)         |

#### User Workflow Comparison

**v2.0 Workspace Model** (Not Optimal):
```
User: "I want to compare last 12 weeks vs last 52 weeks"
System: "Set PERT factor for 12w query... set PERT for 52w query... 
         Oops, different PERT factors = incomparable results!"
```

**v3.0 Profile Model** (Optimal):
```
User: "I want to compare last 12 weeks vs last 52 weeks"
System: "Both queries use profile's PERT factor (1.5) and deadline (2025-12-31).
         Direct comparison: 12w velocity = 8.5/week, 52w velocity = 7.2/week"
```

---

### Profile vs Query: What Goes Where?

#### Understanding Data Points Count vs JQL Time Period

**CRITICAL DISTINCTION**: These are two separate concepts that work together:

1. **JQL Time Period** (Query-Level - varies per query):
   - Part of JQL query string: `created >= -12w`, `created >= -52w`, etc.
   - Determines **what data to fetch** from JIRA
   - Different queries fetch different time periods for different analyses

2. **Data Points Count** (Profile-Level - same for all queries):
   - UI slider setting: `data_points_count: 12` (in profile config)
   - Determines **how many recent weeks to analyze/show** in charts
   - Post-fetch filter applied after data is loaded
   - Used for velocity calculations, forecast generation, chart display

**Example Workflow**:
```
Profile Settings: data_points_count = 12 weeks

Query 1 "Last 52 Weeks":
  1. JQL fetches: "created >= -52w" → 780 issues (52 weeks of data)
  2. data_points_count filters: Show/analyze only last 12 weeks → 180 issues
  3. Velocity calculated: Using only last 12 weeks = 8.2 items/week

Query 2 "Last 12 Weeks":
  1. JQL fetches: "created >= -12w" → 150 issues (12 weeks of data)
  2. data_points_count filters: All 12 weeks used (no filtering needed)
  3. Velocity calculated: Using all 12 weeks = 8.5 items/week

→ Both queries use SAME 12-week analysis window for fair comparison
→ Users can compare "recent trend" (12w) vs "long-term trend" (52w last-12w)
```

**Why Keep data_points_count at Profile Level?**
- ✅ **Consistent Analysis**: All queries use same analysis window (e.g., "last 12 weeks")
- ✅ **Fair Comparison**: Velocity calculations use same time frame across queries
- ✅ **User Intent**: "Compare these queries using same recent-trend window"
- ✅ **Less Confusion**: Single slider for all queries vs per-query configuration

**Why NOT at Query Level?**
- ❌ **Inconsistent Results**: Query A uses 8 weeks, Query B uses 20 weeks = not comparable
- ❌ **More Configuration**: Would need to set data_points_count for every query
- ❌ **User Confusion**: "Why do queries show different time ranges when I want to compare them?"

#### Profile-Level (Shared Comparison Baseline)

**What**: Settings that should be SAME across all queries for fair comparison

✅ **Forecast Settings** (CRITICAL for comparison):
- **PERT factor** (1.5 for predictable, 2.0 for volatile) - SAME for all queries
- **Deadline** (sprint end, quarter end, etc.) - SAME baseline for all queries
- **Data points count** (weeks to analyze) - SAME analysis window for all queries
  - **Important**: This is NOT the JQL time filter - it's a **post-fetch filter** for analysis
  - Example: JQL fetches 52 weeks (`created >= -52w`), but `data_points_count=12` analyzes only last 12 weeks
  - Purpose: Consistent velocity calculation window across all queries for fair comparison

✅ **JIRA Connection**:
- Base URL (e.g., `https://issues.apache.org/jira`)
- API token/credentials
- API version (v2/v3)
- Story points field

✅ **Field Mappings** (DORA/Flow):
- Deployment date field
- Work started/completed fields
- Work type field
- All other JIRA custom field mappings

✅ **Project Classification**:
- DevOps projects list
- Development projects list
- Issue type mappings (bug_types, task_types, etc.)

✅ **Status Mappings**:
- Completion statuses
- Active statuses
- WIP statuses
- Flow start statuses

**Why profile-level?**: 
- **Easy Comparison**: Same PERT/deadline/data_points_count = apples-to-apples across queries
- **Consistency**: All queries use identical forecast methodology and analysis window
- **Less Config**: Set once, applies to all queries
- **Independent from JQL**: `data_points_count` (weeks to show) is separate from JQL time filter (`created >= -52w`)
  - Example: JQL fetches 52 weeks of data, `data_points_count=12` shows/analyzes only last 12 weeks

#### Query-Level (JQL Variation Only)

**What**: Only the JQL query varies - everything else inherited from profile

✅ **JQL Query String ONLY**:
- Time period filter (`created >= -12w`)
- Issue type filter (`type = Bug`)
- Status filter (`status = Done`)
- Project filter (`project = KAFKA`)
- Any JQL variations

✅ **Dedicated Cache Files** (auto-generated):
- JIRA issue cache (different issues per query)
- Project data (different statistics per query)
- Metrics snapshots (DORA/Flow for this query)
- Metric calculation cache

❌ **NOT at query level**:
- PERT factor (inherited from profile)
- Deadline (inherited from profile)
- Field mappings (inherited from profile)
- UI preferences (inherited from profile)

**Why query-level cache only?**: 
- **Fast Switching**: Just swap cache files, same settings
- **Minimal Config**: Only JQL string stored per query
- **Consistent Results**: Same methodology applied to different data

#### Real-World Examples

**Example 1: Comparing Time Periods (Same Settings)**
```
Profile: "Apache Kafka Q4 Analysis"
  PERT Factor: 1.5 (same for all queries)
  Deadline: 2025-12-31 (same baseline)
  Data Points Count: 12 weeks (analysis window - same for all queries)
  JIRA: issues.apache.org, customfield_10002 = story points
  
  Query 1: "Last 12 Weeks"
    JQL: project = KAFKA AND created >= -12w
    Fetches: 150 issues (12 weeks of data)
    Analysis: All 12 weeks used (data_points_count=12)
    Velocity: 8.5 items/week
    
  Query 2: "Last 52 Weeks"  
    JQL: project = KAFKA AND created >= -52w
    Fetches: 780 issues (52 weeks of data)
    Analysis: Only last 12 weeks used (data_points_count=12)
    Velocity: 7.2 items/week
    
  Query 3: "Last 8 Weeks"
    JQL: project = KAFKA AND created >= -8w
    Fetches: 95 issues (8 weeks of data)
    Analysis: All 8 weeks used (data_points_count=12, but only 8 weeks available)
    Velocity: 9.1 items/week
    
  → Easy to compare: "Which time window gives most reliable forecast?"
  → Same PERT/deadline/analysis_window = fair comparison
  → Note: data_points_count filters the fetched data for analysis
```

**Example 2: Comparing Issue Types (Same Settings)**
```
Profile: "Product Team Sprint Analysis"
  PERT Factor: 1.3 (predictable team)
  Deadline: 2025-11-30 (sprint end)
  Data Points Count: 12 weeks (analysis window)
  JIRA: company.atlassian.net, customfield_10016 = story points
  
  Query 1: "All Issues"
    JQL: project = PRODUCT AND sprint = 42
    Fetches: 45 issues from sprint 42
    Velocity: 12 items/week (using profile's data_points_count=12 for calculation)
    
  Query 2: "Bugs Only"
    JQL: project = PRODUCT AND sprint = 42 AND type = Bug
    Fetches: 8 issues from sprint 42 (bugs)
    Velocity: 2 items/week (using same 12-week analysis window)
    
  Query 3: "Stories Only"
    JQL: project = PRODUCT AND sprint = 42 AND type = Story
    Fetches: 37 issues from sprint 42 (stories)
    Velocity: 10 items/week (using same 12-week analysis window)
    
  → Easy to compare: "What's our bug vs story completion rate?"
  → Same PERT/deadline/analysis_window = consistent forecasts
  → Note: All queries analyze data using same 12-week window for velocity
```

**Example 3: Different JIRA Instances (Separate Profiles)**
```
Profile 1: "Company Production JIRA"
  PERT: 1.8 (conservative)
  Deadline: 2025-06-30
  JIRA: company-prod.atlassian.net, customfield_10016
  Queries: Sprint 42, Q4 2025, Critical Bugs
  
Profile 2: "Apache Open Source Projects"
  PERT: 2.0 (very conservative)
  Deadline: 2025-12-31
  JIRA: issues.apache.org, customfield_10002
  Queries: Kafka 12w, Spark 12w, Flink 12w
  
→ Different JIRA instances = different profiles
→ Different risk tolerance = different PERT factors
```

### Profile & Query Lifecycle

#### 1. Create Profile

**Trigger**: User clicks "Create New Profile" in UI

**Actions**:
1. Generate unique profile ID: `profile-{slugify(name)}`
2. Create profile folder: `profiles/profile-{id}/`
3. Create subdirectories: `queries/`
4. Initialize `profile.json` with:
   - **Forecast settings** (PERT factor, deadline, data_points_count)
   - JIRA config (empty or cloned from active profile)
   - Field mappings (empty or cloned)
   - Project config (empty or cloned)
   - Empty queries array
5. Add profile metadata to `profiles.json`
6. Prompt user to create first query

**Validation**:
- Profile name must be unique (case-insensitive)
- Profile name must be non-empty and ≤ 100 chars
- PERT factor must be 1.0-3.0 (reasonable forecast range)
- Max 50 profiles per installation (prevent bloat)

#### 2. Create Query (in Profile)

**Trigger**: User clicks "New Query" button or creates profile

**Actions**:
1. Generate unique query ID: `query-{slugify(name)}`
2. Create query folder: `profiles/{profile_id}/queries/query-{id}/`
3. Create subdirectories: `cache/`
4. Initialize `query.json` with:
   - **JQL query string ONLY** (no PERT/deadline - inherited from profile)
   - Created/last_used timestamps
5. Initialize empty data files:
   - `project_data.json`
   - `jira_cache.json`
   - `metrics_snapshots.json`
6. Add query metadata to parent `profile.json` queries array
7. Set as active query

**Validation**:
- Query name must be unique within profile
- Query name must be non-empty and ≤ 100 chars
- JQL query must be valid (syntax check via JIRA API)
- Max 100 queries per profile

**Key Difference from v2.0**: Query config is minimal (JQL only), inherits PERT/deadline from profile

#### 3. Switch Profile

**Trigger**: User selects profile from dropdown

**Fast Path** (Target: < 100ms):
```python
def switch_profile(new_profile_id: str) -> Tuple[bool, str]:
    """
    Switch to a different profile (changes PERT/deadline settings).
    
    This is a fast operation (< 100ms) because it only changes
    the active profile pointer and loads the most recent query.
    
    Args:
        new_profile_id: Target profile ID (e.g., "profile-kafka")
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # 1. Validate profile exists
    profile = get_profile_by_id(new_profile_id)
    if not profile:
        return False, f"Profile not found: {new_profile_id}"
    
    # 2. Update active profile in profiles.json (atomic operation)
    registry = load_profiles_registry()
    registry["active_profile_id"] = new_profile_id
    
    # 3. Load profile config and get most recent query
    profile_config = load_profile_config(new_profile_id)
    if not profile_config["queries"]:
        return False, "Profile has no queries - create one first"
    
    # Sort by last_used, pick most recent
    queries = sorted(profile_config["queries"], key=lambda q: q["last_used"], reverse=True)
    registry["active_query_id"] = queries[0]["id"]
    
    save_profiles_registry(registry)
    
    # 4. Update profile's last_used timestamp
    profile_config["last_used"] = datetime.now().isoformat()
    save_profile_config(new_profile_id, profile_config)
    
    # 5. Load profile settings into app state (PERT factor, deadline)
    #    Dashboard callbacks will use these settings for all queries
    
    # 6. Trigger UI reload to reflect new profile/query data
    
    return True, f"Switched to profile: {profile['name']} (PERT={profile['pert_factor']}, deadline={profile['deadline']}), query: {queries[0]['name']}"
```

**No cache invalidation** - cached data remains in query folder.  
**Settings change** - PERT factor and deadline change when switching profiles.

#### 4. Switch Query (within Profile)

**Trigger**: User selects query from dropdown

**Fastest Path** (Target: < 50ms):
```python
def switch_query(profile_id: str, new_query_id: str) -> Tuple[bool, str]:
    """
    Switch to a different query within the same profile.
    
    This is the FASTEST operation (< 50ms) because:
    - No profile settings change (PERT, deadline, field mappings unchanged)
    - Only updates active query pointer
    - Dashboard reloads with different cached data
    - Same forecast methodology applied to different data
    
    Args:
        profile_id: Current profile ID
        new_query_id: Target query ID
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # 1. Validate query exists in profile
    query = get_query_by_id(profile_id, new_query_id)
    if not query:
        return False, f"Query not found: {new_query_id}"
    
    # 2. Update active query in profiles.json (atomic operation)
    registry = load_profiles_registry()
    registry["active_query_id"] = new_query_id
    save_profiles_registry(registry)
    
    # 3. Update query's last_used timestamp
    profile_config = load_profile_config(profile_id)
    for q in profile_config["queries"]:
        if q["id"] == new_query_id:
            q["last_used"] = datetime.now().isoformat()
    save_profile_config(profile_id, profile_config)
    
    query_config = load_query_config(profile_id, new_query_id)
    query_config["last_used"] = datetime.now().isoformat()
    save_query_config(profile_id, new_query_id, query_config)
    
    # 4. Trigger UI reload (minimal - only data files change, NOT settings)
    
    return True, f"Switched to query: {query['name']} (using profile PERT={profile_config['forecast_settings']['pert_factor']})"
```

**UI State Management**:
- Dashboard automatically reloads when `active_query_id` changes
- **Forecast settings stay same** (PERT/deadline from profile)
- Existing callbacks load from active query's cache
- No callback code changes needed (abstraction via `data/persistence.py`)

**Key Advantage**: Users can compare queries directly because PERT/deadline unchanged

#### 5. Delete Workspace

**Trigger**: User clicks "Delete Workspace" (with confirmation)

**Actions**:
1. Confirm not deleting active workspace (require switch first)
2. Show warning: "This will delete N queries and all associated data"
3. Delete workspace folder: `shutil.rmtree(f"workspaces/{workspace_id}")`
4. Remove workspace from `workspaces.json`
5. Update UI dropdown

**Safety**:
- Cannot delete default workspace (last resort)
- Cannot delete active workspace (user must switch first)
- Confirmation dialog requires typing workspace name
- Warning shows count of queries to be deleted

#### 6. Delete Query

**Trigger**: User clicks "Delete Query" (with confirmation)

**Actions**:
1. Confirm not deleting last query in workspace (require at least one)
2. Confirm not deleting active query (require switch first)
3. Delete query folder: `shutil.rmtree(f"workspaces/{workspace_id}/queries/{query_id}")`
4. Remove query from parent `workspace.json` queries array
5. Update UI dropdown

**Safety**:
- Cannot delete last query (workspace must have ≥1 query)
- Cannot delete active query (user must switch first)
- Confirmation dialog with query name verification

#### 7. Duplicate Workspace

**Trigger**: User clicks "Duplicate Workspace"

**Use Case**: Clone JIRA config for different project/instance

**Actions**:
1. Generate new workspace ID
2. Copy source workspace folder → new workspace folder
3. Update workspace name (append " (Copy)")
4. Reset timestamps (created_at, last_used)
5. Optionally clone queries or start empty
6. Switch to new workspace

#### 8. Duplicate Query

**Trigger**: User clicks "Duplicate Query"

**Use Case**: Start with existing JQL, modify slightly (e.g., change time period)

**Actions**:
1. Generate new query ID
2. Copy source query folder → new query folder
3. Update query name (append " (Copy)")
4. Reset timestamps (created_at, last_used)
5. Switch to new query

---

## Architecture & Implementation

### Phase 1: Profile-Aware Persistence Layer (Core)

**Goal**: Make `data/persistence.py` profile-aware without breaking existing code

#### Strategy: Path Abstraction

**Key Insight**: Current code uses hardcoded file paths:
```python
# Current (Global)
APP_SETTINGS_FILE = "app_settings.json"
PROJECT_DATA_FILE = "project_data.json"
JIRA_CACHE_FILE = "jira_cache.json"
```

**Proposed (Profile-Aware)**:
```python
# New abstraction layer
def get_active_profile_workspace() -> str:
    """
    Get file system path to active profile's workspace.
    
    Returns:
        str: Path like "profiles/9b4c2712-e06f-4f21.../
             or "" for root (backward compat)
    """
    profiles_meta = load_profiles_metadata()
    active_id = profiles_meta.get("active_profile_id")
    
    if not active_id or active_id == "default":
        return ""  # Root workspace (legacy mode)
    
    return f"profiles/{active_id}/"

def get_profile_file_path(filename: str) -> str:
    """
    Get full path to a file in active profile workspace.
    
    Args:
        filename: Base filename (e.g., "app_settings.json")
        
    Returns:
        str: Full path (e.g., "profiles/abc123.../app_settings.json")
    """
    workspace = get_active_profile_workspace()
    return os.path.join(workspace, filename)

# Usage in existing functions
def load_app_settings():
    settings_file = get_profile_file_path("app_settings.json")
    # Rest of function unchanged
    if os.path.exists(settings_file):
        with open(settings_file, "r") as f:
            return json.load(f)
    ...
```

**Backward Compatibility**:
- If `profiles.json` doesn't exist → use root workspace (current behavior)
- First-run migration: Move root files to `profiles/default/` workspace
- Zero breaking changes to existing callbacks

#### Profile Management Module

**New Module**: `data/profile_manager.py`

```python
"""
Profile workspace management for multi-context support.

This module provides profile lifecycle operations:
- Create, switch, delete, duplicate profiles
- Profile metadata persistence
- Workspace directory management
"""

import json
import os
import shutil
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from configuration import logger

PROFILES_FILE = "profiles.json"
PROFILES_DIR = "profiles"
DEFAULT_PROFILE_ID = "default"
MAX_PROFILES = 50  # Prevent bloat


class Profile:
    """Profile workspace metadata."""
    
    def __init__(self, 
                 id: str,
                 name: str,
                 description: str = "",
                 jql_query: str = "",
                 jira_base_url: str = "",
                 config_snapshot: Optional[Dict] = None):
        self.id = id
        self.name = name
        self.description = description
        self.jql_query = jql_query
        self.jira_base_url = jira_base_url
        self.created_at = datetime.now().isoformat()
        self.last_used = self.created_at
        self.is_default = (id == DEFAULT_PROFILE_ID)
        self.config_snapshot = config_snapshot or {}
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "jql_query": self.jql_query,
            "jira_base_url": self.jira_base_url,
            "is_default": self.is_default,
            "config_snapshot": self.config_snapshot
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Profile':
        """Deserialize from dictionary."""
        profile = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            jql_query=data.get("jql_query", ""),
            jira_base_url=data.get("jira_base_url", ""),
            config_snapshot=data.get("config_snapshot", {})
        )
        profile.created_at = data.get("created_at", profile.created_at)
        profile.last_used = data.get("last_used", profile.last_used)
        profile.is_default = data.get("is_default", False)
        return profile


def load_profiles_metadata() -> Dict:
    """Load profiles registry."""
    if not os.path.exists(PROFILES_FILE):
        # First run - initialize with default profile
        return {
            "version": "1.0",
            "active_profile_id": DEFAULT_PROFILE_ID,
            "profiles": []
        }
    
    try:
        with open(PROFILES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[Profiles] Error loading metadata: {e}")
        return {
            "version": "1.0",
            "active_profile_id": DEFAULT_PROFILE_ID,
            "profiles": []
        }


def save_profiles_metadata(profiles_meta: Dict) -> bool:
    """Save profiles registry (atomic write)."""
    try:
        temp_file = f"{PROFILES_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(profiles_meta, f, indent=2)
        
        # Atomic rename
        if os.path.exists(PROFILES_FILE):
            os.remove(PROFILES_FILE)
        os.rename(temp_file, PROFILES_FILE)
        
        logger.info("[Profiles] Metadata saved")
        return True
    except Exception as e:
        logger.error(f"[Profiles] Error saving metadata: {e}")
        return False


def get_active_profile() -> Optional[Profile]:
    """Get currently active profile."""
    profiles_meta = load_profiles_metadata()
    active_id = profiles_meta.get("active_profile_id")
    
    if not active_id:
        return None
    
    for profile_data in profiles_meta.get("profiles", []):
        if profile_data["id"] == active_id:
            return Profile.from_dict(profile_data)
    
    return None


def create_profile(name: str, 
                   description: str = "",
                   clone_from_active: bool = True) -> Tuple[bool, str, Optional[Profile]]:
    """
    Create new profile workspace.
    
    Args:
        name: Profile name (must be unique)
        description: Optional description
        clone_from_active: If True, clone current profile's data
        
    Returns:
        Tuple of (success: bool, message: str, profile: Optional[Profile])
    """
    # Validate name
    if not name or len(name) > 100:
        return False, "Profile name must be 1-100 characters", None
    
    profiles_meta = load_profiles_metadata()
    
    # Check uniqueness
    existing_names = [p["name"].lower() for p in profiles_meta.get("profiles", [])]
    if name.lower() in existing_names:
        return False, f"Profile name already exists: {name}", None
    
    # Check max profiles limit
    if len(profiles_meta.get("profiles", [])) >= MAX_PROFILES:
        return False, f"Maximum {MAX_PROFILES} profiles reached", None
    
    # Generate profile ID
    profile_id = str(uuid.uuid4())
    
    # Get current settings for config snapshot
    from data.persistence import load_app_settings
    current_settings = load_app_settings()
    
    config_snapshot = {
        "pert_factor": current_settings.get("pert_factor", 1.5),
        "deadline": current_settings.get("deadline"),
        "field_mappings": current_settings.get("field_mappings", {}),
        "jira_config": current_settings.get("jira_config", {})
    }
    
    # Create profile object
    profile = Profile(
        id=profile_id,
        name=name,
        description=description,
        jql_query=current_settings.get("jql_query", ""),
        jira_base_url=current_settings.get("jira_config", {}).get("base_url", ""),
        config_snapshot=config_snapshot
    )
    
    # Create profile workspace directory
    profile_dir = os.path.join(PROFILES_DIR, profile_id)
    try:
        os.makedirs(profile_dir, exist_ok=True)
        os.makedirs(os.path.join(profile_dir, "cache"), exist_ok=True)
        
        # Clone files if requested
        if clone_from_active:
            _clone_workspace_files(profile_dir)
        else:
            _initialize_empty_workspace(profile_dir)
        
        # Add to profiles metadata
        profiles_meta["profiles"].append(profile.to_dict())
        save_profiles_metadata(profiles_meta)
        
        logger.info(f"[Profiles] Created profile: {name} ({profile_id})")
        return True, f"Profile created: {name}", profile
        
    except Exception as e:
        logger.error(f"[Profiles] Error creating profile: {e}")
        # Cleanup on failure
        if os.path.exists(profile_dir):
            shutil.rmtree(profile_dir)
        return False, f"Failed to create profile: {e}", None


def switch_profile(profile_id: str) -> Tuple[bool, str]:
    """
    Switch to a different profile workspace.
    
    Fast operation (< 100ms) - only updates active pointer.
    
    Args:
        profile_id: Target profile UUID
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    profiles_meta = load_profiles_metadata()
    
    # Find target profile
    target_profile = None
    for profile_data in profiles_meta.get("profiles", []):
        if profile_data["id"] == profile_id:
            target_profile = profile_data
            break
    
    if not target_profile:
        return False, f"Profile not found: {profile_id}"
    
    # Verify workspace exists
    profile_dir = os.path.join(PROFILES_DIR, profile_id)
    if not os.path.exists(profile_dir):
        return False, f"Profile workspace missing: {profile_id}"
    
    # Update active profile (atomic)
    old_active_id = profiles_meta.get("active_profile_id")
    profiles_meta["active_profile_id"] = profile_id
    
    # Update last_used timestamp
    target_profile["last_used"] = datetime.now().isoformat()
    
    # Save metadata
    if not save_profiles_metadata(profiles_meta):
        return False, "Failed to save profile switch"
    
    logger.info(f"[Profiles] Switched: {old_active_id} → {profile_id}")
    return True, f"Switched to profile: {target_profile['name']}"


def delete_profile(profile_id: str) -> Tuple[bool, str]:
    """
    Delete profile and its workspace.
    
    Args:
        profile_id: Profile UUID to delete
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    profiles_meta = load_profiles_metadata()
    
    # Prevent deleting active profile
    if profiles_meta.get("active_profile_id") == profile_id:
        return False, "Cannot delete active profile. Switch to another profile first."
    
    # Prevent deleting last profile
    if len(profiles_meta.get("profiles", [])) <= 1:
        return False, "Cannot delete the only profile."
    
    # Find profile
    profile_index = None
    profile_name = None
    for i, profile_data in enumerate(profiles_meta.get("profiles", [])):
        if profile_data["id"] == profile_id:
            profile_index = i
            profile_name = profile_data["name"]
            break
    
    if profile_index is None:
        return False, f"Profile not found: {profile_id}"
    
    # Delete workspace directory
    profile_dir = os.path.join(PROFILES_DIR, profile_id)
    try:
        if os.path.exists(profile_dir):
            shutil.rmtree(profile_dir)
        
        # Remove from metadata
        profiles_meta["profiles"].pop(profile_index)
        save_profiles_metadata(profiles_meta)
        
        logger.info(f"[Profiles] Deleted profile: {profile_name} ({profile_id})")
        return True, f"Profile deleted: {profile_name}"
        
    except Exception as e:
        logger.error(f"[Profiles] Error deleting profile: {e}")
        return False, f"Failed to delete profile: {e}"


def duplicate_profile(source_profile_id: str, new_name: str) -> Tuple[bool, str, Optional[Profile]]:
    """
    Duplicate existing profile.
    
    Args:
        source_profile_id: Source profile UUID
        new_name: Name for duplicated profile
        
    Returns:
        Tuple of (success: bool, message: str, new_profile: Optional[Profile])
    """
    # Implementation similar to create_profile but copies from specific profile
    # instead of active profile
    pass  # Omitted for brevity - follows same pattern as create_profile


def _clone_workspace_files(target_dir: str) -> None:
    """Clone files from active workspace to new profile workspace."""
    from data.persistence import (
        get_active_profile_workspace,
        APP_SETTINGS_FILE,
        PROJECT_DATA_FILE,
        JIRA_CACHE_FILE,
        JIRA_CHANGELOG_CACHE_FILE
    )
    
    source_workspace = get_active_profile_workspace()
    
    files_to_clone = [
        APP_SETTINGS_FILE,
        PROJECT_DATA_FILE,
        JIRA_CACHE_FILE,
        JIRA_CHANGELOG_CACHE_FILE,
        "metrics_snapshots.json"
    ]
    
    for filename in files_to_clone:
        source_file = os.path.join(source_workspace, filename)
        target_file = os.path.join(target_dir, filename)
        
        if os.path.exists(source_file):
            shutil.copy2(source_file, target_file)
    
    # Clone cache directory
    source_cache = os.path.join(source_workspace, "cache")
    target_cache = os.path.join(target_dir, "cache")
    
    if os.path.exists(source_cache):
        shutil.copytree(source_cache, target_cache, dirs_exist_ok=True)


def _initialize_empty_workspace(target_dir: str) -> None:
    """Initialize empty workspace with default files."""
    from data.schema import get_default_unified_data
    from data.persistence import save_unified_project_data, save_app_settings
    
    # Create minimal default files
    # Implementation details...
    pass
```

### Phase 2: UI Integration

#### Profile Selector Component

**Location**: `ui/profile_selector.py`

```python
"""Profile selector dropdown component."""

import dash_bootstrap_components as dbc
from dash import html

def create_profile_selector(profiles: list, active_profile_id: str):
    """
    Create profile selector dropdown with management buttons.
    
    Args:
        profiles: List of profile dictionaries
        active_profile_id: Currently active profile UUID
        
    Returns:
        Dash Bootstrap Components dropdown
    """
    # Dropdown options
    options = [
        {"label": p["name"], "value": p["id"]} 
        for p in profiles
    ]
    
    return dbc.Row([
        dbc.Col([
            dbc.Label("Active Profile:", className="fw-bold"),
            dbc.Select(
                id="profile-selector",
                options=options,
                value=active_profile_id,
                className="mb-2"
            ),
        ], width=8),
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button(
                    html.I(className="fas fa-plus"),
                    id="btn-create-profile",
                    color="success",
                    size="sm",
                    title="Create New Profile"
                ),
                dbc.Button(
                    html.I(className="fas fa-copy"),
                    id="btn-duplicate-profile",
                    color="info",
                    size="sm",
                    title="Duplicate Current Profile"
                ),
                dbc.Button(
                    html.I(className="fas fa-trash"),
                    id="btn-delete-profile",
                    color="danger",
                    size="sm",
                    title="Delete Profile"
                ),
            ])
        ], width=4, className="text-end")
    ], className="mb-3")
```

#### Profile Management Callbacks

**Location**: `callbacks/profile_management.py`

```python
"""Callbacks for profile switching and management."""

from dash import callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from data.profile_manager import (
    switch_profile,
    create_profile,
    delete_profile,
    load_profiles_metadata
)

@callback(
    Output("url", "pathname", allow_duplicate=True),  # Trigger page reload
    Output("profile-switch-alert", "children"),
    Output("profile-switch-alert", "is_open"),
    Input("profile-selector", "value"),
    State("profile-selector", "value"),  # Previous value
    prevent_initial_call=True
)
def handle_profile_switch(new_profile_id, current_profile_id):
    """
    Handle profile selection from dropdown.
    
    Fast operation - only updates active pointer, no data fetch.
    """
    if new_profile_id == current_profile_id:
        return no_update, no_update, False
    
    success, message = switch_profile(new_profile_id)
    
    if success:
        # Trigger page reload to load new profile's data
        return "/", dbc.Alert(message, color="success"), True
    else:
        # Show error, don't reload
        return no_update, dbc.Alert(message, color="danger"), True


@callback(
    Output("profile-create-modal", "is_open"),
    Input("btn-create-profile", "n_clicks"),
    prevent_initial_call=True
)
def open_create_profile_modal(n_clicks):
    """Open modal for creating new profile."""
    return True


@callback(
    Output("profiles-list", "children", allow_duplicate=True),
    Input("profile-create-submit", "n_clicks"),
    State("profile-name-input", "value"),
    State("profile-description-input", "value"),
    State("profile-clone-toggle", "value"),
    prevent_initial_call=True
)
def handle_create_profile(n_clicks, name, description, clone_active):
    """Create new profile and switch to it."""
    success, message, profile = create_profile(
        name=name,
        description=description,
        clone_from_active=bool(clone_active)
    )
    
    if success:
        # Switch to new profile
        switch_profile(profile.id)
        # Reload profiles dropdown
        profiles_meta = load_profiles_metadata()
        return profiles_meta["profiles"]
    else:
        # Show error
        return no_update
```

#### Settings Panel Integration

**Update**: `callbacks/settings_panel.py`

Add profile selector above JQL query editor:

```python
# Add to settings panel layout
profile_selector_section = create_profile_selector(
    profiles=load_profiles_metadata()["profiles"],
    active_profile_id=get_active_profile().id
)

# Place above JQL editor in panel
```

### Phase 3: Backward Compatibility & Migration

#### First-Run Migration

**Goal**: Seamlessly migrate existing users from single-workspace to profile-based model

**Strategy**:
1. Detect if `profiles.json` doesn't exist
2. Create default profile (`profiles/default/`)
3. Move root files → `profiles/default/`
4. Set `active_profile_id = "default"`

**Implementation**: `data/profile_manager.py::migrate_to_profiles()`

```python
def migrate_to_profiles() -> bool:
    """
    One-time migration: Move root workspace to profiles/default/.
    
    Called automatically on app startup if profiles.json missing.
    
    Returns:
        True if migration successful or already complete
    """
    if os.path.exists(PROFILES_FILE):
        return True  # Already migrated
    
    logger.info("[Migration] Starting workspace migration to profiles...")
    
    # Create profiles directory
    os.makedirs(PROFILES_DIR, exist_ok=True)
    default_dir = os.path.join(PROFILES_DIR, DEFAULT_PROFILE_ID)
    os.makedirs(default_dir, exist_ok=True)
    os.makedirs(os.path.join(default_dir, "cache"), exist_ok=True)
    
    # Move root files to default profile
    files_to_move = [
        "app_settings.json",
        "project_data.json",
        "jira_cache.json",
        "jira_changelog_cache.json",
        "metrics_snapshots.json"
    ]
    
    for filename in files_to_move:
        source = filename
        target = os.path.join(default_dir, filename)
        
        if os.path.exists(source):
            shutil.move(source, target)
            logger.info(f"[Migration] Moved {filename} → {target}")
    
    # Move cache directory
    if os.path.exists("cache"):
        target_cache = os.path.join(default_dir, "cache")
        shutil.move("cache", target_cache)
        logger.info(f"[Migration] Moved cache/ → {target_cache}")
    
    # Create default profile metadata
    from data.persistence import load_app_settings
    settings = load_app_settings()  # Will load from profiles/default/ now
    
    default_profile = Profile(
        id=DEFAULT_PROFILE_ID,
        name="Default Profile",
        description="Migrated from single-workspace configuration",
        jql_query=settings.get("jql_query", ""),
        jira_base_url=settings.get("jira_config", {}).get("base_url", ""),
        config_snapshot={
            "pert_factor": settings.get("pert_factor", 1.5),
            "deadline": settings.get("deadline"),
            "field_mappings": settings.get("field_mappings", {})
        }
    )
    
    # Initialize profiles.json
    profiles_meta = {
        "version": "1.0",
        "active_profile_id": DEFAULT_PROFILE_ID,
        "profiles": [default_profile.to_dict()]
    }
    
    save_profiles_metadata(profiles_meta)
    
    logger.info("[Migration] Workspace migration complete")
    return True
```

**App Startup Hook**: `app.py`

```python
# Add to app initialization
from data.profile_manager import migrate_to_profiles

# One-time migration on startup
if not os.path.exists("profiles.json"):
    logger.info("[App] First run - migrating to profile-based workspaces")
    migrate_to_profiles()
```

---

## Performance Characteristics

### Target Metrics

| Operation                       | Target  | Current | Improvement     |
| ------------------------------- | ------- | ------- | --------------- |
| Profile switch                  | < 100ms | N/A     | ∞ (new feature) |
| Profile creation                | < 500ms | N/A     | -               |
| Context reload (switching back) | < 1s    | 3-6 min | 180-360x faster |
| Cache hit rate                  | > 90%   | ~10%    | 9x improvement  |

### Storage Impact

**Profile Overhead**:
- Metadata: ~500 bytes per profile
- Workspace files: ~5-50 MB per profile (depends on JIRA dataset size)

**Example**:
- 10 profiles × 20 MB average = 200 MB total
- Acceptable for SSD-based development machines

**Cleanup Strategy**:
- Auto-cleanup: Profiles not used in 90 days (configurable)
- Manual cleanup: "Delete Profile" action
- Export/backup: Zip profile folder for archival

---

## Security & Privacy Considerations

### JIRA Credentials

**Problem**: Profiles may reference different JIRA instances with different credentials

**Solution**: Credentials stored per-profile in `app_settings.json` → `profiles/<id>/app_settings.json`

**Privacy Rule** (from Constitution VI):
- Profile exports MUST NOT include credentials
- Profile sharing: Remove `jira_config.token` before sharing
- Validate before commit: No real company names/domains in `profiles.json`

### Data Isolation

**Guarantee**: Profiles are completely isolated
- No cross-contamination between workspaces
- Cache invalidation is profile-scoped only
- Deleting profile = deleting all associated data

---

## Testing Strategy

### Unit Tests

**Module**: `tests/unit/data/test_profile_manager.py`

```python
class TestProfileManager:
    def test_create_profile_success(self, temp_profiles_dir):
        """Test profile creation with valid inputs."""
        
    def test_create_profile_duplicate_name(self, temp_profiles_dir):
        """Test rejection of duplicate profile names."""
        
    def test_switch_profile_updates_active_pointer(self, temp_profiles_dir):
        """Test profile switching updates active_profile_id."""
        
    def test_delete_profile_removes_workspace(self, temp_profiles_dir):
        """Test profile deletion removes directory."""
        
    def test_cannot_delete_active_profile(self, temp_profiles_dir):
        """Test safety check prevents deleting active profile."""
        
    def test_profile_workspace_isolation(self, temp_profiles_dir):
        """Test that data changes in one profile don't affect another."""
```

### Integration Tests

**Module**: `tests/integration/test_profile_switching_workflow.py`

```python
class TestProfileSwitchingWorkflow:
    def test_full_profile_lifecycle(self, temp_profiles_dir):
        """Test create → switch → delete workflow."""
        
    def test_cache_preserved_on_profile_switch(self, temp_profiles_dir):
        """Test that cache remains valid after switching back to profile."""
        
    def test_migration_from_single_workspace(self, temp_workspace):
        """Test first-run migration preserves data."""
```

### Performance Tests

**Target**: Profile switch < 100ms

```python
import pytest
import time

def test_profile_switch_performance(temp_profiles_dir):
    """Test profile switching completes within 100ms."""
    # Setup: Create 2 profiles
    create_profile("Profile A")
    create_profile("Profile B")
    
    # Measure switch time
    start = time.perf_counter()
    switch_profile("profile_b_id")
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    assert elapsed_ms < 100, f"Profile switch took {elapsed_ms:.2f}ms (target: <100ms)"
```

---

## Migration & Rollout Plan

### Phase 1: Core Implementation (Week 1)
- [ ] Implement `data/profile_manager.py`
- [ ] Update `data/persistence.py` with path abstraction
- [ ] Add `migrate_to_profiles()` function
- [ ] Unit tests for profile manager

### Phase 2: UI Integration (Week 1-2)
- [ ] Create `ui/profile_selector.py` component
- [ ] Add `callbacks/profile_management.py`
- [ ] Integrate profile selector into settings panel
- [ ] Modal dialogs for create/delete/duplicate

### Phase 3: Testing & Validation (Week 2)
- [ ] Integration tests for profile workflows
- [ ] Performance benchmarks (switch < 100ms)
- [ ] Manual QA: Test with real JIRA data
- [ ] Backward compatibility validation

### Phase 4: Documentation & Release (Week 2)
- [ ] Update user documentation
- [ ] Add feature to changelog
- [ ] Migration guide for existing users
- [ ] Release notes with examples

---

## Risks & Mitigations

### Risk 1: Storage Bloat

**Scenario**: Users create many profiles, consume excessive disk space

**Mitigation**:
- Max 50 profiles per installation
- Auto-cleanup of profiles unused for 90 days (with confirmation)
- UI warning when disk usage > 500 MB

### Risk 2: Migration Failure

**Scenario**: First-run migration fails, users lose data

**Mitigation**:
- Backup root files before migration: `app_settings.json.backup`
- Rollback function: `rollback_migration()` restores from backup
- Migration log: `migration.log` tracks all file operations
- Validate migrated files match originals (checksum)

### Risk 3: Profile Corruption

**Scenario**: Profile workspace directory deleted/corrupted

**Mitigation**:
- Profile validation on startup: Check workspace exists
- Auto-repair: Recreate missing directories
- Fallback to default profile if active profile missing
- User notification: "Profile X is corrupted, switched to default"

### Risk 4: Callback Compatibility

**Scenario**: Existing callbacks break with profile-aware persistence

**Mitigation**:
- **Zero breaking changes**: Path abstraction is transparent to callbacks
- Comprehensive integration tests: All existing callbacks tested with profiles
- Canary testing: Test with 1 profile first, then multi-profile

---

## Open Questions

1. **Profile Naming**:
   - Should profile names support emoji/Unicode?
   - **Recommendation**: Yes, users like expressive names ("🚀 Production", "🧪 Staging")

2. **Profile Import/Export**:
   - Should we support exporting profiles as `.zip` for sharing?
   - **Recommendation**: Phase 2 feature (not MVP)

3. **Profile Templates**:
   - Should we provide templates ("Bug Analysis", "Sprint Retrospective")?
   - **Recommendation**: Phase 2 feature

4. **Profile Search**:
   - With 50 profiles, do we need search/filter in dropdown?
   - **Recommendation**: Implement if user testing shows need (post-MVP)

---

## Success Metrics

### User Experience
- **Time to switch contexts**: < 1 second (vs. 3-6 minutes currently)
- **Cache hit rate**: > 90% (vs. ~10% with global invalidation)
- **User satisfaction**: Survey after 2 weeks

### Technical
- **Profile switch latency**: < 100ms (P99)
- **Zero data loss**: Migration success rate 100%
- **Storage efficiency**: < 50 MB per profile average

### Adoption
- **Target**: 30% of users create 2+ profiles within first month
- **Power users**: 10% create 5+ profiles

---

## Alternatives Considered

### Alternative 1: Query-Based Cache Keys (Rejected)

**Idea**: Keep global cache but include JQL query in cache key

**Pros**:
- Simpler implementation (no profile directories)
- Minimal code changes

**Cons**:
- Configuration entanglement (field mappings, PERT factor still global)
- No config isolation (users can't have different settings per query)
- Cache bloat (no natural cleanup boundary)

**Decision**: Rejected - doesn't solve configuration isolation problem

### Alternative 2: Database Backend (Rejected)

**Idea**: SQLite database for profiles, cache, settings

**Pros**:
- Relational queries, transactions
- Better for many profiles (>50)

**Cons**:
- Overengineering for current scale
- Increases complexity (schema migrations, query API)
- Breaks current JSON-based persistence model
- Harder to debug/inspect than JSON files

**Decision**: Rejected - violates KISS principle (Constitution IV)

### Alternative 3: Profile-Specific Settings Only (Rejected)

**Idea**: Profiles only store settings, share cache globally

**Pros**:
- Less storage overhead
- Simpler implementation

**Cons**:
- Defeats main purpose (avoiding recalculation on switch)
- Cache invalidation still happens on profile switch
- Doesn't solve performance problem

**Decision**: Rejected - doesn't meet core requirement

---

## Related Work

### Similar Patterns in Other Tools

1. **Git Worktrees**: Multiple checkouts of same repository
   - Inspiration for profile workspace isolation
   - Similar "cheap context switching" benefit

2. **Docker Compose Profiles**: Activate different service sets
   - Profile selection concept
   - Configuration isolation pattern

3. **VS Code Workspaces**: Project-specific settings
   - Multi-root workspaces for context switching
   - Configuration inheritance model

4. **Kubernetes Contexts**: Switch between clusters
   - Fast context switching (kubectl config use-context)
   - Credentials isolation

---

## Conclusion

**Recommendation**: Implement profile-based workspace switching

**Key Benefits**:
- **Immediate value**: Solves critical UX pain point (slow context switching)
- **Low risk**: Backward compatible, minimal code changes
- **Scalable**: Supports 50+ profiles without performance degradation
- **Extensible**: Foundation for future features (templates, sharing, export)

**Effort Estimate**: 4-6 days (1 developer)

**Suggested Next Steps**:
1. Review this concept document with team
2. Create detailed task breakdown (see Migration & Rollout Plan)
3. Prototype Phase 1 (profile manager + path abstraction)
4. User testing with 2-3 power users
5. Full implementation and release

**Alignment with Constitution**:
- ✅ **Layered Architecture (I)**: Persistence layer abstraction preserves separation
- ✅ **Test Isolation (II)**: Profile tests use temp directories
- ✅ **Performance Budgets (III)**: Profile switch < 100ms target
- ✅ **Simplicity (IV)**: JSON-based, no database, minimal complexity
- ✅ **Data Privacy (V)**: Profile export strips credentials
- ✅ **Defensive Refactoring (VI)**: Zero breaking changes, backward compatible

---

---

## Version 3.0 Summary: Why Profile-Level Settings?

### Key Insight from User Feedback

**User's Observation**: "I think it would be easier to have the settings like pert, deadline that are in app_config a part of the profile, and for the query, have the query that is saved and the data and cache files that are created for this query."

**Analysis**: This is CORRECT and superior to the v2.0 workspace model.

### Optimal Design Rationale

**Problem**: Users want to compare different queries (time periods, filters, issue types)

**Solution**: Profile-level PERT/deadline ensures consistent comparison baseline

**Code Impact**:
```python
# Current (v1.0 - root level)
app_settings.json: {pert_factor, deadline, jql_query, ...}

# v2.0 Workspace Model (Not Optimal)
workspace.json: {jira_config, field_mappings, ...}
query.json: {jql, pert_factor, deadline, ...}  # ❌ Per-query settings = hard to compare

# v3.0 Profile Model (Optimal)
profile.json: {pert_factor, deadline, jira_config, field_mappings, ...}  # ✅ Shared settings
query.json: {jql}  # ✅ JQL only
```

### Implementation Benefits

✅ **Simpler Migration**: Move PERT/deadline from `app_settings.json` → `profile.json`  
✅ **Less Code Changes**: Queries don't need settings logic, just JQL storage  
✅ **Better UX**: "Create New Query" = enter JQL string only  
✅ **Easier Testing**: Profile settings tested once, queries are just data  
✅ **Faster Development**: 4-6 days vs 5-7 days (v2.0 workspace model)

### Use Case Validation

**Real-World Scenario**:
```
PM: "Compare last 12 weeks vs last 52 weeks for velocity trends"

v2.0 Workspace Model:
- Risk: User might set different PERT factors per query
- Result: Incomparable forecasts (12w uses PERT=1.3, 52w uses PERT=1.8)

v3.0 Profile Model:
- Guarantee: Both queries use profile's PERT=1.5 and deadline=2025-12-31
- Result: Direct comparison - "12w velocity higher, but 52w more stable"
```

### Decision: Implement v3.0 Profile Model

**Recommended Next Steps**:
1. ✅ Review this concept document (v3.0)
2. Create detailed task breakdown (see Migration & Rollout Plan)
3. Prototype Phase 1: `data/profile_manager.py` + persistence layer
4. User testing with 2-3 power users
5. Full implementation and release

---

**Document Version**: 3.1.0  
**Last Updated**: 2025-11-13  
**Status**: Ready for Review - Optimized with Profile-Level Settings

**v3.1.0 Changes**:
- Clarified `data_points_count` (analysis window) vs JQL time period (data fetch) distinction
- Added detailed explanation of post-fetch filtering for consistent velocity comparison
- Updated examples to show how `data_points_count` filters fetched data
- Confirmed `data_points_count` remains at profile level (not query level) for fair comparison
