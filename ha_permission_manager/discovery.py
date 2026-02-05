"""Resource discovery for ha_permission_manager."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import label_registry as lr

from .const import (
    PREFIX_AREA,
    PREFIX_AUTOMATION,
    PREFIX_CUSTOM,
    PREFIX_LABEL,
    PREFIX_PANEL,
    PREFIX_SCRIPT,
    SELF_PANEL_ID,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass
class Resource:
    """Represents a protectable resource."""
    id: str
    name: str
    type: str  # "area" | "label" | "automation" | "script" | "panel" | "custom"


def discover_areas(hass: HomeAssistant) -> list[Resource]:
    """Discover all areas."""
    registry = ar.async_get(hass)
    resources = []
    for area in registry.async_list_areas():
        resources.append(
            Resource(
                id=f"{PREFIX_AREA}{area.id}",
                name=area.name,
                type="area",
            )
        )
    _LOGGER.debug("Discovered %d areas", len(resources))
    return resources


def discover_labels(hass: HomeAssistant) -> list[Resource]:
    """Discover all labels."""
    registry = lr.async_get(hass)
    resources = []
    for label in registry.async_list_labels():
        resources.append(
            Resource(
                id=f"{PREFIX_LABEL}{label.label_id}",
                name=label.name,
                type="label",
            )
        )
    _LOGGER.debug("Discovered %d labels", len(resources))
    return resources


def discover_automations(hass: HomeAssistant) -> list[Resource]:
    """Discover all automations."""
    resources = []
    # Get automations from state machine
    for state in hass.states.async_all("automation"):
        entity_id = state.entity_id
        name = state.attributes.get("friendly_name") or entity_id.split(".")[-1]
        automation_id = entity_id.replace("automation.", "")
        resources.append(
            Resource(
                id=f"{PREFIX_AUTOMATION}{automation_id}",
                name=name,
                type="automation",
            )
        )
    _LOGGER.debug("Discovered %d automations", len(resources))
    return resources


def discover_scripts(hass: HomeAssistant) -> list[Resource]:
    """Discover all scripts."""
    resources = []
    # Get scripts from state machine
    for state in hass.states.async_all("script"):
        entity_id = state.entity_id
        name = state.attributes.get("friendly_name") or entity_id.split(".")[-1]
        script_id = entity_id.replace("script.", "")
        resources.append(
            Resource(
                id=f"{PREFIX_SCRIPT}{script_id}",
                name=name,
                type="script",
            )
        )
    _LOGGER.debug("Discovered %d scripts", len(resources))
    return resources


def discover_custom(hass: HomeAssistant) -> list[Resource]:
    """Discover custom resources from config."""
    resources = []
    # Get custom resources from hass.data if configured
    custom_resources = hass.data.get("ha_permission_manager", {}).get("custom_resources", [])
    for item in custom_resources:
        # Validate required keys exist
        if not isinstance(item, dict):
            _LOGGER.warning("Skipping invalid custom resource (not a dict): %s", item)
            continue
        if "id" not in item or "name" not in item:
            _LOGGER.warning("Skipping custom resource missing 'id' or 'name': %s", item)
            continue
        resources.append(
            Resource(
                id=f"{PREFIX_CUSTOM}{item['id']}",
                name=item["name"],
                type="custom",
            )
        )
    _LOGGER.debug("Discovered %d custom resources", len(resources))
    return resources


def discover_panels(hass: HomeAssistant) -> list[Resource]:
    """Discover all sidebar panels."""
    resources = []

    # Try multiple locations where panels might be stored
    panels = {}

    # Method 1: frontend_panels (modern HA)
    if "frontend_panels" in hass.data:
        panels = hass.data["frontend_panels"]
    # Method 2: frontend -> panels
    elif "frontend" in hass.data:
        frontend_data = hass.data["frontend"]
        if isinstance(frontend_data, dict):
            panels = frontend_data.get("panels", {})
        elif hasattr(frontend_data, "panels"):
            panels = frontend_data.panels or {}

    _LOGGER.debug("Found panels data: %s", list(panels.keys()) if panels else "None")

    for panel_id, panel in panels.items():
        # Skip our own panel (we'll add it manually)
        if panel_id == "ha_permission_manager":
            continue

        # Get panel title
        title = panel_id
        if isinstance(panel, dict):
            title = panel.get("title") or panel.get("sidebar_title") or panel_id
        elif hasattr(panel, "title"):
            title = panel.title or panel_id
        elif hasattr(panel, "sidebar_title"):
            title = panel.sidebar_title or panel_id

        resources.append(
            Resource(
                id=f"{PREFIX_PANEL}{panel_id}",
                name=str(title),
                type="panel",
            )
        )

    # Always add self-reference
    resources.append(
        Resource(
            id=SELF_PANEL_ID,
            name="Permission Manager",
            type="panel",
        )
    )

    _LOGGER.debug("Discovered %d panels (including self)", len(resources))
    return resources


def discover_all_resources(hass: HomeAssistant) -> dict[str, list[Resource]]:
    """Discover all protectable resources grouped by type."""
    return {
        "areas": discover_areas(hass),
        "labels": discover_labels(hass),
        "automations": discover_automations(hass),
        "scripts": discover_scripts(hass),
        "panels": discover_panels(hass),
        "custom": discover_custom(hass),
    }
