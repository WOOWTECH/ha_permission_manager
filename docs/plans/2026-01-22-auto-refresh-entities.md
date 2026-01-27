# PRD: Auto-Refresh Permission Entities on Registry Changes

**Version:** 1.0
**Date:** 2026-01-22
**Status:** Approved

## Problem Statement

Currently, permission entities are only created at integration startup via `async_setup_entry()`. When users add or remove areas, labels, or HA users after setup, the permission matrix becomes out of sync:
- New areas/labels have no permission entities
- Deleted areas/labels leave orphaned entities
- New users have no permission entries
- Manual integration reload required to sync

## Solution

Listen to Home Assistant registry events and automatically:
- **Create** permission entities when areas, labels, or users are added
- **Delete** permission entities when areas, labels, or users are removed

## Scope

- Subscribe to `area_registry`, `label_registry`, and auth user events
- Auto-create entities for new resources × all users
- Auto-create entities for new users × all resources
- Auto-delete entities when resources or users are removed
- Remove any manual reload mechanism (fully automatic)

---

## Backend Architecture

### Event Listeners

The integration will subscribe to three event sources in `__init__.py`:

**1. Area Registry Events**
- `EVENT_AREA_REGISTRY_UPDATED` - fired when areas are created, updated, or deleted
- Action: `created` → add entities, `removed` → delete entities

**2. Label Registry Events**
- `EVENT_LABEL_REGISTRY_UPDATED` - fired when labels are created, updated, or deleted
- Action: `created` → add entities, `removed` → delete entities

**3. User Events**
- Listen via `hass.bus.async_listen` to auth events
- New user → create entities for all resources
- User deleted → remove all their permission entities

### Data Storage

Store references in `hass.data[DOMAIN]`:
```python
hass.data[DOMAIN] = {
    "config_entry": config_entry,
    "entities": {},  # unique_id -> entity mapping
    "users": [],     # cached user list
    "unsubscribe": [],  # event listener cleanup functions
}
```

### Entity Management

- Use `async_add_entities()` for new entities
- Use `entity_registry.async_remove()` for deleted entities
- Track entities by `unique_id` for efficient lookup

---

## Implementation Details

### Files Modified

#### `__init__.py`
- Add event listener setup in `async_setup_entry()`
- Store listeners in `hass.data[DOMAIN]["unsubscribe"]`
- Clean up listeners in `async_unload_entry()`

#### `select.py`
- Add `async_add_entities_for_resource()` function for dynamic entity creation
- Add `async_remove_entities_for_resource()` function for entity deletion
- Store `async_add_entities` callback for later use

### Event Handlers

```python
async def _handle_area_registry_update(event):
    """Handle area registry changes."""
    action = event.data.get("action")
    area_id = event.data.get("area_id")

    if action == "create":
        # Create permission entities for new area × all users
        await async_add_entities_for_resource(area_id, "area")
    elif action == "remove":
        # Remove all permission entities for this area
        await async_remove_entities_for_resource(area_id, "area")

async def _handle_label_registry_update(event):
    # Same pattern as area handler

async def _handle_user_update(event):
    # Create/remove entities for user × all resources
```

### Cleanup on Unload

```python
async def async_unload_entry(hass, config_entry):
    # Unsubscribe from all event listeners
    for unsub in hass.data[DOMAIN]["unsubscribe"]:
        unsub()
```

---

## Testing & Validation

### Manual Testing Checklist

1. **Add area** - Verify permission entities created for all users
2. **Delete area** - Verify permission entities removed for all users
3. **Add label** - Verify permission entities created for all users
4. **Delete label** - Verify permission entities removed for all users
5. **Add user** - Verify permission entities created for all resources
6. **Delete user** - Verify permission entities removed
7. **Restart HA** - Verify listeners re-attach and sync works
8. **Frontend** - Verify UI updates automatically (hass state changes trigger re-render)

### Edge Cases

- **Rapid changes** - Multiple areas added/deleted quickly should handle gracefully
- **Integration reload** - Listeners should be cleaned up and re-attached
- **HA restart** - Initial sync should handle any changes made while offline

### Rollback

If issues arise, revert changes to `__init__.py` and `select.py`. The integration will fall back to startup-only entity creation.

---

## Summary

| File | Changes |
|------|---------|
| `__init__.py` | Add event listeners for area, label, and user registry updates; store in `hass.data[DOMAIN]`; cleanup on unload |
| `select.py` | Add `async_add_entities_for_resource()`, `async_remove_entities_for_resource()`, `async_add_entities_for_user()`, `async_remove_entities_for_user()`; store entity references and `async_add_entities` callback |

### Implementation Order

1. Update `__init__.py` - add data storage structure and event subscriptions
2. Update `select.py` - add dynamic entity add/remove functions
3. Wire event handlers to entity management functions
4. Add cleanup in `async_unload_entry()`

### Out of Scope

- Frontend changes (UI already reacts to `hass.states` changes)
- Automations, scripts, panels auto-refresh (less common to add/remove)
- Batch operations optimization
