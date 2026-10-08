from callbacks.settings.helpers import normalize_show_points


class TestNormalizeShowPoints:
    def test_normalize_checkbox_checked(self):
        assert normalize_show_points(["show"]) is True

    def test_normalize_checkbox_unchecked(self):
        assert normalize_show_points([]) is False

    def test_normalize_integer_true(self):
        assert normalize_show_points(1) is True

    def test_normalize_integer_false(self):
        assert normalize_show_points(0) is False

    def test_normalize_boolean_true(self):
        assert normalize_show_points(True) is True

    def test_normalize_boolean_false(self):
        assert normalize_show_points(False) is False

    def test_normalize_unknown_type(self):
        assert normalize_show_points("invalid") is False
        assert normalize_show_points(None) is False
        assert normalize_show_points({}) is False
