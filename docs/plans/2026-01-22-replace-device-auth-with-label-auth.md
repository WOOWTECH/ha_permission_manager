# PRD: Replace Device Auth with Label Auth

**Version:** 1.0
**Date:** 2026-01-22
**Status:** Approved

## Problem Statement

The current HA Permission Manager creates permission entities for each user×device combination. With typical Home Assistant installations having 50-200+ devices, this creates:
- Hundreds of permission entities (users × devices)
- Unwieldy UI with long device lists
- No logical grouping for access control

## Solution

Remove device-based permission management and rely on the existing label-based permissions. Labels provide:
- **Scalability**: One permission per label instead of per device
- **Flexibility**: Devices can be dynamically added/removed from labels without changing permission rules
- **Logical grouping**: "Guest Access", "Kitchen Devices", "Sensitive Controls"

## Scope

- Remove `discover_devices()` from backend
- Remove device-related constants and prefixes
- Update frontend to remove "Devices" filter and resource config
- This is an **informational** system - enforcement happens externally

---

## Backend Changes

### Files Modified

#### `const.py`
- **Remove**: `PREFIX_DEVICE = "device_"` constant

#### `discovery.py`
- **Remove**: `discover_devices()` function
- **Remove**: `PREFIX_DEVICE` from imports
- **Update**: `discover_all_resources()` - remove `"devices"` key from returned dict

#### `select.py`
- No changes required (entity creation is driven by `discover_all_resources()` output)

#### `__init__.py`
- No changes required (loads resources dynamically)

### Code Changes Summary

```python
# const.py - REMOVE this line:
PREFIX_DEVICE = "device_"

# discovery.py - REMOVE entire function:
def discover_devices(hass: HomeAssistant) -> list[Resource]:
    ...

# discovery.py - UPDATE discover_all_resources():
def discover_all_resources(hass: HomeAssistant) -> dict[str, list[Resource]]:
    return {
        "areas": discover_areas(hass),
        "labels": discover_labels(hass),
        # "devices" line removed
        "automations": discover_automations(hass),
        "scripts": discover_scripts(hass),
        "panels": discover_panels(hass),
        "custom": discover_custom(hass),
    }
```

---

## Frontend Changes

### File Modified

#### `www/ha_permission_manager.js`

**Remove from `RESOURCE_CONFIG` object:**
```javascript
// REMOVE this line:
devices: { icon: "mdi:devices", label: "Devices" },
```

**Update `_getFilteredTypes()` preferred order:**
```javascript
// CHANGE FROM:
const preferredOrder = ["areas", "labels", "devices", "automations", "scripts", "panels", "customs"];

// CHANGE TO:
const preferredOrder = ["areas", "labels", "automations", "scripts", "panels", "customs"];
```

### Result

- "Devices" filter pill will no longer appear in the UI
- Device resources will not be rendered in the permission matrix

---

## Testing & Validation

### Manual Testing Checklist

1. **Reload integration** - Verify no errors in Home Assistant logs
2. **Check entity count** - Confirm no `select.perm_*_device_*` entities exist
3. **Verify labels work** - Label permission entities still created correctly
4. **Frontend UI** - Confirm "Devices" filter pill is gone
5. **Other resources** - Areas, automations, scripts, panels, custom still function

### Edge Cases

- **Existing device entities**: After update, orphaned `select.perm_*_device_*` entities may remain. Users should manually delete them via Developer Tools or remove/re-add the integration.

### Rollback

If issues arise, revert the 3 file changes (const.py, discovery.py, ha_permission_manager.js).

---

## Summary

| File | Action |
|------|--------|
| `const.py` | Remove `PREFIX_DEVICE` |
| `discovery.py` | Remove `discover_devices()`, update `discover_all_resources()` |
| `www/ha_permission_manager.js` | Remove devices from `RESOURCE_CONFIG` and `preferredOrder` |

### Implementation Order

1. `const.py` - Remove constant
2. `discovery.py` - Remove function and import, update return dict
3. `www/ha_permission_manager.js` - Remove devices from config and order array

### Out of Scope

- Migration tooling for existing device permissions
- Enforcement layer (external responsibility)
- Changes to areas, labels, automations, scripts, panels, or custom resources
