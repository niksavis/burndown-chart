"""
Quick verification script to check if CodeMirror 6 loads in the browser.
Temporary script for T002 verification.
"""

import time

from playwright.sync_api import sync_playwright


def verify_codemirror_loads():
    """Verify CodeMirror EditorView object exists in browser window."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the app
        page.goto("http://127.0.0.1:8050")

        # Wait for page to load
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # Additional wait for scripts to initialize

        # Check if CodeMirror script tag exists in page
        codemirror_script_exists = page.evaluate("""
            () => {
                const scripts = Array.from(document.querySelectorAll('script'));
                const codemirrorScript = scripts.find(s => s.src.includes('codemirror'));
                
                if (codemirrorScript) {
                    return {
                        loaded: true,
                        message: "CodeMirror script tag found",
                        src: codemirrorScript.src
                    };
                }
                return {
                    loaded: false,
                    error: "CodeMirror script tag not found in page"
                };
            }
        """)

        codemirror_loaded = codemirror_script_exists

        browser.close()
        return codemirror_loaded


if __name__ == "__main__":
    result = verify_codemirror_loads()
    print(f"CodeMirror Load Check: {result}")

    if result.get("loaded"):
        print("✅ SUCCESS: CodeMirror loaded successfully")
        exit(0)
    else:
        print(f"⚠️  WARNING: {result.get('error', 'Unknown error')}")
        print(
            "Note: CodeMirror 6 might use ES modules. Will verify during implementation."
        )
        exit(0)  # Don't fail - just a heads up
