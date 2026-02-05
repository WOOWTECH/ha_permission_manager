"""Select platform for ha_permission_manager."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

if TYPE_CHECKING:
    from homeassistant.auth.models import User as HAUser

from .const import (
    ADMIN_GROUP_ID,
    DOMAIN,
    PERMISSION_LABELS,
    PERMISSION_OPTIONS,
    SELF_PANEL_ID,
    build_unique_id,
    sanitize_slug,
)
from .discovery import Resource, discover_all_resources
from .users import User, discover_users, get_admin_user_ids

_LOGGER = logging.getLogger(__name__)

# Lock for thread-safe entity registration to prevent race conditions
_entity_registration_lock = asyncio.Lock()


# Core panels that are always protected (full access) for all users
ALWAYS_PROTECTED_PANELS = [
    "panel_profile",  # User profile - needed for logout
]


def is_protected_permission(user_id: str, resource_id: str, admin_ids: set[str]) -> bool:
    """Check if a user-resource permission is protected.

    Protected permissions cannot be changed:
    1. Admin users have full edit permission for ALL resources
    2. Core panels (like profile) are always protected for all users
    """
    # Admin users: all permissions are protected
    if user_id in admin_ids:
        return True

    # Core panels are protected for all users
    if resource_id in ALWAYS_PROTECTED_PANELS:
        return True

    return False


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up permission select entities."""
    # Store callback in hass.data for multi-instance safety
    hass.data[DOMAIN]["async_add_entities"] = async_add_entities

    # Discover users and resources
    users = await discover_users(hass)
    resources = discover_all_resources(hass)
    admin_ids = get_admin_user_ids(users)

    # Store users for later use
    hass.data[DOMAIN]["users"] = users

    # Flatten resources
    all_resources: list[Resource] = []
    for resource_list in resources.values():
        all_resources.extend(resource_list)

    # Store resources for later use
    hass.data[DOMAIN]["resources"] = all_resources

    # Create entities for each user × resource combination
    entities: list[PermissionSelectEntity] = []
    for user in users:
        for resource in all_resources:
            is_protected = is_protected_permission(user.id, resource.id, admin_ids)

            entity = PermissionSelectEntity(
                user=user,
                resource=resource,
                is_protected=is_protected,
            )
            entities.append(entity)

            # Store entity reference
            hass.data[DOMAIN]["entities"][entity._attr_unique_id] = entity

    _LOGGER.info(
        "Creating %d permission entities (%d users × %d resources)",
        len(entities),
        len(users),
        len(all_resources),
    )

    async_add_entities(entities)


async def async_add_entities_for_resource(
    hass: HomeAssistant,
    resource_id: str,
    resource_name: str,
    resource_type: str,
) -> None:
    """Add permission entities for a new resource (for all users)."""
    async with _entity_registration_lock:
        domain_data = hass.data.get(DOMAIN, {})
        callback = domain_data.get("async_add_entities")
        if callback is None:
            _LOGGER.warning("Cannot add entities: async_add_entities callback not available")
            return

        # Check for duplicate resource
        existing_ids = {r.id for r in domain_data.get("resources", [])}
        if resource_id in existing_ids:
            _LOGGER.debug("Resource %s already exists, skipping", resource_id)
            return

        users = domain_data.get("users", [])
        admin_ids = get_admin_user_ids(users)

        resource = Resource(id=resource_id, name=resource_name, type=resource_type)

        # Add to stored resources
        domain_data.setdefault("resources", []).append(resource)

        entities: list[PermissionSelectEntity] = []
        for user in users:
            is_protected = is_protected_permission(user.id, resource_id, admin_ids)

            entity = PermissionSelectEntity(
                user=user,
                resource=resource,
                is_protected=is_protected,
            )
            entities.append(entity)

            # Store entity reference
            domain_data["entities"][entity._attr_unique_id] = entity

        if entities:
            _LOGGER.info(
                "Adding %d permission entities for new resource: %s",
                len(entities),
                resource_name,
            )
            callback(entities)


async def async_remove_entities_for_resource(
    hass: HomeAssistant,
    resource_id: str,
) -> None:
    """Remove all permission entities for a deleted resource."""
    domain_data = hass.data.get(DOMAIN, {})
    entity_registry = er.async_get(hass)
    entities_to_remove = []

    # Find all entities for this resource
    for unique_id, entity in list(domain_data.get("entities", {}).items()):
        if entity._resource.id == resource_id:
            entities_to_remove.append((unique_id, entity))

    for unique_id, entity in entities_to_remove:
        # Remove from entity registry
        entity_entry = entity_registry.async_get(entity.entity_id)
        if entity_entry:
            entity_registry.async_remove(entity.entity_id)
            _LOGGER.debug("Removed entity: %s", entity.entity_id)

        # Remove from stored entities
        domain_data.get("entities", {}).pop(unique_id, None)

    # Remove from stored resources
    resources = domain_data.get("resources", [])
    domain_data["resources"] = [r for r in resources if r.id != resource_id]

    if entities_to_remove:
        _LOGGER.info(
            "Removed %d permission entities for deleted resource: %s",
            len(entities_to_remove),
            resource_id,
        )


async def async_add_entities_for_user(
    hass: HomeAssistant,
    ha_user: HAUser,
) -> None:
    """Add permission entities for a new user (for all resources)."""
    async with _entity_registration_lock:
        domain_data = hass.data.get(DOMAIN, {})
        callback = domain_data.get("async_add_entities")
        if callback is None:
            _LOGGER.warning("Cannot add entities: async_add_entities callback not available")
            return

        # Check for duplicate user
        existing_ids = {u.id for u in domain_data.get("users", [])}
        if ha_user.id in existing_ids:
            _LOGGER.debug("User %s already exists, skipping", ha_user.id)
            return

        # Check if admin
        is_admin = any(
            group.id == ADMIN_GROUP_ID
            for group in (ha_user.groups or [])
        )

        user = User(
            id=ha_user.id,
            name=ha_user.name or "Unknown",
            is_admin=is_admin,
        )

        # Add to stored users
        domain_data.setdefault("users", []).append(user)

        resources = domain_data.get("resources", [])
        admin_ids = get_admin_user_ids(domain_data.get("users", []))

        entities: list[PermissionSelectEntity] = []
        for resource in resources:
            is_protected = is_protected_permission(user.id, resource.id, admin_ids)

            entity = PermissionSelectEntity(
                user=user,
                resource=resource,
                is_protected=is_protected,
            )
            entities.append(entity)

            # Store entity reference
            domain_data["entities"][entity._attr_unique_id] = entity

        if entities:
            _LOGGER.info(
                "Adding %d permission entities for new user: %s",
                len(entities),
                user.name,
            )
            callback(entities)


async def async_remove_entities_for_user(
    hass: HomeAssistant,
    user_id: str,
) -> None:
    """Remove all permission entities for a deleted user."""
    domain_data = hass.data.get(DOMAIN, {})
    entity_registry = er.async_get(hass)
    entities_to_remove = []

    # Find all entities for this user
    for unique_id, entity in list(domain_data.get("entities", {}).items()):
        if entity._user.id == user_id:
            entities_to_remove.append((unique_id, entity))

    for unique_id, entity in entities_to_remove:
        # Remove from entity registry
        entity_entry = entity_registry.async_get(entity.entity_id)
        if entity_entry:
            entity_registry.async_remove(entity.entity_id)
            _LOGGER.debug("Removed entity: %s", entity.entity_id)

        # Remove from stored entities
        domain_data.get("entities", {}).pop(unique_id, None)

    # Remove from stored users
    users = domain_data.get("users", [])
    domain_data["users"] = [u for u in users if u.id != user_id]

    if entities_to_remove:
        _LOGGER.info(
            "Removed %d permission entities for deleted user: %s",
            len(entities_to_remove),
            user_id,
        )


async def async_update_user_info(
    hass: HomeAssistant,
    user_id: str,
    new_name: str | None = None,
    new_is_admin: bool | None = None,
) -> None:
    """Update user info (name and/or admin status) for a user and all their permission entities.

    When a user's admin status changes in HA:
    - If promoted to admin: all permissions become protected (locked at "3")
    - If demoted from admin: permissions become editable and reset to "0" (Closed)

    When a user's name changes:
    - Update the name in all permission entities
    """
    domain_data = hass.data.get(DOMAIN, {})
    users = domain_data.get("users", [])
    entities = domain_data.get("entities", {})

    # Find and update the user
    user_found = False
    old_is_admin = None
    old_name = None
    admin_changed = False
    name_changed = False

    for user in users:
        if user.id == user_id:
            old_is_admin = user.is_admin
            old_name = user.name

            # Update admin status if provided
            if new_is_admin is not None and old_is_admin != new_is_admin:
                user.is_admin = new_is_admin
                admin_changed = True
                _LOGGER.info(
                    "User %s (%s) admin status changed: %s -> %s",
                    user.name, user_id, old_is_admin, new_is_admin
                )

            # Update name if provided
            if new_name is not None and old_name != new_name:
                user.name = new_name
                name_changed = True
                _LOGGER.info(
                    "User %s name changed: %s -> %s",
                    user_id, old_name, new_name
                )

            user_found = True
            break

    if not user_found:
        _LOGGER.warning("User %s not found in permission manager", user_id)
        return

    if not admin_changed and not name_changed:
        _LOGGER.debug("User %s info unchanged", user_id)
        return

    # Recalculate admin_ids
    admin_ids = get_admin_user_ids(users)

    # Update all entities for this user
    updated_count = 0
    for unique_id, entity in entities.items():
        if entity._user.id != user_id:
            continue

        needs_update = False

        # Update user name if changed
        if name_changed and new_name:
            entity._user.name = new_name
            # Update entity display name
            entity._attr_name = f"{new_name} - {entity._resource.name}"
            needs_update = True

        # Update admin status if changed
        if admin_changed and new_is_admin is not None:
            entity._user.is_admin = new_is_admin

            # Update protected status
            new_is_protected = is_protected_permission(user_id, entity._resource.id, admin_ids)
            old_is_protected = entity._is_protected

            if old_is_protected != new_is_protected:
                entity._is_protected = new_is_protected

                if new_is_protected:
                    # Promoted to admin: lock at "3" (Edit)
                    entity._attr_current_option = "3"
                else:
                    # Demoted from admin: set default permissions
                    # Only profile panel needs access (for logout), all others closed
                    resource_id = entity._resource.id
                    if resource_id == "panel_profile":
                        entity._attr_current_option = "3"  # Edit access for profile
                    else:
                        entity._attr_current_option = "0"  # Closed

                needs_update = True

        if needs_update:
            # Write state to trigger UI update
            entity.async_write_ha_state()
            updated_count += 1
            _LOGGER.debug(
                "Updated entity %s: name=%s, is_protected=%s, option=%s",
                entity.entity_id, entity._attr_name, entity._is_protected, entity._attr_current_option
            )

    _LOGGER.info(
        "Updated %d permission entities for user %s (name=%s, admin=%s)",
        updated_count, user_id, new_name if name_changed else "(unchanged)",
        new_is_admin if admin_changed else "(unchanged)"
    )


# Keep backward compatibility alias
async def async_update_user_admin_status(
    hass: HomeAssistant,
    user_id: str,
    new_is_admin: bool,
) -> None:
    """Update admin status for a user. Wrapper for async_update_user_info."""
    await async_update_user_info(hass, user_id, new_is_admin=new_is_admin)


class PermissionSelectEntity(SelectEntity, RestoreEntity):
    """A select entity representing one user-resource permission."""

    _attr_has_entity_name = True
    _attr_options = PERMISSION_OPTIONS
    _attr_icon = "mdi:shield-account"

    def __init__(
        self,
        user: User,
        resource: Resource,
        is_protected: bool,
    ) -> None:
        """Initialize the permission select entity."""
        self._user = user
        self._resource = resource
        self._is_protected = is_protected
        self._attr_current_option = "3" if is_protected else "0"

        # Build IDs
        self._attr_unique_id = build_unique_id(
            user.id, resource.type, resource.id
        )
        # Use suggested_object_id for HA to generate entity_id with this base
        # This is safer than directly setting entity_id as it lets HA handle conflicts
        user_slug = sanitize_slug(user.name)
        resource_slug = sanitize_slug(resource.name)
        self._attr_suggested_object_id = f"perm_{user_slug}_{resource.type}_{resource_slug}"

        # Display name
        self._attr_name = f"{user.name} - {resource.name}"

        # Device info - groups all entities under one device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            name="Permission Manager",
            manufacturer="Custom",
            model="Permission Matrix",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "user_id": self._user.id,
            "user_name": self._user.name,
            "resource_id": self._resource.id,
            "resource_name": self._resource.name,
            "resource_type": self._resource.type,
            "permission_label": PERMISSION_LABELS.get(
                self._attr_current_option, "Unknown"
            ),
            "is_admin": self._user.is_admin,
            "is_protected": self._is_protected,
        }

    async def async_added_to_hass(self) -> None:
        """Restore previous state when added to hass."""
        await super().async_added_to_hass()

        # Try to restore previous state
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in PERMISSION_OPTIONS:
            if self._is_protected:
                # Protected entities always stay at "3"
                self._attr_current_option = "3"
            else:
                self._attr_current_option = last_state.state
            _LOGGER.debug(
                "Restored %s to %s",
                self.entity_id,
                self._attr_current_option
            )

        # Critical: Write state to ensure attributes are available in state machine
        # Without this, hass.states.async_all() returns entities without attributes
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Handle option selection."""
        if self._is_protected:
            _LOGGER.warning(
                "Cannot modify protected permission: %s",
                self.entity_id
            )
            return

        if option not in PERMISSION_OPTIONS:
            _LOGGER.error("Invalid permission option: %s", option)
            return

        self._attr_current_option = option
        self.async_write_ha_state()
        _LOGGER.debug(
            "Permission changed: %s = %s (%s)",
            self.entity_id,
            option,
            PERMISSION_LABELS.get(option, "Unknown"),
        )
