from patchright.sync_api import sync_playwright
import time
import subprocess
import sys

def ensure_browsers_installed():
    """
    Checks for browser binaries and installs them if needed.
    Since checking existence is complex, we'll run the install command which is idempotent.
    """
    print("Ensuring Chromium is installed...")
    try:
        # Attempt to install chromium using patchright's CLI
        subprocess.run([sys.executable, "-m", "patchright", "install", "chromium"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing browsers: {e}")
    except Exception as e:
        print(f"Unexpected error during browser installation: {e}")

def main():
    ensure_browsers_installed()

    with sync_playwright() as p:
        # Launch Chromium
        # headless=False to see the browser
        print("Launching Chromium...")
        browser = p.chromium.launch(headless=False)
        
        # Create a new context
        context = browser.new_context()
        
        # Create a new page
        page = context.new_page()
        
        print("Navigating to https://chat.deepseek.com/ ...")
        page.goto("https://chat.deepseek.com/")
        
        print("Page loaded. Press Ctrl+C to exit.")
        
        # Keep the script running to keep the browser open
        try:
            # Will interrupt with Ctrl+C
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing browser...")
            browser.close()

if __name__ == "__main__":
    main()
