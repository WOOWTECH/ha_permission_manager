---
name: e2e-test-plan
description: Comprehensive E2E test suite using Playwright MCP for ha_permission_manager
created: 2026-02-09T07:19:40Z
updated: 2026-02-09T07:19:40Z
status: ready
---

# E2E Test Plan: ha_permission_manager Component

## Test Environment Setup

### Target Environment
| Setting | Value |
|---------|-------|
| URL | `https://matt-test-254-ha.woowtech.io/` |
| Home Assistant Version | 2025.1.0+ |
| Component Version | 3.0.0 |

### Test Accounts
| Role | Username | Password | Expected Access |
|------|----------|----------|-----------------|
| Admin | `admin` | `woowtech` | Full access to all panels, areas, labels, entities |
| User | `user` | `user` | Restricted access based on permission settings |

### Playwright MCP Tools Reference
```
browser_navigate    - Navigate to URL
browser_snapshot    - Capture accessibility tree (preferred over screenshot)
browser_click       - Click elements by ref
browser_type        - Type text into elements
browser_fill_form   - Fill multiple form fields
browser_wait_for    - Wait for conditions (text, time)
browser_evaluate    - Run JavaScript in page context
browser_console_messages - Check browser console for errors
browser_press_key   - Press keyboard keys
browser_select_option - Select dropdown options
```

### Test Data Prerequisites
- [ ] Admin account exists with full permissions
- [ ] User account exists with restricted permissions
- [ ] At least 3 areas configured (e.g., Living Room, Bedroom, Kitchen)
- [ ] At least 2 labels configured (e.g., Lights, Security)
- [ ] Various entities exist in areas (lights, switches, sensors)
- [ ] At least one custom dashboard configured
- [ ] Permission entities created for user account

---

## Test Category 1: Authentication & Access Control

### TEST-AUTH-001: Admin Login Success
**Priority**: Critical
**Preconditions**: Not logged in

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/
2. browser_wait_for: text "Home Assistant"
3. browser_snapshot: Capture login page
4. browser_type: ref="username", text="admin"
5. browser_type: ref="password", text="woowtech"
6. browser_click: ref="login-button" (or submit form)
7. browser_wait_for: text disappear "Log in"
8. browser_snapshot: Capture authenticated state
```

**Expected Results**:
- Login form accepts credentials
- Redirect to main dashboard
- Sidebar visible with all panels
- No console errors

---

### TEST-AUTH-002: User Login Success
**Priority**: Critical
**Preconditions**: Not logged in

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/
2. browser_wait_for: text "Home Assistant"
3. browser_type: ref="username", text="user"
4. browser_type: ref="password", text="user"
5. browser_click: ref="login-button"
6. browser_wait_for: text disappear "Log in"
7. browser_snapshot: Capture user authenticated state
```

**Expected Results**:
- Login succeeds
- Limited sidebar panels visible
- Permission-restricted content hidden
- No console errors

---

### TEST-AUTH-003: Admin Auto-Detection
**Priority**: High
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
2. browser_wait_for: text "Permission Manager"
3. browser_snapshot: Capture admin panel
4. browser_evaluate: Check for admin-only controls
```

**Expected Results**:
- Permission Manager panel loads
- All permission controls visible
- User selector dropdown present
- Can modify any user's permissions

---

### TEST-AUTH-004: Session Persistence
**Priority**: Medium
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/lovelace/
2. browser_snapshot: Capture dashboard
3. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
4. browser_snapshot: Capture control panel
5. browser_navigate: https://matt-test-254-ha.woowtech.io/lovelace/
6. browser_snapshot: Verify still authenticated
```

**Expected Results**:
- Session maintained across panel navigation
- No re-authentication required
- Same user context preserved

---

## Test Category 2: Permission Management Panel

### TEST-PERM-001: Panel Load
**Priority**: Critical
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
2. browser_wait_for: text "Permission Manager"
3. browser_snapshot: Capture full panel
4. browser_console_messages: level="error"
```

**Expected Results**:
- Panel loads without errors
- User selector dropdown present
- Permission sections visible:
  - Area permissions
  - Label permissions
  - Panel/Dashboard permissions
  - Automation permissions
  - Script permissions
- No console errors

---

### TEST-PERM-002: User Selection
**Priority**: High
**Preconditions**: Logged in as admin, on Permission Manager panel

**Steps**:
```
1. browser_snapshot: Capture initial state
2. browser_click: ref="user-selector"
3. browser_snapshot: Capture dropdown open
4. browser_click: Select "user" from list
5. browser_wait_for: time=1 (wait for state load)
6. browser_snapshot: Capture user permissions displayed
```

**Expected Results**:
- User dropdown lists all non-system users
- Selecting user loads their current permissions
- Permission levels displayed for all resources

---

### TEST-PERM-003: Area Permission Change
**Priority**: Critical
**Preconditions**: Logged in as admin, user selected

**Steps**:
```
1. browser_snapshot: Capture current area permissions
2. browser_click: ref="area-living-room-permission"
3. browser_select_option: ref="area-living-room-permission", values=["2"]
4. browser_wait_for: time=2 (wait for state update)
5. browser_evaluate:
   function: () => {
     return document.querySelector('.area-permission-living-room')?.value
   }
6. browser_snapshot: Capture updated state
```

**Expected Results**:
- Permission selector changes to "Limited" (level 2)
- Entity state updates in Home Assistant
- No page reload required
- Change persists after refresh

---

### TEST-PERM-004: Label Permission Change
**Priority**: Critical
**Preconditions**: Logged in as admin, user selected

**Steps**:
```
1. browser_snapshot: Capture current label permissions
2. browser_click: ref="label-lights-permission"
3. browser_select_option: ref="label-lights-permission", values=["3"]
4. browser_wait_for: time=2
5. browser_snapshot: Capture updated state
```

**Expected Results**:
- Permission selector changes to "Edit" (level 3)
- Label permission entity updated
- Change visible immediately

---

### TEST-PERM-005: Permission Persistence
**Priority**: High
**Preconditions**: Permission changes made in TEST-PERM-003/004

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/lovelace/
2. browser_wait_for: time=2
3. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
4. browser_wait_for: text "Permission Manager"
5. browser_click: ref="user-selector"
6. browser_click: Select "user"
7. browser_snapshot: Verify permissions retained
```

**Expected Results**:
- Navigate away and return
- Same user's permissions still show updated values
- Area permission = Limited
- Label permission = Edit

---

### TEST-PERM-006: Panel Permission Change
**Priority**: High
**Preconditions**: Logged in as admin, user selected

**Steps**:
```
1. browser_snapshot: Capture panel permissions section
2. browser_click: ref="panel-developer-tools-permission"
3. browser_select_option: ref="panel-developer-tools-permission", values=["0"]
4. browser_wait_for: time=2
5. browser_snapshot: Capture hidden panel state
```

**Expected Results**:
- Panel permission set to "Closed" (level 0)
- Developer tools will be hidden from user's sidebar

---

### TEST-PERM-007: Dashboard Permission Change
**Priority**: High
**Preconditions**: Logged in as admin, custom dashboard exists

**Steps**:
```
1. browser_snapshot: Capture dashboard permissions
2. browser_click: ref="dashboard-custom-permission"
3. browser_select_option: ref="dashboard-custom-permission", values=["1"]
4. browser_wait_for: time=2
5. browser_snapshot: Capture view-only state
```

**Expected Results**:
- Dashboard permission set to "View" (level 1)
- User can view but not edit dashboard

---

### TEST-PERM-008: Automation Permission Change
**Priority**: Medium
**Preconditions**: Logged in as admin, user selected

**Steps**:
```
1. browser_snapshot: Capture automation permissions
2. browser_click: ref="automation-permission"
3. browser_select_option: ref="automation-permission", values=["2"]
4. browser_wait_for: time=2
5. browser_snapshot: Capture limited access state
```

**Expected Results**:
- Automation permission set to "Limited"
- User can trigger but not edit automations

---

### TEST-PERM-009: Script Permission Change
**Priority**: Medium
**Preconditions**: Logged in as admin, user selected

**Steps**:
```
1. browser_snapshot: Capture script permissions
2. browser_click: ref="script-permission"
3. browser_select_option: ref="script-permission", values=["3"]
4. browser_wait_for: time=2
5. browser_snapshot: Capture edit access state
```

**Expected Results**:
- Script permission set to "Edit"
- User has full script access

---

## Test Category 3: Areas Tab

### TEST-AREA-001: Tab Navigation
**Priority**: Critical
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
2. browser_wait_for: text "Control Panel"
3. browser_snapshot: Capture initial state
4. browser_click: ref="areas-tab"
5. browser_wait_for: time=1
6. browser_snapshot: Capture Areas tab active
```

**Expected Results**:
- Control Panel loads with tabs
- Areas tab clickable
- Areas list displays after click

---

### TEST-AREA-002: Area List Display
**Priority**: High
**Preconditions**: On Areas tab, logged in as admin

**Steps**:
```
1. browser_snapshot: Capture areas list
2. browser_evaluate:
   function: () => {
     return document.querySelectorAll('.area-card').length
   }
```

**Expected Results**:
- All configured areas visible to admin
- Each area shows:
  - Area name
  - Entity count
  - Permission level indicator

---

### TEST-AREA-003: Area Selection
**Priority**: High
**Preconditions**: On Areas tab with visible areas

**Steps**:
```
1. browser_click: ref="area-living-room"
2. browser_wait_for: time=1
3. browser_snapshot: Capture area detail view
```

**Expected Results**:
- Area expands/opens to show entities
- Entities grouped by domain (lights, switches, sensors)
- Domain icons and colors displayed

---

### TEST-AREA-004: Entity Domain Grouping
**Priority**: Medium
**Preconditions**: Area selected with multiple entity types

**Steps**:
```
1. browser_snapshot: Capture domain grouping
2. browser_evaluate:
   function: () => {
     return Array.from(document.querySelectorAll('.domain-group'))
       .map(g => g.dataset.domain)
   }
```

**Expected Results**:
- Entities grouped by domain
- Domain headers visible (Light, Switch, Sensor, etc.)
- Color coding applied per domain

---

### TEST-AREA-005: Entity Control - Light Toggle
**Priority**: High
**Preconditions**: Area selected with light entities, Edit permission

**Steps**:
```
1. browser_snapshot: Capture light state (on/off)
2. browser_click: ref="light-living-room-main-toggle"
3. browser_wait_for: time=2
4. browser_snapshot: Capture toggled state
5. browser_click: ref="light-living-room-main-toggle"
6. browser_wait_for: time=2
7. browser_snapshot: Capture restored state
```

**Expected Results**:
- Light toggle button clickable
- State changes on click
- Visual feedback shows new state
- No console errors

---

### TEST-AREA-006: Area Permission Filtering - User View
**Priority**: Critical
**Preconditions**: Logged in as user with limited area permissions

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
2. browser_click: ref="areas-tab"
3. browser_wait_for: time=1
4. browser_snapshot: Capture user's area view
5. browser_evaluate:
   function: () => {
     return document.querySelectorAll('.area-card').length
   }
```

**Expected Results**:
- Only permitted areas visible
- Closed (level 0) areas hidden completely
- View-only areas show but controls disabled
- Limited areas allow control but not config

---

### TEST-AREA-007: View-Only Area Behavior
**Priority**: High
**Preconditions**: User with View (level 1) permission on an area

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
2. browser_click: ref="areas-tab"
3. browser_click: ref="area-view-only"
4. browser_snapshot: Capture view-only controls
5. browser_click: ref="light-toggle" (should fail or be disabled)
6. browser_snapshot: Capture no-change state
```

**Expected Results**:
- Area visible and expandable
- Entities listed with current states
- Toggle/control buttons disabled or hidden
- Click on controls has no effect

---

## Test Category 4: Labels Tab

### TEST-LABEL-001: Tab Navigation
**Priority**: Critical
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
2. browser_wait_for: text "Control Panel"
3. browser_click: ref="labels-tab"
4. browser_wait_for: time=1
5. browser_snapshot: Capture Labels tab active
```

**Expected Results**:
- Labels tab clickable
- Labels list displays after click
- Tab indicator shows active state

---

### TEST-LABEL-002: Label List Display
**Priority**: High
**Preconditions**: On Labels tab, logged in as admin

**Steps**:
```
1. browser_snapshot: Capture labels list
2. browser_evaluate:
   function: () => {
     return document.querySelectorAll('.label-card').length
   }
```

**Expected Results**:
- All configured labels visible to admin
- Each label shows:
  - Label name and color
  - Entity count
  - Permission level indicator

---

### TEST-LABEL-003: Label Selection
**Priority**: High
**Preconditions**: On Labels tab with visible labels

**Steps**:
```
1. browser_click: ref="label-lights"
2. browser_wait_for: time=1
3. browser_snapshot: Capture label detail view
```

**Expected Results**:
- Label expands to show entities
- All entities with this label displayed
- Domain grouping applied

---

### TEST-LABEL-004: Entity Domain Grouping by Label
**Priority**: Medium
**Preconditions**: Label selected with multiple entity types

**Steps**:
```
1. browser_snapshot: Capture domain grouping
2. browser_evaluate:
   function: () => {
     return Array.from(document.querySelectorAll('.domain-group'))
       .map(g => g.dataset.domain)
   }
```

**Expected Results**:
- Entities grouped by domain within label
- Same styling as Areas tab

---

### TEST-LABEL-005: Label Permission Filtering - User View
**Priority**: Critical
**Preconditions**: Logged in as user with limited label permissions

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
2. browser_click: ref="labels-tab"
3. browser_wait_for: time=1
4. browser_snapshot: Capture user's label view
5. browser_evaluate:
   function: () => {
     return document.querySelectorAll('.label-card').length
   }
```

**Expected Results**:
- Only permitted labels visible
- Closed labels hidden
- Permission levels respected

---

### TEST-LABEL-006: Real-Time State Updates
**Priority**: Medium
**Preconditions**: Label tab open with entities

**Steps**:
```
1. browser_snapshot: Capture initial entity states
2. browser_evaluate:
   function: () => {
     // Trigger state change via HA service call
     return fetch('/api/services/light/toggle', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ entity_id: 'light.test' })
     }).then(r => r.ok)
   }
3. browser_wait_for: time=3
4. browser_snapshot: Capture updated states
```

**Expected Results**:
- Entity state updates without page refresh
- UI reflects current state
- WebSocket pushes update to panel

---

## Test Category 5: Sidebar Filtering

### TEST-SIDEBAR-001: Admin Sidebar - Full Access
**Priority**: Critical
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/
2. browser_wait_for: time=2
3. browser_snapshot: Capture sidebar
4. browser_evaluate:
   function: () => {
     return Array.from(document.querySelectorAll('paper-listbox a'))
       .map(a => a.getAttribute('data-panel'))
   }
```

**Expected Results**:
- All standard panels visible:
  - Overview
  - Energy
  - Map
  - Logbook
  - History
  - Developer Tools
  - Configuration
  - Permission Manager
  - Control Panel

---

### TEST-SIDEBAR-002: User Sidebar - Filtered Access
**Priority**: Critical
**Preconditions**: Logged in as user with restricted panel permissions

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/
2. browser_wait_for: time=2
3. browser_snapshot: Capture user sidebar
4. browser_evaluate:
   function: () => {
     return Array.from(document.querySelectorAll('paper-listbox a'))
       .map(a => a.getAttribute('data-panel'))
   }
```

**Expected Results**:
- Restricted panels hidden (e.g., Developer Tools if closed)
- Permission Manager panel hidden for non-admin
- Only permitted panels visible
- Control Panel visible (for area/label access)

---

### TEST-SIDEBAR-003: Panel Visibility Update
**Priority**: High
**Preconditions**: Two browser sessions - admin and user

**Steps**:
```
# Session 1 - Admin
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
2. Change user's panel permission to Closed

# Session 2 - User
3. browser_navigate: https://matt-test-254-ha.woowtech.io/ (refresh)
4. browser_snapshot: Capture updated sidebar
```

**Expected Results**:
- Panel disappears from user's sidebar
- No page reload required (WebSocket update)
- Change effective immediately

---

### TEST-SIDEBAR-004: Custom Dashboard Visibility
**Priority**: Medium
**Preconditions**: Custom dashboard exists, user has restricted access

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/
2. browser_snapshot: Capture sidebar with dashboards
3. browser_evaluate:
   function: () => {
     return Array.from(document.querySelectorAll('[data-panel^="lovelace-"]'))
       .map(a => a.getAttribute('data-panel'))
   }
```

**Expected Results**:
- Permitted dashboards visible
- Restricted dashboards hidden from sidebar
- Default dashboard always accessible

---

## Test Category 6: Dashboard Filtering

### TEST-DASHBOARD-001: Admin Dashboard Access
**Priority**: High
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/lovelace/custom-dashboard
2. browser_wait_for: time=2
3. browser_snapshot: Capture dashboard
4. browser_console_messages: level="error"
```

**Expected Results**:
- Dashboard loads fully
- All cards rendered
- Edit mode available
- No errors

---

### TEST-DASHBOARD-002: User Dashboard - View Only
**Priority**: High
**Preconditions**: Logged in as user with View (level 1) dashboard permission

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/lovelace/custom-dashboard
2. browser_wait_for: time=2
3. browser_snapshot: Capture view-only dashboard
4. browser_evaluate:
   function: () => {
     return document.querySelector('hui-root')?.shadowRoot
       ?.querySelector('.edit-mode') === null
   }
```

**Expected Results**:
- Dashboard displays content
- Edit button hidden or disabled
- Cards visible but not configurable

---

### TEST-DASHBOARD-003: Restricted Dashboard - Access Denied
**Priority**: High
**Preconditions**: Logged in as user with Closed (level 0) dashboard permission

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/lovelace/restricted-dashboard
2. browser_wait_for: time=2
3. browser_snapshot: Capture access denied page
```

**Expected Results**:
- Access denied message displayed
- Friendly error message shown
- Redirect or navigation options provided
- No sensitive content exposed

---

### TEST-DASHBOARD-004: Content Filtering by Permission
**Priority**: Medium
**Preconditions**: Dashboard with cards for entities user cannot access

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/lovelace/mixed-dashboard
2. browser_wait_for: time=2
3. browser_snapshot: Capture filtered dashboard
4. browser_evaluate:
   function: () => {
     return document.querySelectorAll('hui-card').length
   }
```

**Expected Results**:
- Cards for permitted entities display
- Cards for restricted entities hidden or show "no access"
- Dashboard layout adjusts gracefully

---

## Test Category 7: WebSocket API

### TEST-WS-001: Get User Permitted Areas
**Priority**: Critical
**Preconditions**: Logged in as user

**Steps**:
```
1. browser_evaluate:
   function: async () => {
     const ws = new WebSocket('wss://matt-test-254-ha.woowtech.io/api/websocket');
     // Send get_user_permitted_areas command
     // Return response
   }
2. browser_console_messages: level="debug"
```

**Expected Results**:
- WebSocket returns array of permitted areas
- Each area includes: id, name, permission_level
- Response time < 100ms
- Only areas with level > 0 included

---

### TEST-WS-002: Get User Permitted Labels
**Priority**: Critical
**Preconditions**: Logged in as user

**Steps**:
```
1. browser_evaluate:
   function: async () => {
     // Send get_user_permitted_labels command
     // Return response
   }
```

**Expected Results**:
- WebSocket returns array of permitted labels
- Each label includes: id, name, color, permission_level
- Response time < 100ms

---

### TEST-WS-003: Get Entities for Area
**Priority**: High
**Preconditions**: Logged in, area ID known

**Steps**:
```
1. browser_evaluate:
   function: async () => {
     // Send get_entities_for_area command with area_id
     // Return grouped entities
   }
```

**Expected Results**:
- Returns entities grouped by domain
- Each entity includes: entity_id, state, attributes
- Only entities in permitted area returned
- Response time < 100ms

---

### TEST-WS-004: Get Entities for Label
**Priority**: High
**Preconditions**: Logged in, label ID known

**Steps**:
```
1. browser_evaluate:
   function: async () => {
     // Send get_entities_for_label command with label_id
     // Return grouped entities
   }
```

**Expected Results**:
- Returns entities grouped by domain
- Entities match the specified label
- Permission-filtered results

---

### TEST-WS-005: WebSocket Authentication Required
**Priority**: High
**Preconditions**: Not authenticated

**Steps**:
```
1. browser_evaluate:
   function: async () => {
     // Attempt WebSocket command without auth
     // Should fail
   }
```

**Expected Results**:
- Unauthenticated request rejected
- Error response returned
- No data leaked

---

### TEST-WS-006: Response Time Performance
**Priority**: Medium
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_evaluate:
   function: async () => {
     const start = performance.now();
     // Execute get_user_permitted_areas
     const end = performance.now();
     return end - start;
   }
```

**Expected Results**:
- Response time < 100ms
- Consistent performance across multiple calls
- No timeout errors

---

## Test Category 8: Event-Driven Updates

### TEST-EVENT-001: Area Registry Change
**Priority**: High
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/config/areas/dashboard
2. Create new area "Test Area"
3. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
4. browser_snapshot: Capture new area in permissions
```

**Expected Results**:
- New area appears in Permission Manager
- Permission entity created for new area
- No page reload required

---

### TEST-EVENT-002: Label Registry Change
**Priority**: High
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/config/labels
2. Create new label "Test Label"
3. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
4. browser_snapshot: Capture new label in permissions
```

**Expected Results**:
- New label appears in Permission Manager
- Permission entity created for new label
- Automatic detection without restart

---

### TEST-EVENT-003: User Addition
**Priority**: High
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/config/users/picker
2. Create new user "testuser"
3. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
4. browser_click: ref="user-selector"
5. browser_snapshot: Capture new user in dropdown
```

**Expected Results**:
- New user appears in user selector
- Permission entities created for new user
- Default permissions applied

---

### TEST-EVENT-004: User Removal Cleanup
**Priority**: Medium
**Preconditions**: Test user exists with permission entities

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/config/users/picker
2. Delete "testuser"
3. browser_navigate: https://matt-test-254-ha.woowtech.io/developer-tools/state
4. Search for "testuser" permission entities
5. browser_snapshot: Capture cleanup state
```

**Expected Results**:
- Deleted user removed from selector
- Permission entities cleaned up
- No orphaned entities

---

### TEST-EVENT-005: Dashboard Change Detection
**Priority**: Medium
**Preconditions**: Logged in as admin

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/lovelace/0?edit=1
2. Add new dashboard via UI
3. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
4. browser_snapshot: Capture new dashboard in permissions
```

**Expected Results**:
- New dashboard appears in Permission Manager
- Permission entity created automatically
- Sidebar updates for users

---

### TEST-EVENT-006: Panel Change Updates
**Priority**: Medium
**Preconditions**: Custom panel added/removed

**Steps**:
```
1. browser_evaluate:
   function: () => {
     // Subscribe to panel changes
     // Trigger panel update
     // Verify sidebar refresh
   }
```

**Expected Results**:
- Panel changes reflected in sidebar
- Real-time update via WebSocket
- No manual refresh needed

---

## Test Category 9: Cross-User Permissions

### TEST-CROSS-001: Admin Changes User Permission
**Priority**: Critical
**Preconditions**: Admin logged in, user has default permissions

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
2. browser_click: ref="user-selector"
3. browser_click: Select "user"
4. browser_select_option: ref="area-kitchen-permission", values=["0"]
5. browser_wait_for: time=2
6. browser_snapshot: Capture permission set to Closed
```

**Expected Results**:
- Admin can change user's permissions
- Permission entity state updated
- Change ready to affect user

---

### TEST-CROSS-002: Permission Affects Target User
**Priority**: Critical
**Preconditions**: Admin set user's Kitchen area to Closed

**Steps**:
```
# New browser session or logout/login as user
1. browser_navigate: https://matt-test-254-ha.woowtech.io/
2. browser_type: ref="username", text="user"
3. browser_type: ref="password", text="user"
4. browser_click: ref="login-button"
5. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
6. browser_click: ref="areas-tab"
7. browser_snapshot: Capture user's area view (Kitchen hidden)
```

**Expected Results**:
- Kitchen area not visible to user
- Other permitted areas still visible
- Permission change effective immediately

---

### TEST-CROSS-003: Multiple Permission Levels
**Priority**: High
**Preconditions**: Different permission levels set for same user

**Steps**:
```
# Admin sets:
# - Living Room: View (1)
# - Bedroom: Limited (2)
# - Kitchen: Closed (0)

# As user:
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
2. browser_click: ref="areas-tab"
3. browser_snapshot: Capture multi-level permissions
```

**Expected Results**:
- Kitchen hidden (Closed)
- Living Room visible, controls disabled (View)
- Bedroom visible, controls enabled (Limited)

---

### TEST-CROSS-004: Admin Always Has Full Access
**Priority**: Critical
**Preconditions**: Admin account, any permission entity states

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
2. browser_click: ref="areas-tab"
3. browser_snapshot: Capture admin full access
4. browser_evaluate:
   function: () => {
     return document.querySelectorAll('.area-card').length
   }
```

**Expected Results**:
- Admin sees all areas regardless of permission entities
- All controls enabled
- No restrictions applied to admin

---

### TEST-CROSS-005: User Permission Update Without Re-login
**Priority**: High
**Preconditions**: User logged in, admin about to change permission

**Steps**:
```
# User session open on Control Panel
# Admin changes user's Bedroom to Closed

# On user session:
1. browser_wait_for: time=5 (WebSocket update)
2. browser_snapshot: Capture updated view
# or
1. browser_press_key: key="F5" (refresh)
2. browser_snapshot: Capture updated view
```

**Expected Results**:
- User sees updated permissions
- WebSocket pushes update (ideal)
- Or refresh shows changes (acceptable)
- No re-login required

---

## Test Category 10: Error Handling & Edge Cases

### TEST-ERROR-001: Panel Load with WebSocket Failure
**Priority**: High
**Preconditions**: Simulate WebSocket disconnect

**Steps**:
```
1. browser_evaluate:
   function: () => {
     // Disconnect WebSocket
     window.hassConnection?.close();
   }
2. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
3. browser_wait_for: time=3
4. browser_snapshot: Capture degraded state
```

**Expected Results**:
- Panel shows loading or error state
- Graceful error message displayed
- No JavaScript exceptions
- Retry mechanism visible

---

### TEST-ERROR-002: Missing Area Handling
**Priority**: Medium
**Preconditions**: Area deleted but permission entity exists

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
2. browser_snapshot: Capture orphaned permission handling
3. browser_console_messages: level="error"
```

**Expected Results**:
- No errors for missing area
- Orphaned permissions handled gracefully
- UI continues to function
- Cleanup happens automatically or is non-blocking

---

### TEST-ERROR-003: Missing Label Handling
**Priority**: Medium
**Preconditions**: Label deleted but permission entity exists

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
2. browser_snapshot: Capture orphaned permission handling
3. browser_console_messages: level="error"
```

**Expected Results**:
- No errors for missing label
- Graceful handling in UI
- No crashes or exceptions

---

### TEST-ERROR-004: Deleted User in Permissions
**Priority**: Medium
**Preconditions**: User deleted but permission entities remain

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
2. browser_click: ref="user-selector"
3. browser_snapshot: Capture user list (deleted user should not appear)
```

**Expected Results**:
- Deleted user not in selector
- No errors in console
- Orphaned entities don't affect UI

---

### TEST-ERROR-005: Console Error-Free Operation
**Priority**: Critical
**Preconditions**: Fresh browser session

**Steps**:
```
1. browser_navigate: https://matt-test-254-ha.woowtech.io/
2. Login as admin
3. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
4. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
5. browser_click: ref="areas-tab"
6. browser_click: ref="labels-tab"
7. browser_console_messages: level="error"
```

**Expected Results**:
- Zero JavaScript errors
- Zero failed network requests
- Zero undefined references
- Clean console throughout navigation

---

### TEST-ERROR-006: Network Timeout Handling
**Priority**: Medium
**Preconditions**: Slow network simulation

**Steps**:
```
1. browser_evaluate:
   function: () => {
     // Simulate slow network
   }
2. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_control_panel
3. browser_wait_for: time=30
4. browser_snapshot: Capture timeout handling
```

**Expected Results**:
- Loading indicator shown
- Timeout message after threshold
- Retry option available
- No infinite loading states

---

### TEST-ERROR-007: Invalid Permission Value Handling
**Priority**: Low
**Preconditions**: Manually set invalid permission value

**Steps**:
```
1. browser_evaluate:
   function: () => {
     // Set invalid permission value via service call
   }
2. browser_navigate: https://matt-test-254-ha.woowtech.io/ha_permission_manager
3. browser_snapshot: Capture handling of invalid value
```

**Expected Results**:
- Invalid values corrected or ignored
- UI shows valid default
- No crashes or exceptions

---

## Test Execution Checklist

### Pre-Execution
- [ ] Test environment accessible
- [ ] Admin credentials working
- [ ] User credentials working
- [ ] All areas configured
- [ ] All labels configured
- [ ] Permission Manager component installed
- [ ] Control Panel component installed

### Execution Order
1. Authentication tests (TEST-AUTH-*)
2. Permission Management tests (TEST-PERM-*)
3. Areas Tab tests (TEST-AREA-*)
4. Labels Tab tests (TEST-LABEL-*)
5. Sidebar Filtering tests (TEST-SIDEBAR-*)
6. Dashboard Filtering tests (TEST-DASHBOARD-*)
7. WebSocket API tests (TEST-WS-*)
8. Event-Driven tests (TEST-EVENT-*)
9. Cross-User tests (TEST-CROSS-*)
10. Error Handling tests (TEST-ERROR-*)

### Post-Execution
- [ ] Document all failures with screenshots
- [ ] Create bug reports for failures
- [ ] Verify all critical tests pass
- [ ] Generate test summary report

---

## Rollback Procedures

If tests reveal critical failures:

1. **Revert to previous version**:
   ```bash
   git checkout v2.9.1 -- custom_components/ha_permission_manager/
   ```

2. **Restart Home Assistant**:
   ```bash
   ha core restart
   ```

3. **Verify rollback**:
   - Check component version in HA Settings
   - Verify basic functionality works
   - Document what broke for fix iteration

---

## Test Data Templates

### Permission Level Reference
| Level | Name | Description |
|-------|------|-------------|
| 0 | Closed | No access, hidden |
| 1 | View | Read-only access |
| 2 | Limited | Control but no config |
| 3 | Edit | Full access |

### Sample Area Setup
```yaml
areas:
  - id: living_room
    name: Living Room
    entities: [light.main, switch.tv, sensor.temperature]
  - id: bedroom
    name: Bedroom
    entities: [light.bedroom, switch.fan]
  - id: kitchen
    name: Kitchen
    entities: [light.kitchen, sensor.humidity]
```

### Sample Label Setup
```yaml
labels:
  - id: lights
    name: Lights
    color: "#FFD700"
    entities: [light.main, light.bedroom, light.kitchen]
  - id: security
    name: Security
    color: "#FF0000"
    entities: [binary_sensor.door, binary_sensor.motion]
```

### Sample User Permissions
```yaml
user_permissions:
  area_living_room: 3  # Edit
  area_bedroom: 2      # Limited
  area_kitchen: 1      # View
  label_lights: 3      # Edit
  label_security: 0    # Closed
  panel_developer_tools: 0  # Closed
  dashboard_custom: 1  # View
```

---

## Appendix: Playwright MCP Command Examples

### Login Flow
```
browser_navigate: url="https://matt-test-254-ha.woowtech.io/"
browser_wait_for: text="Home Assistant"
browser_snapshot: {}
browser_type: ref="input-username", text="admin"
browser_type: ref="input-password", text="woowtech"
browser_click: ref="button-login"
browser_wait_for: textGone="Log in"
```

### Tab Navigation
```
browser_click: ref="tab-areas"
browser_wait_for: time=1
browser_snapshot: {}
```

### Form Filling
```
browser_fill_form: fields=[
  {name: "username", type: "textbox", ref: "input-username", value: "admin"},
  {name: "password", type: "textbox", ref: "input-password", value: "woowtech"}
]
```

### Console Check
```
browser_console_messages: level="error"
# Returns any console errors for validation
```

### JavaScript Evaluation
```
browser_evaluate:
  function: "() => document.querySelectorAll('.area-card').length"
# Returns count of area cards
```
