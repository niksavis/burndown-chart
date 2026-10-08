EXTERNAL_STYLESHEETS = [
    "/assets/vendor/bootswatch/flatly/bootstrap.min.css",
    "/assets/vendor/fontawesome/css/fontawesome.min.css",
    "/assets/vendor/fontawesome/css/solid.min.css",
    "/assets/vendor/fontawesome/css/brands.min.css",
    "/assets/vendor/codemirror/codemirror.min.css",
    "/assets/custom.css",
    "/assets/help_system.css",
]

EXTERNAL_SCRIPTS = [
    "/assets/vendor/bootstrap/js/bootstrap.bundle.min.js",
    "/assets/vendor/codemirror/codemirror.min.js",
    "/assets/vendor/codemirror/mode/sql/sql.min.js",
    "/assets/jql_language_mode.js",
    "/assets/jql_editor_native.js",
    "/assets/mobile_navigation.js",
    "/assets/conflict_resolution_clientside.js",
    "/assets/active_work_toggle.js",
]

META_TAGS = [
    {
        "name": "viewport",
        "content": (
            "width=device-width, initial-scale=1.0, "
            "maximum-scale=5.0, user-scalable=yes"
        ),
    },
    {"name": "theme-color", "content": "#0d6efd"},
    {"name": "apple-mobile-web-app-capable", "content": "yes"},
    {"name": "apple-mobile-web-app-status-bar-style", "content": "default"},
    {"name": "apple-mobile-web-app-title", "content": "Burndown"},
    {"name": "mobile-web-app-capable", "content": "yes"},
    {
        "name": "description",
        "content": (
            "Modern mobile-first agile project forecasting with JIRA integration"
        ),
    },
    {
        "name": "keywords",
        "content": "burndown chart, agile, project management, JIRA, forecasting",
    },
    {"property": "og:title", "content": "Burndown"},
    {"property": "og:type", "content": "website"},
    {
        "property": "og:description",
        "content": (
            "Modern mobile-first agile project forecasting with JIRA integration"
        ),
    },
    {
        "http-equiv": "Content-Security-Policy",
        "content": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com "
            "https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdnjs.cloudflare.com "
            "https://fonts.gstatic.com data:; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://cdn.jsdelivr.net"
        ),
    },
]

INDEX_STRING = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <!-- Custom Favicon -->
        <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
        <link rel="shortcut icon" href="/assets/favicon.svg">
        {%css%}
        <!-- PWA Manifest -->
        <link rel="manifest" href="/assets/manifest.json">
        <!-- Apple Touch Icons -->
        <link rel="apple-touch-icon" href="/assets/icon-192.svg">
        <link rel="apple-touch-icon" sizes="512x512" href="/assets/icon-512.svg">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""
