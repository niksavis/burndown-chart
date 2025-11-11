"""
Script to refactor logging statements in data/jira_simple.py
Applies logging standards: removes emojis, adds [JIRA] prefix, adjusts log levels
"""

import re

# Map of old patterns to new patterns
REPLACEMENTS = [
    # Changelog logging
    (
        r'logger\.info\(f"Fetching JIRA issues WITH changelog from: \{api_endpoint\}"\)',
        r'logger.debug(f"[JIRA] Fetching with changelog from: {api_endpoint}")',
    ),
    (
        r'logger\.info\(f"Using JQL: \{jql\}"\)',
        r'logger.debug(f"[JIRA] JQL: {jql}")',
    ),
    (
        r'logger\.info\(\s*f"Page size: \{page_size\} issues/page, Fields: \{fields\}"\s*\)',
        r'logger.debug(f"[JIRA] Page size: {page_size}, Fields: {fields}")',
    ),
    (
        r"logger\.info\(progress_msg\)",
        r"logger.debug(progress_msg)",
    ),
    # Cache logging
    (
        r'logger\.info\(\s*f"✓ Loaded \{len\(issues\)\} issues from cache \(config hash match\)"\s*\)',
        r'logger.info(f"[Cache] Loaded {len(issues)} issues (hash match)")',
    ),
    (
        r'logger\.info\("New cache miss, checking legacy cache file\.\.\."\)',
        r'logger.debug("[Cache] Checking legacy cache file")',
    ),
    (
        r'logger\.info\(\s*f"Cache miss: JQL query mismatch.*?\)',
        r'logger.debug("[Cache] Miss: JQL mismatch")',
    ),
    (
        r'logger\.info\("Legacy cache JQL mismatch"\)',
        r'logger.debug("[Cache] Legacy cache JQL mismatch")',
    ),
    (
        r'logger\.info\(f"✓ Loaded \{len\(issues\)\} issues from legacy cache"\)',
        r'logger.info(f"[Cache] Loaded {len(issues)} issues from legacy cache")',
    ),
    (
        r'logger\.info\("Migrating legacy cache to new system\.\.\."\)',
        r'logger.info("[Cache] Migrating legacy cache to new system")',
    ),
    (
        r'logger\.debug\("Cache miss: No valid cache found"\)',
        r'logger.debug("[Cache] Miss: No valid cache found")',
    ),
    (
        r'logger\.warning\(\s*f"⚠️  Cache file exceeds.*?\)',
        r'logger.warning(f"[Cache] File exceeds size limit: {size_mb:.1f}MB > {max_size_mb}MB")',
    ),
    (
        r'logger\.error\(f"Cache file validation failed: \{e\}"\)',
        r'logger.error(f"[Cache] Validation failed: {e}")',
    ),
    (
        r'logger\.error\(f"Error getting cache status: \{e\}"\)',
        r'logger.error(f"[Cache] Error getting status: {e}")',
    ),
    # Changelog cache
    (
        r'logger\.info\(\s*f"📥 Caching changelog response.*?\)',
        r'logger.debug(f"[Cache] Saving changelog: {changelog_count} items")',
    ),
    (
        r'logger\.error\(f"Error caching changelog response: \{e\}"\)',
        r'logger.error(f"[Cache] Failed to save changelog: {e}")',
    ),
    (
        r'logger\.info\(\s*f"✓ Loaded \{changelog_count\} changelog entries from cache.*?\)',
        r'logger.info(f"[Cache] Loaded {changelog_count} changelog entries")',
    ),
    (
        r'logger\.info\(\s*f"Cache miss:.*?config_hash mismatch.*?\)',
        r'logger.debug("[Cache] Miss: Config hash mismatch")',
    ),
    (
        r'logger\.warning\(\s*f"Cache validation failed:.*?\)',
        r'logger.warning("[Cache] Validation failed: Invalid format")',
    ),
    (
        r'logger\.info\(\s*f"Cache miss: Changelog data missing.*?\)',
        r'logger.debug("[Cache] Miss: Data missing")',
    ),
    (
        r'logger\.info\(\s*f"Cache miss: age_hours.*?\)',
        r'logger.debug(f"[Cache] Miss: Expired ({age_hours:.1f}h > {max_age_hours}h)")',
    ),
    (
        r'logger\.info\(\s*f"✓ Using cached changelog data.*?\)',
        r'logger.info(f"[Cache] Using cached changelog: {changelog_count} items")',
    ),
    (
        r'logger\.error\(f"Error loading changelog cache: \{e\}"\)',
        r'logger.error(f"[Cache] Failed to load changelog: {e}")',
    ),
    # Warnings
    (
        r'logger\.warning\(\s*f"JQL query may use unavailable ScriptRunner functions.*?\)',
        r'logger.warning(f"[JIRA] Query may use unavailable ScriptRunner functions: {jql_preview}")',
    ),
    (
        r'logger\.warning\(\s*f"⚠️  Unestimated issues detected.*?\)',
        r'logger.warning(f"[JIRA] Unestimated issues detected: {unestimated_count}/{total_issues}")',
    ),
    (
        r'logger\.warning\("No valid dates found in JIRA issues"\)',
        r'logger.warning("[JIRA] No valid dates found in issues")',
    ),
    # Success messages
    (
        r'logger\.info\(f"Generated \{len\(weekly_data\)\} weekly data points from JIRA"\)',
        r'logger.info(f"[JIRA] Generated {len(weekly_data)} weekly data points")',
    ),
    (
        r'logger\.error\(f"Error transforming JIRA data: \{e\}"\)',
        r'logger.error(f"[JIRA] Transform failed: {e}")',
    ),
    # Debug messages (CACHE DEBUG should become regular debug)
    (
        r'logger\.info\(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"\)',
        r"# Removed debug separator",
    ),
    (
        r'logger\.info\(f?"CACHE DEBUG:.*?"\)',
        r"# Removed cache debug message",
    ),
    (
        r'logger\.info\("🔄 CACHE DEBUG:.*?"\)',
        r"# Removed cache debug message",
    ),
    (
        r'logger\.info\("CACHE DEBUG:.*?"\)',
        r"# Removed cache debug message",
    ),
    (
        r'logger\.info\("✓ Using cached issues - changelog cache remains valid"\)',
        r'logger.info("[Cache] Using cached issues, changelog valid")',
    ),
    (
        r'logger\.info\(\s*f"✓ Force refresh complete.*?\)',
        r'logger.info(f"[JIRA] Force refresh complete: {issue_count} issues")',
    ),
    (
        r'logger\.warning\("Failed to cache JIRA response"\)',
        r'logger.warning("[Cache] Failed to save response")',
    ),
    (
        r'logger\.info\(f"DEBUG: Config keys available: \{list\(config\.keys\(\)\)\}"\)',
        r"# Removed debug message",
    ),
    (
        r'logger\.info\(f"DEBUG: devops_projects from config: \{devops_projects\}"\)',
        r"# Removed debug message",
    ),
]


def refactor_file(file_path: str):
    """Apply all replacements to the file"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Refactored {file_path}")
        return True
    else:
        print(f"No changes needed for {file_path}")
        return False


if __name__ == "__main__":
    import sys

    file_path = sys.argv[1] if len(sys.argv) > 1 else "data/jira_simple.py"
    refactor_file(file_path)
