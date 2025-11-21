import json
import os
from pathlib import Path
from typing import Any, Dict
from cryptography.fernet import Fernet
from .schema import SCHEMA, SettingType

class ConfigManager:
    def __init__(self, config_dir: str = "config_data"):
        self.config_dir = Path(config_dir)
        self.settings_file = self.config_dir / "settings.json.enc"
        self.key_file = self.config_dir / "settings.key"
        self.settings: Dict[str, Any] = {}
        
        self._ensure_dir()
        self._load_key()
        self.load_settings()

    def _ensure_dir(self):
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_key(self):
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(self.key)
        self.cipher = Fernet(self.key)

    def load_settings(self):
        if not self.settings_file.exists():
            self._init_default_settings()
            return

        try:
            with open(self.settings_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            self.settings = json.loads(decrypted_data.decode("utf-8"))
            
            # Validate/Merge with schema to ensure all fields exist
            self._merge_defaults()
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._init_default_settings()

    def _init_default_settings(self):
        self.settings = {}
        for category in SCHEMA:
            if category.key not in self.settings:
                self.settings[category.key] = {}
            for field in category.fields:
                self.settings[category.key][field.key] = field.default
        self.save_settings()

    def _merge_defaults(self):
        updated = False
        for category in SCHEMA:
            if category.key not in self.settings:
                self.settings[category.key] = {}
                updated = True
            for field in category.fields:
                if field.key not in self.settings[category.key]:
                    self.settings[category.key][field.key] = field.default
                    updated = True
        if updated:
            self.save_settings()

    def save_settings(self):
        try:
            json_data = json.dumps(self.settings).encode("utf-8")
            encrypted_data = self.cipher.encrypt(json_data)
            
            with open(self.settings_file, "wb") as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_setting(self, category_key: str, field_key: str) -> Any:
        return self.settings.get(category_key, {}).get(field_key)

    def set_setting(self, category_key: str, field_key: str, value: Any):
        if category_key not in self.settings:
            self.settings[category_key] = {}
        self.settings[category_key][field_key] = value
