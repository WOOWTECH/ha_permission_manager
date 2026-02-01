"""WebSocket API for ha_permission_manager."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, PREFIX_PANEL, PREFIX_AREA, PREFIX_LABEL

if TYPE_CHECKING:
    from homeassistant.components.websocket_api import ActiveConnection

_LOGGER = logging.getLogger(__name__)


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register WebSocket API handlers."""
    websocket_api.async_register_command(hass, ws_get_panel_permissions)
    websocket_api.async_register_command(hass, ws_get_all_permissions)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "permission_manager/get_panel_permissions",
    }
)
@callback
def ws_get_panel_permissions(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict,
) -> None:
    """Return panel permissions for the current user.

    Returns dict of panel_id -> permission_level (0, 1, 2, 3)
    Level 0 = Deny (hidden)
    Level 1 = View (read-only)
    Level 2 = Limited (same as Edit in Phase 1)
    Level 3 = Edit (full access)
    """
    user_id = connection.user.id
    is_admin = connection.user.is_owner or (
        hasattr(connection.user, "groups")
        and any(g.id == "system-admin" for g in (connection.user.groups or []))
    )

    permissions: dict[str, int] = {}

    # Find all panel permission entities for this user
    # Entity IDs can be:
    # - select.perm_* (suggested object id format)
    # - select.permission_manager_* (has_entity_name format)
    all_select_entities = hass.states.async_all("select")
    perm_entities_found = 0
    matched_user = 0
    matched_panel = 0

    for entity in all_select_entities:
        entity_id = entity.entity_id
        if not (entity_id.startswith("select.perm_") or entity_id.startswith("select.permission_manager_")):
            continue

        perm_entities_found += 1
        attrs = entity.attributes

        # Debug: Log first few entities to see what attributes are available
        if perm_entities_found <= 3:
            _LOGGER.warning(
                "DEBUG: Entity %s attrs=%s",
                entity_id,
                dict(attrs) if attrs else "EMPTY"
            )

        entity_user_id = attrs.get("user_id")
        if entity_user_id != user_id:
            continue

        matched_user += 1

        if attrs.get("resource_type") != "panel":
            continue

        matched_panel += 1

        # Extract panel_id from resource_id (strip prefix)
        resource_id = attrs.get("resource_id", "")
        if resource_id.startswith(PREFIX_PANEL):
            panel_id = resource_id[len(PREFIX_PANEL):]
        else:
            panel_id = resource_id

        # Get permission level
        try:
            level = int(entity.state)
        except (ValueError, TypeError):
            level = 3  # Default to full access on error

        # Admin users always get level 3 for permission_manager panel
        if is_admin and panel_id == "ha_permission_manager":
            level = 3

        permissions[panel_id] = level

    _LOGGER.warning(
        "Panel permissions for user %s (is_admin=%s): found=%d, matched_user=%d, matched_panel=%d, permissions=%s",
        user_id,
        is_admin,
        perm_entities_found,
        matched_user,
        matched_panel,
        permissions,
    )

    # Return is_admin flag so frontend knows to skip filtering
    connection.send_result(msg["id"], {
        "permissions": permissions,
        "is_admin": is_admin,
        "user_id": user_id,
    })


@websocket_api.websocket_command(
    {
        vol.Required("type"): "permission_manager/get_all_permissions",
    }
)
@callback
def ws_get_all_permissions(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict,
) -> None:
    """Return all permissions for the current user.

    Returns dict with:
    - panels: dict of panel_id -> permission_level
    - areas: dict of area_id -> permission_level
    - labels: dict of label_id -> permission_level
    - is_admin: bool
    - user_id: str
    """
    user_id = connection.user.id
    is_admin = connection.user.is_owner or (
        hasattr(connection.user, "groups")
        and any(g.id == "system-admin" for g in (connection.user.groups or []))
    )

    panels: dict[str, int] = {}
    areas: dict[str, int] = {}
    labels: dict[str, int] = {}

    # Find all permission entities for this user
    # Entity IDs can be:
    # - select.perm_* (suggested object id format)
    # - select.permission_manager_* (has_entity_name format)
    for entity in hass.states.async_all("select"):
        entity_id = entity.entity_id
        if not (entity_id.startswith("select.perm_") or entity_id.startswith("select.permission_manager_")):
            continue

        attrs = entity.attributes
        if attrs.get("user_id") != user_id:
            continue

        resource_type = attrs.get("resource_type")
        resource_id = attrs.get("resource_id", "")

        # Get permission level
        try:
            level = int(entity.state)
        except (ValueError, TypeError):
            level = 3  # Default to full access on error

        if resource_type == "panel":
            if resource_id.startswith(PREFIX_PANEL):
                panel_id = resource_id[len(PREFIX_PANEL):]
            else:
                panel_id = resource_id
            panels[panel_id] = level

        elif resource_type == "area":
            if resource_id.startswith(PREFIX_AREA):
                area_id = resource_id[len(PREFIX_AREA):]
            else:
                area_id = resource_id
            areas[area_id] = level

        elif resource_type == "label":
            if resource_id.startswith(PREFIX_LABEL):
                label_id = resource_id[len(PREFIX_LABEL):]
            else:
                label_id = resource_id
            labels[label_id] = level

    _LOGGER.info(
        "All permissions for user %s (is_admin=%s): panels=%d, areas=%d, labels=%d",
        user_id, is_admin, len(panels), len(areas), len(labels),
    )

    connection.send_result(msg["id"], {
        "panels": panels,
        "areas": areas,
        "labels": labels,
        "is_admin": is_admin,
        "user_id": user_id,
    })
