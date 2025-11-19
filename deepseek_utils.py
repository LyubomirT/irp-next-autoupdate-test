from patchright.sync_api import Page

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
