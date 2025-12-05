from enum import Enum
from dataclasses import dataclass, field
from typing import List, Any, Optional, Callable, Dict
from .validators import validate_email

class SettingType(Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    INTEGER = "integer"
    PASSWORD = "password"
    TEXTAREA = "textarea"
    DROPDOWN = "dropdown"
    DIVIDER = "divider"
    DESCRIPTION = "description"
    BUTTON = "button"

@dataclass
class SettingField:
    key: str
    label: str
    type: SettingType
    default: Any
    tooltip: Optional[str] = None
    validator: Optional[Callable[[Any], None]] = None
    required: bool = False
    depends: Optional[str] = None
    options: Optional[List[str]] = None # For dropdowns
    action: Optional[str] = None # For buttons (function name to call)

@dataclass
class SettingCategory:
    name: str
    key: str
    fields: List[SettingField] = field(default_factory=list)

# Define the schema
SCHEMA = [
    SettingCategory(
        name="Providers & Credentials",
        key="providers_credentials",
        fields=[
            SettingField(
                key="auto_login",
                label="Auto Login",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Automatically log in using the provided credentials."
            ),
            SettingField(
                key="deepseek_email",
                label="DeepSeek Email",
                type=SettingType.STRING,
                default="",
                tooltip="Email address for DeepSeek login.",
                validator=validate_email,
                required=True,
                depends="providers_credentials.auto_login"
            ),
            SettingField(
                key="deepseek_password",
                label="DeepSeek Password",
                type=SettingType.PASSWORD,
                default="",
                tooltip="Password for DeepSeek login.",
                required=True,
                depends="providers_credentials.auto_login"
            ),
        ]
    ),
    SettingCategory(
        name="Formatting",
        key="formatting",
        fields=[
            SettingField(
                key="formatting_divider_1",
                label="Formatting Template",
                type=SettingType.DIVIDER,
                default=None
            ),
            SettingField(
                key="formatting_preset",
                label="Preset",
                type=SettingType.DROPDOWN,
                default="Classic - Name",
                options=[
                    "Classic - Name", "Classic - Role", 
                    "XML-Like - Name", "XML-Like - Role", 
                    "Divided - Name", "Divided - Role", 
                    "Custom"
                ],
                tooltip="Choose a formatting preset or create your own."
            ),
            SettingField(
                key="formatting_template",
                label="Template",
                type=SettingType.TEXTAREA,
                default="{{name}}: {{content}}",
                tooltip="Define how messages are formatted. Use {{name}}, {{role}}, and {{content}} placeholders."
            ),
            SettingField(
                key="reset_formatting_btn",
                label="Reset to Default",
                type=SettingType.BUTTON,
                default="Reset",
                action="reset_formatting",
                tooltip="Reset formatting template to Classic - Name."
            ),
            SettingField(
                key="formatting_divider",
                label="Divide messages with...",
                type=SettingType.TEXTAREA,
                default="\\n",
                tooltip="String to insert between messages. Default is a newline."
            ),
            SettingField(
                key="apply_formatting",
                label="Apply Formatting",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="Toggle whether to apply the formatting rules."
            ),
            SettingField(
                key="formatting_divider_2",
                label="Name Behavior",
                type=SettingType.DIVIDER,
                default=None
            ),
            SettingField(
                key="name_behavior_desc",
                label="Description",
                type=SettingType.DESCRIPTION,
                default="Toggle methods for fetching names. If all fail or are disabled, role names are used. Methods run in order.",
                tooltip=None
            ),
            SettingField(
                key="enable_msg_objects",
                label="Message Objects",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="Scan for 'name' parameter in message objects."
            ),
            SettingField(
                key="enable_ir2",
                label="IR2 blocks",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="Parse [[IR2u]]username[[/IR2u]]-[[IR2a]]charname[[/IR2a]] blocks."
            ),
            SettingField(
                key="enable_classic_irp",
                label="Classic IntenseRP",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="Parse DATA1: \"{{char}}\" DATA2: \"{{user}}\" blocks."
            ),
            SettingField(
                key="formatting_divider_3",
                label="Injection",
                type=SettingType.DIVIDER,
                default=None
            ),
            SettingField(
                key="injection_desc",
                label="Description",
                type=SettingType.DESCRIPTION,
                default="Insert a small instruction before or after all other messages.",
                tooltip=None
            ),
            SettingField(
                key="injection_position",
                label="Position",
                type=SettingType.DROPDOWN,
                default="Before",
                options=["Before", "After"],
                tooltip="Where to place the injected content."
            ),
            SettingField(
                key="injection_content",
                label="Content",
                type=SettingType.TEXTAREA,
                default="",
                tooltip="Content to inject."
            ),
            SettingField(
                key="reset_injection_btn",
                label="Reset to Default",
                type=SettingType.BUTTON,
                default="Reset",
                action="reset_injection",
                tooltip="Reset injection settings to default."
            ),
        ]
    ),
    SettingCategory(
        name="DeepSeek Behavior",
        key="deepseek_behavior",
        fields=[
            SettingField(
                key="enable_deepthink",
                label="Enable DeepThink",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Toggle the DeepThink button on the DeepSeek interface."
            ),
            SettingField(
                key="send_deepthink",
                label="Send DeepThink",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Include the thinking process in the response sent to the API."
            ),
            SettingField(
                key="enable_search",
                label="Enable Search",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Toggle the Search button on the DeepSeek interface."
            ),
            SettingField(
                key="send_as_text_file",
                label="Send As Text File",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Upload message as a text file instead of typing it."
            ),
            SettingField(
                key="file_upload_timeout",
                label="File Upload Timeout",
                type=SettingType.INTEGER,
                default=15,
                tooltip="Max seconds to wait for the send button to become enabled after file upload.",
                depends="deepseek_behavior.send_as_text_file"
            ),
            SettingField(
                key="anti_censorship",
                label="Anti-Censorship",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="If enabled, suppresses the 'Sorry, that's beyond my current scope' message when content filtering is triggered."
            ),
            SettingField(
                key="clean_regeneration",
                label="Clean Regeneration",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="If enabled, attempts to regenerate the last message instead of creating a new chat if the prompt is identical."
            ),
        ]
    ),
    SettingCategory(
        name="System Settings",
        key="system_settings",
        fields=[
            SettingField(
                key="enable_console",
                label="Enable Console",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Show a console window for viewing application logs."
            ),
        ]
    ),
    SettingCategory(
        name="Console Settings",
        key="console_settings",
        fields=[
            SettingField(
                key="max_lines",
                label="Max Line Limit",
                type=SettingType.INTEGER,
                default=500,
                tooltip="Maximum number of lines to keep in the console history."
            ),
            SettingField(
                key="font_size",
                label="Font Size",
                type=SettingType.INTEGER,
                default=10,
                tooltip="Font size for the console text."
            ),
            SettingField(
                key="color_palette",
                label="Color Palette",
                type=SettingType.DROPDOWN,
                default="Modern",
                options=["Modern", "Classic", "Bright"],
                tooltip="Choose a color scheme for log levels."
            ),
            SettingField(
                key="always_on_top",
                label="Always On Top",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Keep the console window on top of other windows."
            ),
        ]
    ),
]

