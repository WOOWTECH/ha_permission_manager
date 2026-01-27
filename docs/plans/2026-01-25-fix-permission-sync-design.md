# Fix Permission Sync on User Role Change

## Problem Statement

The frontend permission blocking has two critical bugs:

1. **Admin → User**: When an admin is demoted to regular user, all panels become denied by default instead of only denying panels explicitly set to permission level 0.

2. **User → Admin**: When a user is promoted to admin, panels remain locked/restricted instead of becoming fully accessible.

## Root Cause Analysis

### Issue 1: Corrupted Original Panels Cache
- `originalPanels` stores panels on first load
- After filtering, subsequent re-filters use already-filtered list
- When permissions change, we filter from corrupted base → everything disappears

### Issue 2: No User Role Change Detection
- `isAdmin` flag is set once on page load
- No subscription to user role changes
- Admin status is stale after role change

### Issue 3: Browser Caching
- JS files cached by browser
- Version query string not updated on changes
- Users see old behavior even after backend updates

## Solution Design

### Approach: Server-Side Permission Resolution + Force Refresh

**Key Principle**: Move all permission logic to backend WebSocket API. Frontend just applies what backend says.

### Backend Changes

Modify `websocket_api.py` to return:
```python
{
    "permissions": {"panel_id": level, ...},
    "is_admin": True/False,
    "user_id": "xxx"
}
```

- Backend already knows if user is admin
- Backend returns complete permission state
- Frontend doesn't need to check admin status separately

### Frontend Changes

1. **Remove client-side admin check** - trust backend `is_admin` flag

2. **Fix original panels storage** - fetch panels from HA API instead of caching from DOM

3. **Subscribe to user changes** - listen for `user_updated` events

4. **Force page reload on role change** - cleanest way to reset all state

5. **Add cache-busting** - use timestamp in JS URL

### Data Flow

```
User Role Changes (in HA Settings)
         ↓
HA fires 'user_updated' event
         ↓
Frontend receives event
         ↓
Force page reload (location.reload())
         ↓
Fresh JS loads, fresh permissions fetched
         ↓
Correct filtering applied
```

## Implementation Tasks

### Task 1: Update WebSocket API Response
- Add `is_admin` and `user_id` to response
- Ensure admin users get empty permissions (no filtering needed)

### Task 2: Simplify Frontend Filter
- Remove `checkIsAdmin()` function
- Use `is_admin` from API response
- Remove `originalPanels` cache - fetch fresh each time

### Task 3: Subscribe to User Changes
- Listen for HA user/auth events
- Force `location.reload()` on user role change

### Task 4: Add Cache Busting
- Add timestamp to JS URLs: `?v=2.3.1&t={timestamp}`
- Or use `Cache-Control: no-cache` headers

## Success Criteria

1. Admin demoted to user → sees correct filtered panels (only level 0 hidden)
2. User promoted to admin → sees all panels, full access
3. Changes apply within 2 seconds without manual refresh
4. No console errors

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Page reload disrupts user | Only reload on role change, not permission change |
| Performance impact | Minimal - only fetches panels list once per reload |
| Race conditions | Backend is source of truth, frontend just renders |
