"""Dash application configuration constants.

Centralizes external stylesheets, scripts, meta tags, and the PWA HTML
template string used during Dash app initialization.
"""

EXTERNAL_STYLESHEETS = [
    # Bootswatch Flatly theme (local copy for offline use)
    "/assets/vendor/bootswatch/flatly/bootstrap.min.css",
    # SECURITY: Font Awesome served locally
    # (no tracking, no checkout popup injection)
    # Using free version CSS-only (no kit system) to prevent checkout code injection
    "/assets/vendor/fontawesome/css/fontawesome.min.css",
    # Font Awesome core (CSS only)
    "/assets/vendor/fontawesome/css/solid.min.css",  # Solid icons
    "/assets/vendor/fontawesome/css/brands.min.css",  # Brand icons (GitHub, etc.)
    "/assets/vendor/codemirror/codemirror.min.css",  # CodeMirror base styles
    "/assets/custom.css",
    # Our custom CSS for standardized styling (includes CodeMirror theme overrides)
    "/assets/help_system.css",  # Help system CSS for progressive disclosure
]

EXTERNAL_SCRIPTS = [
    # Bootstrap JS Bundle (required for CSS interactive states and transitions)
    "/assets/vendor/bootstrap/js/bootstrap.bundle.min.js",
    # CodeMirror 5 (legacy) - Better script tag support than CM6
    # CM6 requires ES modules which don't work well with Dash script loading
    # CM5 provides adequate syntax highlighting for our use case
    "/assets/vendor/codemirror/codemirror.min.js",
    "/assets/vendor/codemirror/mode/sql/sql.min.js",  # Base for query language
    "/assets/jql_language_mode.js",  # JQL tokenizer for syntax highlighting
    "/assets/jql_editor_native.js",
    # Native CodeMirror editors (no textarea transformation)
    "/assets/mobile_navigation.js",
    # Mobile navigation JavaScript for swipe gestures
    "/assets/conflict_resolution_clientside.js",
    # Conflict resolution clientside callbacks (import/export)
    "/assets/active_work_toggle.js",  # Active Work expand/collapse all button
]

META_TAGS = [
    # PWA Meta Tags for Mobile-First Design
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
    # Performance and SEO
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
    # SECURITY: Content Security Policy to prevent unauthorized script injection
    # Prevents Font Awesome and other CDNs from injecting tracking/checkout scripts
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
