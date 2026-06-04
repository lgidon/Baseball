import os
from functools import wraps
from flask import request
from typing import Optional

# Use a class with properties (immutable)
class Config:
    """Application configuration loaded from environment variables."""
    
    # User settings
    USER_NAME: str = os.environ.get("USER_NAME", "Test User")
    THEME_COLOR: str = os.environ.get("THEME_COLOR", "dark")
    
    # Application settings (with validation)
    @property
    def SYNC_INTERVAL_MINS(self) -> int:
        """Sync interval in minutes. Must be a positive integer."""
        value = os.environ.get("SYNC_INTERVAL_MINS", "5")
        try:
            interval = int(value)
            if interval <= 0:
                return 5  # fallback to default
            return interval
        except ValueError:
            return 5  # fallback if not a number
    
    # Admin credentials - NO DEFAULTS!
    ADMIN_USER: Optional[str] = os.environ.get("ADMIN_USER")
    ADMIN_PASSWORD: Optional[str] = os.environ.get("ADMIN_PASSWORD")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration at startup."""
        missing = []
        if not cls.ADMIN_USER:
            missing.append("ADMIN_USER")
        if not cls.ADMIN_PASSWORD:
            missing.append("ADMIN_PASSWORD")
        
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")
        return True

# Create singleton instance
settings = Config()