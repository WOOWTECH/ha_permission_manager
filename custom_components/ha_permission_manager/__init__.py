"""The ha_permission_manager integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.frontend import (
    add_extra_js_url,
    async_register_built_in_panel,
    async_remove_panel,
)
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import DOMAIN as PANEL_CUSTOM_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import label_registry as lr

from .const import (
    DOMAIN,
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_TITLE_ZH,
    PANEL_URL,
    PANEL_VERSION,
    PREFIX_AREA,
    PREFIX_LABEL,
    PREFIX_PANEL,
)
from .websocket_api import async_register_websocket_api

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["select"]


def _get_panel_title(hass: HomeAssistant) -> str:
    """Get panel title based on HA language setting."""
    language = hass.config.language or "en"
    if language.startswith("zh"):
        return PANEL_TITLE_ZH
    return PANEL_TITLE

# Key for frontend panels storage (internal HA structure)
_FRONTEND_PANELS_KEY = "frontend_panels"


def _get_frontend_panels(hass: HomeAssistant) -> dict[str, Any]:
    """Get frontend panels using available API.

    Note: This accesses hass.data["frontend_panels"] which is an internal API.
    We wrap it in a helper function to centralize the access point and make
    it easier to update if HA provides a public API in the future.
    """
    return hass.data.get(_FRONTEND_PANELS_KEY, {})


# Event types
EVENT_AREA_REGISTRY_UPDATED = "area_registry_updated"
EVENT_LABEL_REGISTRY_UPDATED = "label_registry_updated"
EVENT_USER_ADDED = "user_added"
EVENT_USER_REMOVED = "user_removed"
EVENT_USER_UPDATED = "user_updated"
EVENT_LOVELACE_UPDATED = "lovelace_updated"
EVENT_PANELS_UPDATED = "panels_updated"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Permission Manager from a config entry."""
    _LOGGER.info("Setting up ha_permission_manager v2.9.1")

    # Initialize data storage
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["entry"] = entry
    hass.data[DOMAIN]["entities"] = {}
    hass.data[DOMAIN]["unsubscribe"] = []

    # Register WebSocket API
    async_register_websocket_api(hass)

    # Register the sidebar panel
    await _async_register_panel(hass)

    # Forward to select platform to create entities
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up event listeners for auto-refresh
    await _async_setup_listeners(hass)

    _LOGGER.info("ha_permission_manager setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading ha_permission_manager")

    # Unsubscribe from all event listeners (with safety check)
    domain_data = hass.data.get(DOMAIN, {})
    for unsub in domain_data.get("unsubscribe", []):
        unsub()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Remove panel
        async_remove_panel(hass, PANEL_URL)

        # Clean up stored data
        hass.data.pop(DOMAIN, None)

    return unload_ok


async def _async_setup_listeners(hass: HomeAssistant) -> None:
    """Set up event listeners for registry changes."""
    from .select import (
        async_add_entities_for_resource,
        async_remove_entities_for_resource,
        async_add_entities_for_user,
        async_remove_entities_for_user,
        async_update_user_info,
    )
    from .const import ADMIN_GROUP_ID

    async def _handle_area_registry_update(event: Event) -> None:
        """Handle area registry changes."""
        try:
            action = event.data.get("action")
            area_id = event.data.get("area_id")

            _LOGGER.debug("Area registry update: action=%s, area_id=%s", action, area_id)

            if action == "create":
                # Get area info
                registry = ar.async_get(hass)
                area = registry.async_get_area(area_id)
                if area:
                    resource_id = f"{PREFIX_AREA}{area_id}"
                    await async_add_entities_for_resource(
                        hass, resource_id, area.name, "area"
                    )
            elif action == "remove":
                resource_id = f"{PREFIX_AREA}{area_id}"
                await async_remove_entities_for_resource(hass, resource_id)
        except Exception as err:
            _LOGGER.error("Error handling area registry update: %s", err)

    async def _handle_label_registry_update(event: Event) -> None:
        """Handle label registry changes."""
        try:
            action = event.data.get("action")
            label_id = event.data.get("label_id")

            _LOGGER.debug("Label registry update: action=%s, label_id=%s", action, label_id)

            if action == "create":
                # Get label info
                registry = lr.async_get(hass)
                label = registry.async_get_label(label_id)
                if label:
                    resource_id = f"{PREFIX_LABEL}{label_id}"
                    await async_add_entities_for_resource(
                        hass, resource_id, label.name, "label"
                    )
            elif action == "remove":
                resource_id = f"{PREFIX_LABEL}{label_id}"
                await async_remove_entities_for_resource(hass, resource_id)
        except Exception as err:
            _LOGGER.error("Error handling label registry update: %s", err)

    async def _handle_user_added(event: Event) -> None:
        """Handle new user added."""
        try:
            user_id = event.data.get("user_id")
            _LOGGER.debug("User added: user_id=%s", user_id)

            if user_id:
                # Get user info from auth
                user = await hass.auth.async_get_user(user_id)
                if user and not user.system_generated:
                    await async_add_entities_for_user(hass, user)
        except Exception as err:
            _LOGGER.error("Error handling user added event: %s", err)

    async def _handle_user_removed(event: Event) -> None:
        """Handle user removed."""
        try:
            user_id = event.data.get("user_id")
            _LOGGER.debug("User removed: user_id=%s", user_id)

            if user_id:
                await async_remove_entities_for_user(hass, user_id)
        except Exception as err:
            _LOGGER.error("Error handling user removed event: %s", err)

    async def _handle_user_updated(event: Event) -> None:
        """Handle user updated (including admin status and name changes)."""
        try:
            user_id = event.data.get("user_id")
            _LOGGER.info("User updated event: user_id=%s, data=%s", user_id, event.data)

            if user_id:
                # Get current user info from auth
                user = await hass.auth.async_get_user(user_id)
                if user and not user.system_generated:
                    # Check if user is now admin
                    is_admin = any(
                        group.id == ADMIN_GROUP_ID
                        for group in (user.groups or [])
                    )
                    # Get user name
                    user_name = user.name or "Unknown"

                    _LOGGER.info(
                        "User %s (%s) current info: name=%s, admin=%s",
                        user_name, user_id, user_name, is_admin
                    )

                    # Update permission entities (both name and admin status)
                    await async_update_user_info(hass, user_id, new_name=user_name, new_is_admin=is_admin)
        except Exception as err:
            _LOGGER.error("Error handling user updated event: %s", err)

    async def _handle_lovelace_updated(event: Event) -> None:
        """Handle lovelace dashboard changes (create/delete)."""
        try:
            action = event.data.get("action")
            url_path = event.data.get("url_path")

            _LOGGER.info("Lovelace updated: action=%s, url_path=%s, data=%s", action, url_path, event.data)

            if not url_path:
                _LOGGER.debug("No url_path in lovelace_updated event, skipping")
                return

            if action == "create":
                # Get dashboard title from event data
                title = event.data.get("title") or url_path
                resource_id = f"{PREFIX_PANEL}{url_path}"
                await async_add_entities_for_resource(
                    hass, resource_id, title, "panel"
                )
                _LOGGER.info("Added permission entities for new dashboard: %s (%s)", title, url_path)

            elif action == "delete":
                resource_id = f"{PREFIX_PANEL}{url_path}"
                await async_remove_entities_for_resource(hass, resource_id)
                _LOGGER.info("Removed permission entities for deleted dashboard: %s", url_path)

        except Exception as err:
            _LOGGER.error("Error handling lovelace updated event: %s", err)

    async def _handle_panels_updated(event: Event) -> None:
        """Handle panel registry changes - sync new/deleted panels."""
        try:
            _LOGGER.info("Panels updated event received")

            # Get current panels from HA using public API
            current_panels = _get_frontend_panels(hass)
            if not current_panels:
                _LOGGER.debug("No frontend_panels data found")
                return

            # Get stored resources (panels only)
            domain_data = hass.data.get(DOMAIN, {})
            stored_resources = domain_data.get("resources", [])
            stored_panel_ids = {
                r.id for r in stored_resources if r.type == "panel"
            }

            # Build set of current panel IDs (with prefix)
            current_panel_ids = set()
            for panel_id, panel in current_panels.items():
                # Skip our own panel
                if panel_id == "ha_permission_manager":
                    continue
                resource_id = f"{PREFIX_PANEL}{panel_id}"
                current_panel_ids.add(resource_id)

            # Find new panels (in current but not in stored)
            new_panel_ids = current_panel_ids - stored_panel_ids
            for resource_id in new_panel_ids:
                panel_id = resource_id[len(PREFIX_PANEL):]
                panel = current_panels.get(panel_id)
                if panel:
                    # Get panel title
                    title = panel_id
                    if isinstance(panel, dict):
                        title = panel.get("title") or panel.get("sidebar_title") or panel_id
                    elif hasattr(panel, "title"):
                        title = panel.title or panel_id
                    elif hasattr(panel, "sidebar_title"):
                        title = panel.sidebar_title or panel_id

                    await async_add_entities_for_resource(
                        hass, resource_id, str(title), "panel"
                    )
                    _LOGGER.info("Added permission entities for new panel: %s (%s)", title, panel_id)

            # Find deleted panels (in stored but not in current)
            # Note: We need to exclude our own panel from deletion check
            self_panel_id = f"{PREFIX_PANEL}ha_permission_manager"
            deleted_panel_ids = stored_panel_ids - current_panel_ids - {self_panel_id}
            for resource_id in deleted_panel_ids:
                await async_remove_entities_for_resource(hass, resource_id)
                _LOGGER.info("Removed permission entities for deleted panel: %s", resource_id)

        except Exception as err:
            _LOGGER.error("Error handling panels updated event: %s", err)

    # Subscribe to events
    unsub_area = hass.bus.async_listen(
        EVENT_AREA_REGISTRY_UPDATED, _handle_area_registry_update
    )
    unsub_label = hass.bus.async_listen(
        EVENT_LABEL_REGISTRY_UPDATED, _handle_label_registry_update
    )
    unsub_user_added = hass.bus.async_listen(
        EVENT_USER_ADDED, _handle_user_added
    )
    unsub_user_removed = hass.bus.async_listen(
        EVENT_USER_REMOVED, _handle_user_removed
    )
    unsub_user_updated = hass.bus.async_listen(
        EVENT_USER_UPDATED, _handle_user_updated
    )
    unsub_lovelace = hass.bus.async_listen(
        EVENT_LOVELACE_UPDATED, _handle_lovelace_updated
    )
    unsub_panels = hass.bus.async_listen(
        EVENT_PANELS_UPDATED, _handle_panels_updated
    )

    # Store unsubscribe functions
    hass.data[DOMAIN]["unsubscribe"].extend([
        unsub_area,
        unsub_label,
        unsub_user_added,
        unsub_user_removed,
        unsub_user_updated,
        unsub_lovelace,
        unsub_panels,
    ])

    _LOGGER.debug("Event listeners registered for area, label, user, lovelace, panels")


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the frontend panel."""
    # Register static path for JS files (skip if already registered)
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                "/local/ha_permission_manager.js",
                hass.config.path(
                    "custom_components/ha_permission_manager/www/ha_permission_manager.js"
                ),
                False,
            ),
            StaticPathConfig(
                "/local/ha_sidebar_filter.js",
                hass.config.path(
                    "custom_components/ha_permission_manager/www/ha_sidebar_filter.js"
                ),
                False,
            ),
            StaticPathConfig(
                "/local/ha_access_denied.js",
                hass.config.path(
                    "custom_components/ha_permission_manager/www/ha_access_denied.js"
                ),
                False,
            ),
            StaticPathConfig(
                "/local/ha_lovelace_filter.js",
                hass.config.path(
                    "custom_components/ha_permission_manager/www/ha_lovelace_filter.js"
                ),
                False,
            ),
        ])
    except RuntimeError:
        # Path already registered from previous load
        _LOGGER.debug("Static path already registered, skipping")

    # Register the panel using the built-in panel API
    # Only register if not already registered
    if PANEL_URL not in _get_frontend_panels(hass):
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=_get_panel_title(hass),
            sidebar_icon=PANEL_ICON,
            frontend_url_path=PANEL_URL,
            config={
                "_panel_custom": {
                    "name": "ha-permission-manager",
                    "module_url": f"/local/ha_permission_manager.js?v={PANEL_VERSION}",
                }
            },
            require_admin=True,
        )

    # Register sidebar filter as extra JS (runs on every page)
    # Use version query param for cache busting
    add_extra_js_url(hass, "/local/ha_sidebar_filter.js?v=2.9.1")

    _LOGGER.debug("Frontend panel registered")
