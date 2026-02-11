"""WebSocket API for ha_permission_manager."""
from __future__ import annotations

import logging
import re
from typing import Any, TYPE_CHECKING

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import label_registry as lr

from .const import DOMAIN, PREFIX_PANEL, PREFIX_AREA, PREFIX_LABEL

if TYPE_CHECKING:
    from homeassistant.components.websocket_api import ActiveConnection

_LOGGER = logging.getLogger(__name__)

# Input validation pattern for IDs
VALID_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Permission levels (2-level model)
# Level 0 = Closed (hidden, no access)
# Level 1 = View (full access - can view and control)
PERM_CLOSED = 0
PERM_VIEW = 1

# Resource types
PERM_AREA_TYPE = "area"
PERM_LABEL_TYPE = "label"

# Permission entity prefix pattern
PERM_PREFIX = "select.permission_manager_"


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register WebSocket API handlers."""
    websocket_api.async_register_command(hass, ws_get_panel_permissions)
    websocket_api.async_register_command(hass, ws_get_all_permissions)
    # Area control handlers
    websocket_api.async_register_command(hass, websocket_get_permitted_areas)
    websocket_api.async_register_command(hass, websocket_get_area_entities)
    # Label control handlers
    websocket_api.async_register_command(hass, websocket_get_permitted_labels)
    websocket_api.async_register_command(hass, websocket_get_label_entities)


# =============================================================================
# Area Control WebSocket Handlers
# =============================================================================

async def get_user_permitted_areas(hass: HomeAssistant, user_id: str) -> list[dict]:
    """Get areas the user has permission to access."""
    permitted = []

    # Get all states for select entities
    states = hass.states.async_all("select")

    _LOGGER.debug("Checking permissions for user_id: %s", user_id)
    _LOGGER.debug("Looking for entities with prefix: %s", PERM_PREFIX)

    matching_count = 0
    for state in states:
        entity_id = state.entity_id
        # Pattern: select.perm_{user_slug}_{resource_type}_{resource_slug}
        if not entity_id.startswith(PERM_PREFIX):
            continue

        matching_count += 1
        attrs = state.attributes
        attr_user_id = attrs.get("user_id")
        attr_resource_type = attrs.get("resource_type")

        _LOGGER.debug(
            "Found entity %s: user_id=%s (match=%s), resource_type=%s (match=%s), state=%s",
            entity_id, attr_user_id, attr_user_id == user_id,
            attr_resource_type, attr_resource_type == PERM_AREA_TYPE, state.state
        )

        if attr_user_id != user_id:
            continue
        if attr_resource_type != PERM_AREA_TYPE:
            continue

        # Check permission level >= 1 (View)
        try:
            perm_level = int(state.state)
        except ValueError:
            continue

        if perm_level >= PERM_VIEW:
            # Extract area_id from resource_id (remove "area_" prefix)
            resource_id = attrs.get("resource_id", "")
            area_id = resource_id[5:] if resource_id.startswith("area_") else resource_id

            permitted.append({
                "id": area_id,
                "name": attrs.get("resource_name", area_id),
                "permission_level": perm_level,
            })
            _LOGGER.info("User %s has permission %d for area %s", user_id, perm_level, area_id)

    _LOGGER.debug("Total entities with prefix: %d, permitted areas: %d", matching_count, len(permitted))
    return permitted


async def get_entities_for_area(hass: HomeAssistant, area_id: str) -> dict[str, list[str]]:
    """Get entities grouped by domain for an area."""
    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)

    entities_by_domain: dict[str, list[str]] = {}

    for entry in entity_reg.entities.values():
        entity_area = entry.area_id

        # If entity doesn't have area, check device
        if not entity_area and entry.device_id:
            device = device_reg.async_get(entry.device_id)
            if device:
                entity_area = device.area_id

        if entity_area == area_id and not entry.disabled:
            domain = entry.entity_id.split(".")[0]
            if domain not in entities_by_domain:
                entities_by_domain[domain] = []
            entities_by_domain[domain].append(entry.entity_id)

    return entities_by_domain


@websocket_api.websocket_command({
    vol.Required("type"): "area_control/get_permitted_areas",
})
@websocket_api.async_response
async def websocket_get_permitted_areas(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Handle get permitted areas command."""
    user = connection.user

    if user is None:
        connection.send_error(msg["id"], "not_authenticated", "User not authenticated")
        return

    area_reg = ar.async_get(hass)
    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)

    # Pre-compute entity counts for all areas (O(n) instead of O(n*m))
    entity_counts: dict[str, int] = {}
    for entry in entity_reg.entities.values():
        if entry.disabled:
            continue
        entity_area = entry.area_id
        if not entity_area and entry.device_id:
            device = device_reg.async_get(entry.device_id)
            if device:
                entity_area = device.area_id
        if entity_area:
            entity_counts[entity_area] = entity_counts.get(entity_area, 0) + 1

    _LOGGER.info("get_permitted_areas called by user: %s (id=%s, is_admin=%s)", user.name, user.id, user.is_admin)

    # Admin users see all areas
    if user.is_admin:
        areas = []
        for area in area_reg.async_list_areas():
            areas.append({
                "id": area.id,
                "name": area.name,
                "icon": area.icon,
                "entity_count": entity_counts.get(area.id, 0),
                "permission_level": 1,  # Full access for admin
            })

        _LOGGER.info("Admin user %s gets all %d areas", user.name, len(areas))
        connection.send_result(msg["id"], {"areas": areas})
        return

    # Non-admin: check permissions
    permitted = await get_user_permitted_areas(hass, user.id)
    _LOGGER.info("Non-admin user %s (id=%s) has %d permitted areas", user.name, user.id, len(permitted))

    # Enrich with area details and entity count
    areas = []
    for perm in permitted:
        area = area_reg.async_get_area(perm["id"])
        if area:
            areas.append({
                "id": area.id,
                "name": area.name,
                "icon": area.icon,
                "entity_count": entity_counts.get(area.id, 0),
                "permission_level": perm["permission_level"],
            })

    connection.send_result(msg["id"], {"areas": areas})


@websocket_api.websocket_command({
    vol.Required("type"): "area_control/get_area_entities",
    vol.Required("area_id"): vol.All(str, vol.Length(min=1, max=255)),
})
@websocket_api.async_response
async def websocket_get_area_entities(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Handle get area entities command."""
    user = connection.user
    area_id = msg["area_id"]

    if user is None:
        connection.send_error(msg["id"], "not_authenticated", "User not authenticated")
        return

    # Validate area_id format
    if not VALID_ID_PATTERN.match(area_id):
        connection.send_error(msg["id"], "invalid_area_id", "Invalid area_id format")
        return

    # Verify permission (admin or has area permission)
    if not user.is_admin:
        permitted = await get_user_permitted_areas(hass, user.id)
        area_ids = [p["id"] for p in permitted]
        if area_id not in area_ids:
            connection.send_error(msg["id"], "forbidden", "No permission for this area")
            return

    entities_by_domain = await get_entities_for_area(hass, area_id)

    connection.send_result(msg["id"], {"entities": entities_by_domain})


# =============================================================================
# Label Control WebSocket Handlers
# =============================================================================

async def get_user_permitted_labels(hass: HomeAssistant, user_id: str) -> list[dict]:
    """Get labels the user has permission to access."""
    permitted = []

    # Get all states for select entities
    states = hass.states.async_all("select")

    for state in states:
        entity_id = state.entity_id
        # Pattern: select.perm_{user_slug}_label_{label_slug}
        if not entity_id.startswith(PERM_PREFIX):
            continue

        attrs = state.attributes
        if attrs.get("user_id") != user_id:
            continue
        if attrs.get("resource_type") != PERM_LABEL_TYPE:
            continue

        # Check permission level >= 1 (View)
        try:
            perm_level = int(state.state)
        except ValueError:
            _LOGGER.debug("Invalid permission level for %s: %s", entity_id, state.state)
            continue

        if perm_level >= PERM_VIEW:
            # Extract label_id from resource_id (remove "label_" prefix)
            resource_id = attrs.get("resource_id", "")
            label_id = resource_id[6:] if resource_id.startswith("label_") else resource_id

            permitted.append({
                "id": label_id,
                "name": attrs.get("resource_name", label_id),
                "permission_level": perm_level,
            })

    return permitted


async def get_entities_for_label(hass: HomeAssistant, label_id: str) -> dict[str, list[str]]:
    """Get entities grouped by domain for a label."""
    entity_reg = er.async_get(hass)

    entities_by_domain: dict[str, list[str]] = {}

    for entry in entity_reg.entities.values():
        # Check if entity has this label
        if label_id in (entry.labels or set()) and not entry.disabled:
            domain = entry.entity_id.split(".")[0]
            if domain not in entities_by_domain:
                entities_by_domain[domain] = []
            entities_by_domain[domain].append(entry.entity_id)

    return entities_by_domain


@websocket_api.websocket_command({
    vol.Required("type"): "label_control/get_permitted_labels",
})
@websocket_api.async_response
async def websocket_get_permitted_labels(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Handle get permitted labels command."""
    user = connection.user

    if user is None:
        connection.send_error(msg["id"], "not_authenticated", "User not authenticated")
        return

    label_reg = lr.async_get(hass)
    entity_reg = er.async_get(hass)

    # Pre-compute entity counts for all labels (O(n) instead of O(n*m))
    entity_counts: dict[str, int] = {}
    for entry in entity_reg.entities.values():
        if entry.disabled:
            continue
        for label_id in (entry.labels or set()):
            entity_counts[label_id] = entity_counts.get(label_id, 0) + 1

    # Admin users see all labels
    if user.is_admin:
        labels = []
        for label in label_reg.async_list_labels():
            labels.append({
                "id": label.label_id,
                "name": label.name,
                "icon": label.icon,
                "color": label.color,
                "entity_count": entity_counts.get(label.label_id, 0),
                "permission_level": 1,  # Full access for admin
            })

        connection.send_result(msg["id"], {"labels": labels})
        return

    # Non-admin: check permissions
    permitted = await get_user_permitted_labels(hass, user.id)

    # Enrich with label details and entity count
    labels = []
    for perm in permitted:
        label = label_reg.async_get_label(perm["id"])
        if label:
            labels.append({
                "id": label.label_id,
                "name": label.name,
                "icon": label.icon,
                "color": label.color,
                "entity_count": entity_counts.get(label.label_id, 0),
                "permission_level": perm["permission_level"],
            })

    connection.send_result(msg["id"], {"labels": labels})


@websocket_api.websocket_command({
    vol.Required("type"): "label_control/get_label_entities",
    vol.Required("label_id"): vol.All(str, vol.Length(min=1, max=255)),
})
@websocket_api.async_response
async def websocket_get_label_entities(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Handle get label entities command."""
    user = connection.user
    label_id = msg["label_id"]

    if user is None:
        connection.send_error(msg["id"], "not_authenticated", "User not authenticated")
        return

    # Validate label_id format
    if not VALID_ID_PATTERN.match(label_id):
        connection.send_error(msg["id"], "invalid_label_id", "Invalid label_id format")
        return

    # Verify permission (admin or has label permission)
    if not user.is_admin:
        permitted = await get_user_permitted_labels(hass, user.id)
        label_ids = [p["id"] for p in permitted]
        if label_id not in label_ids:
            connection.send_error(msg["id"], "forbidden", "No permission for this label")
            return

    entities_by_domain = await get_entities_for_label(hass, label_id)

    connection.send_result(msg["id"], {"entities": entities_by_domain})


# =============================================================================
# Permission Manager WebSocket Handlers
# =============================================================================

@websocket_api.websocket_command(
    {
        vol.Required("type"): "permission_manager/get_panel_permissions",
    }
)
@callback
def ws_get_panel_permissions(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return panel permissions for the current user.

    Returns dict of panel_id -> permission_level (0 or 1)
    Level 0 = Closed (hidden, no access)
    Level 1 = View (full access - can view and control)
    """
    user_id = connection.user.id
    is_admin = connection.user.is_admin

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

        # Validate user_id attribute
        entity_user_id = attrs.get("user_id")
        if not isinstance(entity_user_id, str) or not entity_user_id:
            continue
        if entity_user_id != user_id:
            continue

        matched_user += 1

        # Validate resource_type
        resource_type = attrs.get("resource_type")
        if resource_type not in ("panel", "area", "label"):
            continue
        if resource_type != "panel":
            continue

        matched_panel += 1

        # Extract panel_id from resource_id (strip prefix)
        resource_id = attrs.get("resource_id", "")
        if resource_id.startswith(PREFIX_PANEL):
            panel_id = resource_id[len(PREFIX_PANEL):]
        else:
            panel_id = resource_id

        # Get permission level - fail secure (default to no access)
        try:
            level = int(entity.state)
        except (ValueError, TypeError):
            level = 0  # Fail secure - no access
            _LOGGER.warning("Invalid permission level for entity %s, defaulting to CLOSED", entity_id)

        # Admin users always get level 1 (full access) for permission_manager panel
        if is_admin and panel_id == "ha_permission_manager":
            level = 1

        permissions[panel_id] = level

    _LOGGER.debug(
        "Panel permissions for user %s (is_admin=%s): found=%d, matched_user=%d, matched_panel=%d, permissions=%s",
        user_id,
        is_admin,
        perm_entities_found,
        matched_user,
        matched_panel,
        permissions,
    )

    # Return is_admin flag so frontend knows to skip filtering
    # Note: user_id intentionally not included for security
    connection.send_result(msg["id"], {
        "permissions": permissions,
        "is_admin": is_admin,
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
    msg: dict[str, Any],
) -> None:
    """Return all permissions for the current user.

    Returns dict with:
    - panels: dict of panel_id -> permission_level
    - areas: dict of area_id -> permission_level
    - labels: dict of label_id -> permission_level
    - is_admin: bool
    """
    user_id = connection.user.id
    is_admin = connection.user.is_admin

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

        # Validate user_id attribute
        entity_user_id = attrs.get("user_id")
        if not isinstance(entity_user_id, str) or not entity_user_id:
            continue
        if entity_user_id != user_id:
            continue

        resource_type = attrs.get("resource_type")
        # Validate resource_type
        if resource_type not in ("panel", "area", "label"):
            continue
        resource_id = attrs.get("resource_id", "")

        # Get permission level - fail secure (default to no access)
        try:
            level = int(entity.state)
        except (ValueError, TypeError):
            level = 0  # Fail secure - no access
            _LOGGER.warning("Invalid permission level for entity %s, defaulting to CLOSED", entity_id)

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

    # Note: user_id intentionally not included for security
    connection.send_result(msg["id"], {
        "panels": panels,
        "areas": areas,
        "labels": labels,
        "is_admin": is_admin,
    })
