import os
import shutil
from .logger import Logger

class CacheManager:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        self.ensure_cache_dir()

    def ensure_cache_dir(self):
        """Creates the cache directory if it does not exist."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cache_path(self, filename):
        """Returns the full path to a cache file."""
        return os.path.join(self.cache_dir, filename)

    def read_cache(self, filename):
        """Reads content from a cache file. Returns None if file doesn't exist."""
        filepath = self.get_cache_path(filename)
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            Logger.error(f"Error reading cache file {filename}: {e}")
            return None

    def write_cache(self, filename, content):
        """Writes content to a cache file."""
        filepath = self.get_cache_path(filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            Logger.error(f"Error writing to cache file {filename}: {e}")

    def clear_cache(self, filename):
        """Removes a specific cache file."""
        filepath = self.get_cache_path(filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                Logger.error(f"Error clearing cache file {filename}: {e}")

    def clear_all_cache(self):
        """Removes the entire cache directory."""
        if os.path.exists(self.cache_dir):
            try:
                shutil.rmtree(self.cache_dir)
                self.ensure_cache_dir()
            except Exception as e:
                Logger.error(f"Error clearing all cache: {e}")
