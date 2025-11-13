"""
Pytest configuration for unit tests.

Makes fixtures from tests/fixtures/ available to all unit tests.
"""

# Import all fixtures from tests/fixtures/
from tests.fixtures.temp_profiles_dir import (  # noqa: F401
    temp_profiles_dir,
    temp_profiles_dir_with_default,
)
from tests.fixtures.sample_profile_data import (  # noqa: F401
    sample_profile_data,
    sample_query_data,
    sample_profiles_registry,
    multiple_profile_configs,
    multiple_query_configs,
)
from tests.fixtures.sample_jira_cache import (  # noqa: F401
    sample_jira_issue,
    sample_jira_cache_data,
    sample_jira_response_page_1,
    sample_jira_response_page_2,
    large_jira_cache_50mb,
)
