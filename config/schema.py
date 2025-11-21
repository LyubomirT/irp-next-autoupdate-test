from enum import Enum
from dataclasses import dataclass, field
from typing import List, Any, Optional

class SettingType(Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    INTEGER = "integer"

@dataclass
class SettingField:
    key: str
    label: str
    type: SettingType
    default: Any
    tooltip: Optional[str] = None

@dataclass
class SettingCategory:
    name: str
    key: str
    fields: List[SettingField] = field(default_factory=list)

# Define the schema
SCHEMA = [
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
        ]
    ),
    SettingCategory(
        name="Test Category",
        key="test_category",
        fields=[
            SettingField(
                key="test_bool_1",
                label="Test Boolean 1",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="A test boolean field."
            ),
            SettingField(
                key="test_bool_2",
                label="Test Boolean 2",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Another test boolean field."
            ),
            SettingField(
                key="test_bool_3",
                label="Test Boolean 3",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="Yet another test boolean field."
            ),
        ]
    ),
    SettingCategory(
        name="Another Category",
        key="another_category",
        fields=[
            SettingField(
                key="another_bool_1",
                label="Another Boolean 1",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="A test boolean field."
            ),
            SettingField(
                key="another_bool_2",
                label="Another Boolean 2",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Another test boolean field."
            ),
            SettingField(
                key="another_bool_3",
                label="Another Boolean 3",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="Yet another test boolean field."
            ),
        ]
    ),
    SettingCategory(
        name="Very Long Section",
        key="very_long_section",
        fields=[
            SettingField(
                key="very_long_bool_1",
                label="Very Long Boolean 1",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="A test boolean field."
            ),
            SettingField(
                key="very_long_bool_2",
                label="Very Long Boolean 2",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Another test boolean field."
            ),
            SettingField(
                key="very_long_bool_3",
                label="Very Long Boolean 3",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="Yet another test boolean field."
            ),
            SettingField(
                key="very_long_bool_4",
                label="Very Long Boolean 4",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="Another test boolean field."
            ),
            SettingField(
                key="very_long_bool_5",
                label="Very Long Boolean 5",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="Yet another test boolean field."
            ),
            SettingField(
                key="new_bool_1",
                label="New Boolean 1",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="A new test boolean field."
            ),
            SettingField(
                key="new_bool_2",
                label="New Boolean 2",
                type=SettingType.BOOLEAN,
                default=False,
                tooltip="A new test boolean field."
            ),
            SettingField(
                key="new_bool_3",
                label="New Boolean 3",
                type=SettingType.BOOLEAN,
                default=True,
                tooltip="A new test boolean field."
            ),
        ]
    ),
]
