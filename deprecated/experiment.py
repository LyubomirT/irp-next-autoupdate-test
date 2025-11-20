from patchright.sync_api import sync_playwright
import time
import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

import deepseek_utils

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

def handle_login(page):
    """
    Handles the login process if redirected to the sign-in page.
    """
    # Check if we were redirected to sign in
    if "sign_in" in page.url:
        print("Redirected to sign in page. Attempting to log in...")
        
        email = os.getenv("DEEPSEEK_EMAIL")
        password = os.getenv("DEEPSEEK_PASSWORD")
        
        if not email or not password:
            print("Error: DEEPSEEK_EMAIL or DEEPSEEK_PASSWORD not found in environment variables.")
            return
        else:
            try:
                # Wait for the form to appear
                page.wait_for_selector(".ds-sign-up-form__main")
                
                # Fill email
                print(f"Entering email: {email}")
                page.fill("input[type='text']", email)
                
                # Fill password
                print("Entering password...")
                page.fill("input[type='password']", password)
                
                # Click login button
                print("Clicking login button...")
                page.click(".ds-sign-up-form__register-button")
                
                # Wait for navigation back to the chat page
                page.wait_for_url("https://chat.deepseek.com/")
                print("Login successful.")
                
            except Exception as e:
                print(f"Error during auto-login: {e}")
    else:
        print("Not redirected to sign in. Continuing...")

def run_testing_workflow(page):
    """
    Runs a testing workflow to verify the mini-utils.
    """
    print("\n--- Starting Testing Workflow ---\n")
    
    # 1. Test DeepThink Toggle
    print("Testing DeepThink Toggle...")
    deepseek_utils.set_deepthink_state(page, True)
    time.sleep(2)
    deepseek_utils.set_deepthink_state(page, False)
    time.sleep(2)
    
    # 2. Test Search Toggle
    print("Testing Search Toggle...")
    deepseek_utils.set_search_state(page, True)
    time.sleep(2)
    deepseek_utils.set_search_state(page, False)
    time.sleep(2)
    
    # 3. Test Message Entry
    print("Testing Message Entry...")
    test_message = "Hello, admin is speaking. How are you today?"
    deepseek_utils.enter_message(page, test_message)
    time.sleep(2)
    
    # 4. Test Send Message
    #print("Testing Send Message...")
    #deepseek_utils.send_message(page)
    #time.sleep(2)

    # 5. Test Sidebar Status
    print("Testing Sidebar Status...")
    # Close sidebar
    deepseek_utils.set_sidebar_status(page, False)
    time.sleep(2)
    # Open sidebar
    deepseek_utils.set_sidebar_status(page, True)
    time.sleep(2)

    # 6. Test New Chat (Sidebar)
    print("Testing New Chat (Sidebar)...")
    deepseek_utils.click_new_chat(page, source="sidebar")
    time.sleep(2)

    # 7. Test New Chat (Simple)
    print("Testing New Chat (Simple)...")
    # Must close sidebar first to see simple button
    deepseek_utils.set_sidebar_status(page, False)
    time.sleep(1)
    deepseek_utils.click_new_chat(page, source="simple")
    time.sleep(2)
    # Re-open sidebar for good measure
    deepseek_utils.set_sidebar_status(page, True)
    
    print("\n--- Testing Workflow Completed ---\n")

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
        
        # Handle Login
        handle_login(page)
        
        # Run Testing Workflow
        # This is an arbitrary wait because sometimes the page takes time to load after login
        # Even if Playwright handles it pretty well, I still have Selenium trauma
        time.sleep(3)
        run_testing_workflow(page)
        
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
