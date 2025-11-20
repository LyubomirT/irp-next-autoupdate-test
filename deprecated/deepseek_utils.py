from patchright.sync_api import Page

# So basically I'm splitting the deepseek structure into four areas as those are the only ones we care about:
# 1. Main input (that's where we enter messages, toggle modes, and attach files)
# 2. Sidebar (that's where we have one of the New Chat buttons and can open/close it)
# 3. Simple controls (that's where we have the other New Chat button and the open sidebar button)
# 4. Message area (n/y implemented here, that will contain the messages themselves)

def set_deepthink_state(page: Page, state: bool):
    """
    Toggles the DeepThink mode to the desired state.
    
    Args:
        page: The playwright page object.
        state: True to enable DeepThink, False to disable.
    """
    # Find the DeepThink button. It contains text "DeepThink".
    button = page.locator("button.ds-toggle-button", has_text="DeepThink")
    
    if not button.count():
        print("DeepThink button not found.")
        return

    # Check if it is currently selected
    # The class 'ds-toggle-button--selected' indicates it is active.
    is_selected = "ds-toggle-button--selected" in button.get_attribute("class")
    
    if is_selected != state:
        print(f"Toggling DeepThink to {state}...")
        button.click()
    else:
        print(f"DeepThink is already {state}.")

def set_search_state(page: Page, state: bool):
    """
    Toggles the Search mode to the desired state.
    
    Args:
        page: The playwright page object.
        state: True to enable Search, False to disable.
    """
    # Find the Search button. It contains text "Search".
    button = page.locator("button.ds-toggle-button", has_text="Search")
    
    if not button.count():
        print("Search button not found.")
        return

    # Check if it is currently selected
    is_selected = "ds-toggle-button--selected" in button.get_attribute("class")
    
    if is_selected != state:
        print(f"Toggling Search to {state}...")
        button.click()
    else:
        print(f"Search is already {state}.")

def enter_message(page: Page, message: str):
    """
    Enters the message into the chat input textarea.
    
    Args:
        page: The playwright page object.
        message: The message text to enter.
    """
    # The textarea has placeholder "Message DeepSeek"
    textarea = page.locator("textarea[placeholder='Message DeepSeek']")
    
    if not textarea.count():
        print("Message textarea not found.")
        return
        
    print(f"Entering message: {message}")
    textarea.fill(message)

def send_message(page: Page):
    """
    Clicks the send button if it is enabled.
    """
    # The send button is a div with role="button" and class "ds-icon-button"
    # The send button has a specific hashed class "_7436101"
    # Gonna use it because it's more reliable than role or other attributes
    send_button = page.locator("div.ds-icon-button._7436101")
    
    if send_button.count():
        # Check if it is disabled. The attribute is 'aria-disabled'
        # Note: get_attribute returns a string, so we compare to "true"
        is_disabled = send_button.get_attribute("aria-disabled") == "true"
        
        if not is_disabled:
            print("Clicking send button...")
            send_button.click()
        else:
            print("Send button is disabled. Cannot send message.")
    else:
        print("Send button could not be located.")

def set_sidebar_status(page: Page, open: bool):
    """
    Sets the sidebar status to open or closed.
    
    Args:
        page: The playwright page object.
        open: True to open the sidebar, False to close it.
    """
    # Selectors
    # Inner sidebar container that gets the hidden class
    sidebar_inner_selector = "div.b8812f16.a2f3d50e"
    # Class added when sidebar is closed (I guess it used to be 'hidden' or something like that)
    sidebar_closed_class = "_70b689f"
    
    # Close button is inside the sidebar
    close_button_selector = "div.ds-icon-button._7d1f5e2"
    # Open button is in the simple container
    open_button_selector = "div.e5bf614e >> div.ds-icon-button._4f3769f >> nth=0"

    # Check current state
    sidebar_inner = page.locator(sidebar_inner_selector)
    if not sidebar_inner.count():
        print("Sidebar inner container not found.")
        return

    # Check if the inner sidebar has the closed class
    class_attr = sidebar_inner.get_attribute("class") or ""
    is_closed = sidebar_closed_class in class_attr
    is_open = not is_closed

    if open:
        if is_open:
            print("Sidebar is already open.")
            return
        
        print("Opening sidebar...")
        open_btn = page.locator(open_button_selector)
        if open_btn.is_visible():
            open_btn.click()
        else:
            print("Open sidebar button not visible.")
            
    else:
        if is_closed:
            print("Sidebar is already closed.")
            return
            
        print("Closing sidebar...")
        close_btn = page.locator(close_button_selector)
        if close_btn.is_visible():
            close_btn.click()
        else:
            print("Close sidebar button not visible.")

def click_new_chat(page: Page, source: str = "auto"):
    """
    Clicks the New Chat button.
    
    Args:
        page: The playwright page object.
        source: "auto", "simple", or "sidebar".
                "auto" tries simple first, then sidebar.
                "simple" forces using the collapsed sidebar button.
                "sidebar" forces using the open sidebar button.
    """
    # Selectors
    simple_new_chat_selector = "div.e5bf614e >> div.ds-icon-button._4f3769f >> nth=1"
    sidebar_new_chat_selector = "div._5a8ac7a.a084f19e"
    
    if source == "simple":
        print("Clicking New Chat (Simple)...")
        btn = page.locator(simple_new_chat_selector)
        if btn.count() > 0:
            btn.click()
        else:
            print("New Chat (Simple) button not found.")
            
    elif source == "sidebar":
        print("Clicking New Chat (Sidebar)...")
        btn = page.locator(sidebar_new_chat_selector)
        if btn.count() > 0:
            btn.click()
        else:
            print("New Chat (Sidebar) button not found.")
            
    elif source == "auto":
        print("Attempting to click New Chat (Auto)...")
        # Try simple first
        simple_btn = page.locator(simple_new_chat_selector)
        if simple_btn.count() > 0:
            print("Found Simple New Chat button. Clicking...")
            simple_btn.click()
            return
            
        # Fallback to sidebar
        sidebar_btn = page.locator(sidebar_new_chat_selector)
        if sidebar_btn.count() > 0:
            print("Found Sidebar New Chat button. Clicking...")
            sidebar_btn.click()
            return
            
        print("Could not find New Chat button in either mode.")
    else:
        print(f"Unknown source: {source}")
