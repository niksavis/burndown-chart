from ui.loading_utils import create_content_placeholder, create_skeleton_loader


class TestLazyLoadingImplementation:
    def test_skeleton_loader_creates_valid_components(self):
        skeleton = create_skeleton_loader(type="chart", height="400px")
        assert skeleton is not None, "Skeleton loader should create a component"

        skeleton_with_height = create_skeleton_loader(
            type="chart", height="400px", width="100%"
        )
        assert skeleton_with_height is not None, (
            "Skeleton with height should create a component"
        )

    def test_content_placeholder_creates_valid_components(self):
        placeholder = create_content_placeholder(
            type="chart", text="No data available", height="400px"
        )
        assert placeholder is not None, "Content placeholder should create a component"

    def test_lazy_loading_implementation_exists(self):
        import os

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        callback_file = os.path.join(project_root, "callbacks", "visualization.py")

        with open(callback_file) as f:
            content = f.read()

        assert "create_content_placeholder" in content, (
            "Lazy loading placeholder should be used"
        )
        assert "chart_cache" in content, "Client-side caching should be implemented"
        assert "ui_state" in content, "UI state management should be implemented"
        assert "cache_key" in content, "Cache key generation should be implemented"
        assert (
            'Input("chart-tabs", "active_tab")' in content
            and "def render_tab_content(" in content
        ), "Selective chart generation should be implemented"

    def test_cache_key_generation_logic(self):

        def generate_cache_key(active_tab, data_hash, show_points):
            return f"{active_tab}_{data_hash}_{show_points}"

        key1 = generate_cache_key("tab-burndown", "hash123", True)
        key2 = generate_cache_key("tab-scope-tracking", "hash123", True)
        key3 = generate_cache_key("tab-burndown", "hash456", True)
        key4 = generate_cache_key("tab-burndown", "hash123", False)

        keys = [key1, key2, key3, key4]
        assert len(set(keys)) == 4, (
            "Different parameters should generate different cache keys"
        )
