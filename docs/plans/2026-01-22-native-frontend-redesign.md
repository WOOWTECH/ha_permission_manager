# PRD: Recreate Frontend with HA Native Components

**Version:** 1.0
**Date:** 2026-01-22
**Status:** Approved

## Problem Statement

The current frontend has several issues:
- **External CDN dependency** - Imports Lit Element from unpkg.com, fails offline
- **Custom styling** - Doesn't inherit HA themes (dark mode broken)
- **Non-standard UX** - Custom components don't match HA's look and feel
- **Maintenance burden** - Must manually update when HA changes

## Solution

Rebuild the frontend using only Home Assistant's native frontend components:
- Use HA's bundled Lit (no external CDN)
- Use `ha-tabs` for resource type navigation
- Use `ha-data-table` for user/permission display
- Use `ha-select` for permission changes
- Inherit all HA CSS variables for automatic theme support

## Goals

- Zero external dependencies
- Automatic dark/light theme support
- Standard HA UX patterns
- Reduced code complexity

---

## Component Architecture

### HA Native Components Used

| Component | Purpose |
|-----------|---------|
| `ha-tabs` | Resource type navigation (Areas, Labels, Automations, etc.) |
| `ha-data-table` | Display users and permissions in tabular format |
| `ha-select` | Permission level dropdown selector |
| `ha-icon` | Icons throughout the UI |
| `ha-card` | Container for content sections |
| `ha-top-app-bar-fixed` | Header with title and stats |
| `ha-textfield` | Search input for filtering |
| `ha-chip` | Stats badges (users count, resources count) |

### CSS Variables Used (HA Theme)

```css
--primary-color
--primary-text-color
--secondary-text-color
--card-background-color
--divider-color
--table-row-background-color
--table-row-alternative-background-color
--mdc-theme-primary
--mdc-select-fill-color
```

### File Structure

```
www/
  ha_permission_manager.js  (complete rewrite)
```

Single file, no external dependencies. Uses HA's bundled Lit.

---

## UI Layout & Behavior

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  ha-top-app-bar-fixed                                   │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 🛡 Permission Manager    [Users: 3] [Resources: 12] ││
│  └─────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────┤
│  ha-textfield (search)                                  │
├─────────────────────────────────────────────────────────┤
│  ha-tabs                                                │
│  [ Areas | Labels | Automations | Scripts | Panels ]    │
├─────────────────────────────────────────────────────────┤
│  ha-card                                                │
│  ┌─────────────────────────────────────────────────────┐│
│  │ ha-data-table                                       ││
│  │ ┌──────────┬──────────┬──────────┬──────────┐       ││
│  │ │ User     │ Kitchen  │ Bedroom  │ Office   │       ││
│  │ ├──────────┼──────────┼──────────┼──────────┤       ││
│  │ │ Admin 👤 │ [Full ▼] │ [Full ▼] │ [Full ▼] │       ││
│  │ │ Guest 👤 │ [View ▼] │ [Deny ▼] │ [Deny ▼] │       ││
│  │ └──────────┴──────────┴──────────┴──────────┘       ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Behavior

- **Tab switch** → Load resources for that type, update table columns
- **Search** → Filter resources (columns) by name
- **ha-select change** → Call `hass.callService("select", "select_option", ...)`
- **Protected permissions** → Dropdown disabled, shows lock icon

### Permission Dropdown Options

```
Denied   (0) - Red indicator
View     (1) - Orange indicator
Control  (2) - Blue indicator
Full     (3) - Green indicator
```

---

## Implementation Details

### Import Pattern (HA Native)

```javascript
// Use HA's bundled Lit - no external CDN
const { LitElement, html, css, nothing } = window.litElement || {};

// HA components are globally available when panel loads
// No imports needed for ha-tabs, ha-card, ha-select, etc.
```

### Key Implementation Notes

**1. Access HA Theme Variables**
```css
:host {
  --permission-denied: var(--error-color, #db4437);
  --permission-view: var(--warning-color, #ff9800);
  --permission-control: var(--info-color, #039be5);
  --permission-full: var(--success-color, #43a047);
}
```

**2. ha-select for Permissions**
```javascript
html`
  <ha-select
    .value=${currentLevel}
    @selected=${(e) => this._changePermission(entityId, e.target.value)}
    ?disabled=${isProtected}
  >
    <mwc-list-item value="0">Denied</mwc-list-item>
    <mwc-list-item value="1">View</mwc-list-item>
    <mwc-list-item value="2">Control</mwc-list-item>
    <mwc-list-item value="3">Full</mwc-list-item>
  </ha-select>
`
```

**3. Tab Change Handler**
```javascript
_handleTabChange(e) {
  this._activeTab = e.detail.index;
  this._currentType = this._availableTypes[this._activeTab];
}
```

---

## Testing & Validation

### Manual Testing Checklist

1. **Theme support** - Switch HA between light/dark mode, verify panel adapts
2. **Tab navigation** - Click each tab, verify correct resources load
3. **Search filter** - Type in search, verify columns filter correctly
4. **Permission change** - Select new permission, verify service call succeeds
5. **Protected permissions** - Verify admin's Permission Manager access is locked
6. **Loading state** - Verify spinner shows while entities load
7. **Empty state** - Verify graceful message when no resources exist
8. **Mobile responsive** - Test on narrow viewport, verify layout adapts

### Browser Compatibility

- Chrome/Edge (primary)
- Firefox
- Safari
- HA Companion App (iOS/Android)

### Rollback

If issues arise, restore the previous `www/ha_permission_manager.js` file. No backend changes required.

---

## Summary

### File to Modify

| File | Action |
|------|--------|
| `www/ha_permission_manager.js` | Complete rewrite using HA native components |

### HA Components Used

- `ha-top-app-bar-fixed` - Header bar
- `ha-tabs` / `mwc-tab-bar` - Resource type tabs
- `ha-card` - Content container
- `ha-data-table` - User/permission grid
- `ha-select` / `ha-combo-box` - Permission dropdown
- `ha-textfield` - Search input
- `ha-icon` - Icons
- `ha-chip` - Stats badges

### Implementation Checklist

1. Remove external CDN import, use HA's bundled Lit
2. Create tab-based layout with `ha-tabs`
3. Build data table structure for each resource type
4. Implement `ha-select` dropdowns for permission changes
5. Add search filtering with `ha-textfield`
6. Use HA CSS variables for full theme support
7. Handle loading and empty states
8. Preserve protected permission behavior (disabled selects)

### Out of Scope

- Backend changes (none required)
- New features (same functionality, new UI)
- Localization/i18n
