"""
Unit tests for build_config.yaml structure and validity.

Tests that the build configuration file is well-formed and contains all required fields.
"""

from pathlib import Path
import yaml


def get_build_config_path() -> Path:
    """Get the path to build_config.yaml."""
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "build" / "build_config.yaml"


def load_build_config() -> dict:
    """Load and parse build_config.yaml."""
    config_path = get_build_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestBuildConfigStructure:
    """Test build configuration file structure."""

    def test_config_file_exists(self):
        """Test that build_config.yaml exists."""
        config_path = get_build_config_path()
        assert config_path.exists(), f"Build config not found at {config_path}"

    def test_config_is_valid_yaml(self):
        """Test that config file is valid YAML."""
        config = load_build_config()
        assert isinstance(config, dict), "Config should be a dictionary"

    def test_config_has_required_top_level_keys(self):
        """Test that all required top-level sections exist."""
        config = load_build_config()
        required_keys = ["app", "dependencies", "assets", "updater", "build"]

        for key in required_keys:
            assert key in config, f"Missing required section: {key}"


class TestAppConfiguration:
    """Test app section of build config."""

    def test_app_section_exists(self):
        """Test that app section is present."""
        config = load_build_config()
        assert "app" in config

    def test_app_has_name(self):
        """Test that app has a name defined."""
        config = load_build_config()
        assert "name" in config["app"]
        assert isinstance(config["app"]["name"], str)
        assert len(config["app"]["name"]) > 0

    def test_app_has_version_source(self):
        """Test that version_source is defined and points to a file."""
        config = load_build_config()
        assert "version_source" in config["app"]

        version_source = config["app"]["version_source"]
        assert isinstance(version_source, str)

        # Version source should point to configuration/__init__.py
        assert "configuration" in version_source
        assert "__init__.py" in version_source

    def test_app_version_source_file_exists(self):
        """Test that the version source file exists."""
        config = load_build_config()
        version_source = config["app"]["version_source"]

        project_root = Path(__file__).parent.parent.parent.parent
        version_file = project_root / version_source

        assert version_file.exists(), f"Version source file not found: {version_file}"

    def test_app_has_entry_point(self):
        """Test that entry_point is defined."""
        config = load_build_config()
        assert "entry_point" in config["app"]
        assert isinstance(config["app"]["entry_point"], str)

    def test_app_entry_point_exists(self):
        """Test that entry point file exists."""
        config = load_build_config()
        entry_point = config["app"]["entry_point"]

        project_root = Path(__file__).parent.parent.parent.parent
        entry_file = project_root / entry_point

        assert entry_file.exists(), f"Entry point file not found: {entry_file}"

    def test_app_has_icon(self):
        """Test that icon path is defined."""
        config = load_build_config()
        assert "icon" in config["app"]
        assert isinstance(config["app"]["icon"], str)

    def test_app_icon_exists(self):
        """Test that icon file exists."""
        config = load_build_config()
        icon_path = config["app"]["icon"]

        project_root = Path(__file__).parent.parent.parent.parent
        icon_file = project_root / icon_path

        assert icon_file.exists(), f"Icon file not found: {icon_file}"

    def test_app_has_console_setting(self):
        """Test that console setting is defined."""
        config = load_build_config()
        assert "console" in config["app"]
        assert isinstance(config["app"]["console"], bool)


class TestDependenciesConfiguration:
    """Test dependencies section of build config."""

    def test_dependencies_section_exists(self):
        """Test that dependencies section is present."""
        config = load_build_config()
        assert "dependencies" in config

    def test_dependencies_has_include_and_exclude(self):
        """Test that both include and exclude lists exist."""
        config = load_build_config()
        deps = config["dependencies"]

        assert "include" in deps
        assert "exclude" in deps

    def test_dependencies_include_is_list(self):
        """Test that include is a list of strings."""
        config = load_build_config()
        include = config["dependencies"]["include"]

        assert isinstance(include, list)
        assert len(include) > 0
        assert all(isinstance(dep, str) for dep in include)

    def test_dependencies_exclude_is_list(self):
        """Test that exclude is a list of strings."""
        config = load_build_config()
        exclude = config["dependencies"]["exclude"]

        assert isinstance(exclude, list)
        assert len(exclude) > 0
        assert all(isinstance(dep, str) for dep in exclude)

    def test_core_dependencies_included(self):
        """Test that essential dependencies are in the include list."""
        config = load_build_config()
        include = config["dependencies"]["include"]

        # Core dependencies required for the app to run
        core_deps = ["dash", "plotly", "pandas", "waitress"]

        for dep in core_deps:
            assert dep in include, f"Core dependency missing from include: {dep}"

    def test_dev_dependencies_excluded(self):
        """Test that development dependencies are in the exclude list."""
        config = load_build_config()
        exclude = config["dependencies"]["exclude"]

        # Development dependencies that shouldn't be bundled
        dev_deps = ["pytest", "playwright"]

        for dep in dev_deps:
            assert dep in exclude, f"Dev dependency missing from exclude: {dep}"

    def test_no_overlap_between_include_and_exclude(self):
        """Test that no dependency appears in both include and exclude."""
        config = load_build_config()
        include = set(config["dependencies"]["include"])
        exclude = set(config["dependencies"]["exclude"])

        overlap = include & exclude
        assert len(overlap) == 0, f"Dependencies in both include and exclude: {overlap}"


class TestAssetsConfiguration:
    """Test assets section of build config."""

    def test_assets_section_exists(self):
        """Test that assets section is present."""
        config = load_build_config()
        assert "assets" in config

    def test_assets_has_include_list(self):
        """Test that assets include list exists."""
        config = load_build_config()
        assert "include" in config["assets"]

        include = config["assets"]["include"]
        assert isinstance(include, list)
        assert len(include) > 0

    def test_assets_directories_exist(self):
        """Test that all asset directories exist."""
        config = load_build_config()
        asset_dirs = config["assets"]["include"]

        project_root = Path(__file__).parent.parent.parent.parent

        for asset_dir in asset_dirs:
            dir_path = project_root / asset_dir
            assert dir_path.exists(), f"Asset directory not found: {dir_path}"
            assert dir_path.is_dir(), f"Asset path is not a directory: {dir_path}"

    def test_assets_include_contains_assets_folder(self):
        """Test that assets folder is included."""
        config = load_build_config()
        include = config["assets"]["include"]

        assert "assets" in include, "assets folder should be in include list"


class TestUpdaterConfiguration:
    """Test updater section of build config."""

    def test_updater_section_exists(self):
        """Test that updater section is present."""
        config = load_build_config()
        assert "updater" in config

    def test_updater_has_name(self):
        """Test that updater has a name."""
        config = load_build_config()
        assert "name" in config["updater"]
        assert isinstance(config["updater"]["name"], str)
        assert len(config["updater"]["name"]) > 0

    def test_updater_has_entry_point(self):
        """Test that updater entry_point is defined."""
        config = load_build_config()
        assert "entry_point" in config["updater"]
        assert isinstance(config["updater"]["entry_point"], str)

    def test_updater_entry_point_exists(self):
        """Test that updater entry point file exists."""
        config = load_build_config()
        entry_point = config["updater"]["entry_point"]

        project_root = Path(__file__).parent.parent.parent.parent
        entry_file = project_root / entry_point

        assert entry_file.exists(), f"Updater entry point not found: {entry_file}"

    def test_updater_has_icon(self):
        """Test that updater icon is defined."""
        config = load_build_config()
        assert "icon" in config["updater"]

    def test_updater_has_console_setting(self):
        """Test that updater console setting is defined."""
        config = load_build_config()
        assert "console" in config["updater"]
        assert isinstance(config["updater"]["console"], bool)


class TestBuildConfiguration:
    """Test build section of build config."""

    def test_build_section_exists(self):
        """Test that build section is present."""
        config = load_build_config()
        assert "build" in config

    def test_build_has_output_dir(self):
        """Test that output_dir is defined."""
        config = load_build_config()
        assert "output_dir" in config["build"]
        assert isinstance(config["build"]["output_dir"], str)

    def test_build_has_work_dir(self):
        """Test that work_dir is defined."""
        config = load_build_config()
        assert "work_dir" in config["build"]
        assert isinstance(config["build"]["work_dir"], str)

    def test_build_output_dir_is_relative_path(self):
        """Test that output_dir is a relative path."""
        config = load_build_config()
        output_dir = config["build"]["output_dir"]

        # Should not start with / or C:
        assert not output_dir.startswith("/")
        assert not output_dir.startswith("C:")

    def test_build_work_dir_is_relative_path(self):
        """Test that work_dir is a relative path."""
        config = load_build_config()
        work_dir = config["build"]["work_dir"]

        # Should not start with / or C:
        assert not work_dir.startswith("/")
        assert not work_dir.startswith("C:")


class TestConfigurationConsistency:
    """Test consistency across different sections."""

    def test_app_and_updater_use_same_icon(self):
        """Test that app and updater use the same icon file."""
        config = load_build_config()

        app_icon = config["app"]["icon"]
        updater_icon = config["updater"]["icon"]

        assert app_icon == updater_icon, "App and updater should use the same icon"

    def test_app_name_matches_updater_name_prefix(self):
        """Test that updater name is derived from app name."""
        config = load_build_config()

        app_name = config["app"]["name"]
        updater_name = config["updater"]["name"]

        # Updater name should contain or be derived from app name
        assert app_name in updater_name or updater_name.startswith(app_name), (
            "Updater name should be related to app name"
        )

    def test_no_duplicate_asset_directories(self):
        """Test that asset directories are not duplicated."""
        config = load_build_config()
        asset_dirs = config["assets"]["include"]

        assert len(asset_dirs) == len(set(asset_dirs)), (
            "Asset directories should not contain duplicates"
        )
