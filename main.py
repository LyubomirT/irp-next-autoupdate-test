from patchright.sync_api import sync_playwright
import time
import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

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
        
        # Check if we were redirected to sign in
        if "sign_in" in page.url:
            print("Redirected to sign in page. Attempting to log in...")
            
            email = os.getenv("DEEPSEEK_EMAIL")
            password = os.getenv("DEEPSEEK_PASSWORD")
            
            if not email or not password:
                print("Error: DEEPSEEK_EMAIL or DEEPSEEK_PASSWORD not found in environment variables.")
            else:
                try:
                    # Wait for the form to appear
                    page.wait_for_selector(".ds-sign-up-form__main")
                    
                    # Fill email
                    # The email input is a text input inside the form
                    # Let's try to find the input by type="text" inside the form
                    print(f"Entering email: {email}")
                    page.fill("input[type='text']", email)
                    
                    # Fill password
                    print("Entering password...")
                    page.fill("input[type='password']", password)
                    
                    # Click login button
                    # The button has class ds-sign-up-form__register-button and text "Log in"
                    print("Clicking login button...")
                    page.click(".ds-sign-up-form__register-button")
                    
                    # Wait for navigation back to the chat page
                    page.wait_for_url("https://chat.deepseek.com/")
                    
                except Exception as e:
                    print(f"Error during auto-login: {e}")
        else:
            print("Not redirected to sign in. Continuing...")
        
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
