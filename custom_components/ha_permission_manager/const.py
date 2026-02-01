"""Constants for ha_permission_manager."""
import re
from enum import IntEnum

DOMAIN = "ha_permission_manager"

# Permission levels
class PermissionLevel(IntEnum):
    """Permission levels for resources."""
    CLOSED = 0   # Hidden / No Access
    VIEW = 1     # Read Only
    LIMITED = 2  # Control entities, no config changes
    EDIT = 3     # Full Admin

PERMISSION_OPTIONS = ["0", "1", "2", "3"]
PERMISSION_LABELS = {
    "0": "Closed",
    "1": "View",
    "2": "Limited",
    "3": "Edit",
}

# Resource type prefixes
PREFIX_AREA = "area_"
PREFIX_LABEL = "label_"
PREFIX_PANEL = "panel_"
PREFIX_AUTOMATION = "automation_"
PREFIX_SCRIPT = "script_"
PREFIX_CUSTOM = "custom_"

# Resource type names for display
RESOURCE_TYPES = {
    "area": "Areas",
    "label": "Labels",
    "panel": "Panels",
    "automation": "Automations",
    "script": "Scripts",
    "custom": "Custom",
}

# Self-reference resource ID (for bootstrap protection)
SELF_PANEL_ID = f"{PREFIX_PANEL}ha_permission_manager"

# Admin group ID (HA built-in)
ADMIN_GROUP_ID = "system-admin"

# Panel configuration
PANEL_TITLE = "Permission Manager"
PANEL_TITLE_ZH = "權限管理"
PANEL_ICON = "mdi:shield-lock"
PANEL_URL = "ha_permission_manager"
PANEL_VERSION = "2.9.6"


def sanitize_slug(name: str) -> str:
    """Sanitize a name for use in entity IDs."""
    # Lowercase and replace common separators with underscores
    slug = name.lower()
    # Replace any non-alphanumeric characters with underscores
    slug = re.sub(r'[^a-z0-9]', '_', slug)
    # Collapse multiple underscores into one
    slug = re.sub(r'_+', '_', slug)
    # Remove leading/trailing underscores
    slug = slug.strip('_')
    # Ensure non-empty
    return slug or 'unnamed'


def build_entity_id(user_name: str, resource_type: str, resource_name: str) -> str:
    """Build entity_id from components."""
    user_slug = sanitize_slug(user_name)
    resource_slug = sanitize_slug(resource_name)
    return f"select.perm_{user_slug}_{resource_type}_{resource_slug}"


def build_unique_id(user_id: str, resource_type: str, resource_id: str) -> str:
    """Build unique_id from components."""
    return f"perm_{user_id}_{resource_type}_{resource_id}"
