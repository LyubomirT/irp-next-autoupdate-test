from typing import Dict, Any

class SettingsMigrator:
    @staticmethod
    def migrate(settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrates settings from older versions to the current version.
        Modifies the settings dictionary in-place.
        """
        
        # Migration: Preset Variants (Non-Role/Name to Role/Name)
        if "formatting" in settings:
            formatting = settings["formatting"]
            if "formatting_preset" in formatting:
                preset = formatting["formatting_preset"]
                
                # Map old presets to new defaults
                if preset == "Classic":
                    formatting["formatting_preset"] = "Classic - Name"
                elif preset == "XML-Like":
                    formatting["formatting_preset"] = "XML-Like - Name"
                elif preset == "Divided":
                    formatting["formatting_preset"] = "Divided - Name"
                    
        # Future migrations will be added here
        # e.g. v1 to v2
        
        return settings
