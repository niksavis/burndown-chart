from utils.offline_assets import local_stylesheet


def test_remote_css_import_is_removed_without_breaking_local_styles() -> None:
    source = (
        "@import url(https://fonts.googleapis.com/css2?family=Lato:"
        "wght@0,400;0,700&display=swap);\n"
        '@import url("local.css");\nbody{color:blue}'
    )
    assert local_stylesheet(source) == '\n@import url("local.css");\nbody{color:blue}'


def test_ordinary_stylesheet_and_local_imports_remain_byte_identical() -> None:
    source = '@import url("local.css");\nbody{color:blue}'
    assert local_stylesheet(source) == source
