# PRD: Admin Users Default Full Edit Permission

**Version:** 1.0
**Date:** 2026-01-25
**Status:** Draft

---

## 1. Overview

### 1.1 Problem Statement

Currently, when a new admin user is created in Home Assistant, their permission entities for the Permission Manager panel are initialized with default "Closed" (level 0) permission. This means:

1. New admin users cannot access the Permission Manager panel until another admin grants them access
2. If all admin users accidentally lose access to the Permission Manager panel, there's no way to recover
3. Admin users should inherently have full control over permission management

### 1.2 Proposed Solution

Automatically grant **all admin users** full "Edit" (level 3) permission for **all resources** in the Permission Manager, not just the Permission Manager panel itself. This ensures:

1. New admin users immediately have full control
2. Bootstrap protection is extended to all admin permissions
3. Consistent with Home Assistant's admin role expectations

---

## 2. Requirements

### 2.1 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | All admin users shall have default permission level "3" (Edit) for ALL resources | P0 |
| FR-2 | Admin user permissions for all resources shall be marked as "protected" (read-only in UI) | P0 |
| FR-3 | When a new admin user is added, all their permission entities shall initialize to level "3" | P0 |
| FR-4 | When an existing user is promoted to admin, their permissions shall update to level "3" | P1 |
| FR-5 | Protected permissions shall display a lock icon (🔒) in the frontend | P0 |
| FR-6 | Non-admin users shall retain current behavior (default to "0", editable) | P0 |

### 2.2 Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-1 | Permission check shall add no noticeable latency (<10ms) | P1 |
| NFR-2 | Solution shall be backwards compatible with existing permission states | P0 |
| NFR-3 | Solution shall work with dynamically added/removed admin users | P0 |

---

## 3. Current Implementation

### 3.1 Current `is_protected_permission` Function

```python
def is_protected_permission(user_id: str, resource_id: str, admin_ids: set[str]) -> bool:
    """Check if a user-resource permission is protected (admin + Permission Manager panel)."""
    return user_id in admin_ids and resource_id == SELF_PANEL_ID
```

**Current behavior:** Only protects admin users' access to the Permission Manager panel (`panel_ha_permission_manager`).

### 3.2 Current Entity Initialization

```python
entity = PermissionSelectEntity(
    user=user,
    resource=resource,
    is_protected=is_protected,  # Only True for admin + PM panel
)
# Default: "3" if protected, else "0"
self._attr_current_option = "3" if is_protected else "0"
```

---

## 4. Proposed Changes

### 4.1 Update `is_protected_permission` Function

**File:** `select.py`

```python
def is_protected_permission(user_id: str, resource_id: str, admin_ids: set[str]) -> bool:
    """Check if a user-resource permission is protected.

    Admin users have full edit permission for ALL resources, which cannot be changed.
    This ensures admins always maintain control over the system.
    """
    return user_id in admin_ids
```

**Rationale:** Remove the `resource_id == SELF_PANEL_ID` condition so ALL admin permissions are protected.

### 4.2 Update Default Permission for Admins

**File:** `select.py` - `PermissionSelectEntity.__init__`

Already handled by existing logic:
```python
self._attr_current_option = "3" if is_protected else "0"
```

Since `is_protected` will now be `True` for all admin+resource combinations, admins will default to "3".

### 4.3 Update State Restoration

**File:** `select.py` - `async_added_to_hass`

Current logic already enforces protected entities stay at "3":
```python
if self._is_protected:
    self._attr_current_option = "3"
else:
    self._attr_current_option = last_state.state
```

No changes needed.

### 4.4 Frontend Updates

**File:** `www/ha_permission_manager.js`

No changes needed. The frontend already:
- Displays 🔒 icon for protected entities
- Disables dropdown for protected entities
- Shows "protected" tooltip

---

## 5. Migration & Backwards Compatibility

### 5.1 Existing Admin Users

When HA restarts after upgrade:
1. `is_protected` will now return `True` for all admin permissions
2. `async_added_to_hass` will override any restored state to "3"
3. UI will show all admin permissions as locked

### 5.2 Existing Non-Admin Users

No change - their permissions remain as previously set.

### 5.3 Data Migration

No database migration required. State restoration logic handles the transition automatically.

---

## 6. Test Cases

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| TC-1 | Create new admin user | All permission entities initialize to "3" with 🔒 |
| TC-2 | Create new non-admin user | All permission entities initialize to "0", editable |
| TC-3 | Try to change admin permission via UI | Dropdown disabled, no change possible |
| TC-4 | Try to change admin permission via service call | Warning logged, no change made |
| TC-5 | Restart HA with existing admin | All admin permissions reset to "3" |
| TC-6 | Demote admin to regular user | Permissions become editable (future FR-4) |

---

## 7. Implementation Checklist

- [ ] Update `is_protected_permission()` in `select.py`
- [ ] Update version to 2.2.0 in `manifest.json` and `__init__.py`
- [ ] Update cache-busting version in `__init__.py` panel config
- [ ] Add/update unit tests
- [ ] Update translations if any new strings needed
- [ ] Test with new admin user creation
- [ ] Test with existing admin users after upgrade
- [ ] Test UI shows lock icon for all admin permissions
- [ ] Sync to HA and verify

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Admin loses ability to delegate limited access | Medium | Admins can create non-admin users with specific permissions |
| Breaking change for existing setups | Low | State restoration handles migration automatically |
| Performance impact with many users/resources | Low | Simple boolean check, negligible overhead |

---

## 9. Future Considerations

1. **FR-4 Implementation:** Handle user role changes (admin ↔ non-admin) dynamically
2. **Audit Logging:** Log permission change attempts on protected entities
3. **Super Admin Role:** Optional role that can even modify other admin permissions

---

## 10. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
| QA Lead | | | |
