/**
 * HA Permission Manager - Sidebar Filter
 * Hides panels user doesn't have access to
 *
 * v2.9.16 - Insert Access Denied into partial-panel-resolver to preserve native sidebar
 */
(function() {
  "use strict";

  const PERM_DENY = 0;

  // Sidebar title translations
  const SIDEBAR_TITLES = {
    en: "Permission Manager",
    zh: "權限管理"
  };

  // State
  let originalPanels = null;  // Stored once on first load
  let currentUserId = null;
  let isAdmin = false;
  let initialized = false;
  let lastLanguage = null;

  /**
   * Wait for Home Assistant frontend to be ready
   */
  function waitForHass(maxWait = 15000) {
    return new Promise((resolve) => {
      const start = Date.now();

      function check() {
        const haMain = document.querySelector("home-assistant");
        if (haMain && haMain.hass && haMain.hass.user && haMain.hass.panels) {
          resolve(haMain.hass);
          return;
        }

        if (Date.now() - start > maxWait) {
          console.warn("[SidebarFilter] Timeout waiting for hass");
          resolve(null);
          return;
        }

        setTimeout(check, 100);
      }

      check();
    });
  }

  /**
   * Store original panels on first load (before any filtering)
   */
  async function storeOriginalPanels() {
    if (originalPanels) return originalPanels;

    const hass = await waitForHass();
    if (!hass || !hass.panels) return null;

    // Deep copy the original panels
    originalPanels = JSON.parse(JSON.stringify(hass.panels));
    console.log("[SidebarFilter] Stored", Object.keys(originalPanels).length, "original panels");
    return originalPanels;
  }

  /**
   * Fetch permissions from WebSocket API
   */
  async function fetchPermissions() {
    try {
      const hass = await waitForHass();
      if (!hass) return { permissions: {}, is_admin: false };

      const result = await hass.callWS({
        type: "permission_manager/get_panel_permissions",
      });

      isAdmin = result.is_admin || false;
      currentUserId = result.user_id || null;

      console.log("[SidebarFilter] Fetched permissions: is_admin=" + isAdmin + ", permissions:", result.permissions);

      return {
        permissions: result.permissions || {},
        is_admin: isAdmin,
        user_id: currentUserId,
      };
    } catch (err) {
      console.error("[SidebarFilter] Failed to fetch permissions:", err);
      return { permissions: {}, is_admin: false, user_id: null };
    }
  }

  /**
   * Apply sidebar filtering
   */
  async function applySidebarFilter() {
    console.log("[SidebarFilter] applySidebarFilter called");
    const haMain = document.querySelector("home-assistant");
    if (!haMain || !haMain.hass) {
      console.warn("[SidebarFilter] haMain or hass not available");
      return;
    }

    // Store original panels on first run
    await storeOriginalPanels();
    if (!originalPanels) {
      console.error("[SidebarFilter] Failed to store original panels");
      return;
    }

    // Fetch permissions from backend
    const { permissions, is_admin } = await fetchPermissions();
    console.log("[SidebarFilter] Fetched: is_admin=" + is_admin + ", user_id=" + currentUserId + ", permissions=", JSON.stringify(permissions));

    // Admin users see all panels
    if (is_admin) {
      console.log("[SidebarFilter] Admin user, showing all", Object.keys(originalPanels).length, "panels");
      haMain.hass = { ...haMain.hass, panels: { ...originalPanels } };
      return;
    }

    // Core panels that should NEVER be hidden
    // - profile: user needs access to logout
    const ALWAYS_VISIBLE_PANELS = ["profile"];

    // For non-admin users, filter panels
    // ONLY hide panels that are explicitly set to 0 (DENY)
    // All other panels (undefined, 1, 2, 3) are shown
    const filteredPanels = {};
    let hiddenCount = 0;
    const hiddenPanels = [];

    for (const [panelId, panel] of Object.entries(originalPanels)) {
      // Never hide core panels like profile
      if (ALWAYS_VISIBLE_PANELS.includes(panelId)) {
        filteredPanels[panelId] = panel;
        continue;
      }

      const level = permissions[panelId];

      // Fail-secure: only show panels with explicit permission > 0
      // Hide panels that are undefined or explicitly set to 0
      if (level !== undefined && level > PERM_DENY) {
        filteredPanels[panelId] = panel;
      } else {
        // undefined or 0 = hide
        hiddenPanels.push(panelId);
        hiddenCount++;
      }
    }

    // Apply filtered panels
    haMain.hass = { ...haMain.hass, panels: filteredPanels };
    console.log("[SidebarFilter] Applied filter: showing", Object.keys(filteredPanels).length, "panels, hidden", hiddenCount, ":", hiddenPanels);
  }

  /**
   * Check current URL and block access if denied
   */
  async function checkCurrentPanelAccess() {
    if (isAdmin) return;

    const { permissions } = await fetchPermissions();

    const path = window.location.pathname;

    // Handle root path as lovelace - always allow access (content will be filtered)
    if (path === "/" || path === "") {
      return;
    }

    const match = path.match(/^\/([^\/]+)/);
    if (!match) return;

    const currentPanel = match[1];

    // Skip system paths and always-accessible panels
    if (["local", "api", "auth", "static", "frontend_latest", "frontend_es5", "_my_redirect", "profile"].includes(currentPanel)) {
      return;
    }

    let panelToCheck = currentPanel;

    // Only block if explicitly denied
    if (permissions[panelToCheck] === PERM_DENY) {
      console.log("[SidebarFilter] Access denied for panel:", panelToCheck);
      showAccessDenied();
    }
  }

  /**
   * Wait for partial-panel-resolver's shadowRoot to be ready
   */
  function waitForPartialPanelResolver(maxWait = 5000) {
    return new Promise((resolve) => {
      const start = Date.now();

      function check() {
        const haMain = document.querySelector("home-assistant");
        const homeAssistantMain = haMain?.shadowRoot?.querySelector("home-assistant-main");
        const haDrawer = homeAssistantMain?.shadowRoot?.querySelector("ha-drawer");
        const resolver = haDrawer?.querySelector("partial-panel-resolver");

        if (resolver?.shadowRoot) {
          console.log("[SidebarFilter] partial-panel-resolver ready after", Date.now() - start, "ms");
          resolve(resolver.shadowRoot);
          return;
        }

        if (Date.now() - start > maxWait) {
          console.warn("[SidebarFilter] Timeout waiting for partial-panel-resolver");
          resolve(null);
          return;
        }

        requestAnimationFrame(() => setTimeout(check, 50));
      }

      check();
    });
  }

  /**
   * Show access denied page
   * Inserts into partial-panel-resolver to preserve native sidebar and header
   */
  async function showAccessDenied() {
    if (document.querySelector("ha-access-denied")) return;

    // 載入組件腳本
    if (!customElements.get("ha-access-denied")) {
      const script = document.createElement("script");
      script.type = "module";
      script.src = "/local/ha_access_denied.js?v=" + Date.now();
      document.head.appendChild(script);
    }

    const accessDenied = document.createElement("ha-access-denied");
    const haMain = document.querySelector("home-assistant");
    if (haMain?.hass) {
      accessDenied.hass = haMain.hass;
    }

    // 等待 partial-panel-resolver 就緒
    const shadowRoot = await waitForPartialPanelResolver(5000);

    if (shadowRoot) {
      // 隱藏現有面板
      const panels = shadowRoot.querySelectorAll(':scope > *');
      panels.forEach(p => {
        if (p.tagName !== 'HA-ACCESS-DENIED' && p.tagName !== 'STYLE') {
          p.style.display = 'none';
        }
      });

      // 插入 Access Denied
      shadowRoot.appendChild(accessDenied);
      console.log("[SidebarFilter] Access denied inserted into panel container (native sidebar preserved)");
      return;
    }

    // 回退：使用 standalone 模式（組件自帶頂部欄）
    console.warn("[SidebarFilter] Fallback: using standalone mode with built-in header");
    accessDenied.setAttribute("standalone", "true");

    // 計算側邊欄寬度
    let sidebarWidth = 0;
    try {
      const homeAssistantMain = haMain?.shadowRoot?.querySelector("home-assistant-main");
      const haDrawer = homeAssistantMain?.shadowRoot?.querySelector("ha-drawer");
      const haSidebar = haDrawer?.querySelector("ha-sidebar");

      if (haSidebar) {
        const actualWidth = haSidebar.offsetWidth;
        if (actualWidth > 0) {
          sidebarWidth = actualWidth;
        }
      }
    } catch (e) {
      console.warn("[SidebarFilter] Could not detect sidebar width:", e);
    }

    // standalone 模式：top 從 0 開始（組件自己渲染頂部欄）
    accessDenied.style.cssText = `
      position: fixed;
      top: 0;
      left: ${sidebarWidth}px;
      right: 0;
      bottom: 0;
      z-index: 100;
      background: var(--primary-background-color, #fafafa);
      overflow: auto;
    `;
    document.body.appendChild(accessDenied);

    // 隱藏原有面板內容
    try {
      const homeAssistantMain = haMain?.shadowRoot?.querySelector("home-assistant-main");
      const haDrawer = homeAssistantMain?.shadowRoot?.querySelector("ha-drawer");
      const partialPanelResolver = haDrawer?.querySelector("partial-panel-resolver");
      if (partialPanelResolver) {
        partialPanelResolver.style.visibility = 'hidden';
      }
    } catch (e) {
      // ignore
    }

    console.log("[SidebarFilter] Access denied overlay mounted (standalone mode, sidebar width: " + sidebarWidth + "px)");
  }

  /**
   * Subscribe to permission changes
   */
  async function subscribeToChanges() {
    const hass = await waitForHass();
    if (!hass || !hass.connection) return;

    // Listen for permission entity changes
    // Entity IDs can be select.perm_* or select.permission_manager_*
    hass.connection.subscribeEvents(async (event) => {
      const entityId = event.data?.entity_id;
      if (!entityId || !(entityId.startsWith("select.perm_") || entityId.startsWith("select.permission_manager_"))) return;

      const newState = event.data?.new_state;
      if (!newState) return;

      // Only care about panel permissions
      if (newState.attributes?.resource_type !== "panel") return;

      // Only care about permissions for the current user
      const permUserId = newState.attributes?.user_id;
      if (!permUserId) {
        console.log("[SidebarFilter] Permission changed but no user_id attribute:", entityId);
        return;
      }

      // Check if this permission change is for the current user
      // If currentUserId is not set yet, try to get it
      if (!currentUserId) {
        const { user_id } = await fetchPermissions();
        if (!user_id) {
          console.warn("[SidebarFilter] Cannot determine current user ID");
          return;
        }
      }

      if (permUserId !== currentUserId) {
        console.log("[SidebarFilter] Permission changed for different user:", permUserId, "current:", currentUserId);
        return;
      }

      console.log("[SidebarFilter] Permission changed for current user:", entityId, "->", newState.state);

      // Small delay to ensure state is fully propagated
      await new Promise(r => setTimeout(r, 100));

      // Re-apply filter
      await applySidebarFilter();
      await checkCurrentPanelAccess();
    }, "state_changed");

    // Listen for user_updated events (when admin status changes in HA)
    hass.connection.subscribeEvents(async (event) => {
      console.log("[SidebarFilter] User updated event received:", event.data);

      // Check if current user's admin status changed
      const oldIsAdmin = isAdmin;
      const { is_admin } = await fetchPermissions();

      if (oldIsAdmin !== is_admin) {
        console.log("[SidebarFilter] Admin status changed via user_updated:", oldIsAdmin, "->", is_admin);
        // Force reload to reset all state
        location.reload();
        return;
      }

      // Even if admin status didn't change, re-apply filter in case permissions changed
      await applySidebarFilter();
    }, "user_updated");

    // Listen for auth events (login/logout, permission changes)
    hass.connection.subscribeEvents(async (event) => {
      console.log("[SidebarFilter] Auth event received:", event.data);

      // Re-check admin status and permissions
      const oldIsAdmin = isAdmin;
      const { is_admin } = await fetchPermissions();

      if (oldIsAdmin !== is_admin) {
        console.log("[SidebarFilter] Admin status changed via auth event:", oldIsAdmin, "->", is_admin);
        location.reload();
        return;
      }

      await applySidebarFilter();
    }, "homeassistant_auth_updated");

    // Listen for lovelace dashboard changes (create/delete)
    hass.connection.subscribeEvents(async (event) => {
      const action = event.data?.action;
      console.log("[SidebarFilter] Lovelace updated event:", action, event.data);

      if (action === "create" || action === "delete") {
        // Wait a bit for backend to create/remove permission entities
        await new Promise(r => setTimeout(r, 500));

        // Refresh originalPanels from current hass.panels
        const haMain = document.querySelector("home-assistant");
        if (haMain && haMain.hass && haMain.hass.panels) {
          originalPanels = JSON.parse(JSON.stringify(haMain.hass.panels));
          console.log("[SidebarFilter] Refreshed originalPanels:", Object.keys(originalPanels).length, "panels");
        }

        // Re-apply filter with new permissions
        await applySidebarFilter();
      }
    }, "lovelace_updated");

    // Also poll every 5 seconds as fallback (reduced from original)
    setInterval(async () => {
      const oldIsAdmin = isAdmin;
      const { is_admin } = await fetchPermissions();

      if (oldIsAdmin !== is_admin) {
        console.log("[SidebarFilter] Admin status changed (poll):", oldIsAdmin, "->", is_admin);
        location.reload();
      }
    }, 5000);

    // Listen for language changes via core_config_updated event
    hass.connection.subscribeEvents(async (event) => {
      console.log("[SidebarFilter] Core config updated event received");

      // Get current language from hass object (more reliable than event data)
      const haMain = document.querySelector("home-assistant");
      const newLanguage = haMain?.hass?.language || "en";

      // Skip if language hasn't changed
      if (newLanguage === lastLanguage) {
        return;
      }

      console.log("[SidebarFilter] Language changed:", lastLanguage, "->", newLanguage);
      lastLanguage = newLanguage;

      // Update sidebar title via DOM manipulation (more reliable than hass.panels)
      updateSidebarTitle();
    }, "core_config_updated");

    console.log("[SidebarFilter] Subscribed to changes (state_changed, user_updated, auth, lovelace_updated, core_config_updated)");
  }

  /**
   * Update sidebar title based on current language
   * Returns true if successfully updated, false otherwise
   */
  function updateSidebarTitle() {
    const hass = document.querySelector("home-assistant")?.hass;
    if (!hass) {
      return false;
    }

    const lang = hass.language || "en";
    const title = lang.startsWith("zh") ? SIDEBAR_TITLES.zh : SIDEBAR_TITLES.en;

    // Traverse Shadow DOM to find sidebar items
    const haMain = document.querySelector("home-assistant");
    if (!haMain?.shadowRoot) return false;

    const homeAssistantMain = haMain.shadowRoot.querySelector("home-assistant-main");
    if (!homeAssistantMain?.shadowRoot) return false;

    const haDrawer = homeAssistantMain.shadowRoot.querySelector("ha-drawer");
    if (!haDrawer) return false;

    // Try shadowRoot first, then direct query (HA version differences)
    let haSidebar = haDrawer.shadowRoot?.querySelector("ha-sidebar");
    if (!haSidebar) {
      haSidebar = haDrawer.querySelector("ha-sidebar");
    }
    if (!haSidebar?.shadowRoot) return false;

    // Find the sidebar navigation items
    const paperListbox = haSidebar.shadowRoot.querySelector("paper-listbox");
    if (!paperListbox) return false;

    const items = paperListbox.querySelectorAll("a");
    let updated = false;

    items.forEach(item => {
      const href = item.getAttribute("href");
      if (href === "/ha_permission_manager") {
        const textSpan = item.querySelector(".item-text");
        if (textSpan && textSpan.textContent !== title) {
          textSpan.textContent = title;
          console.log("[SidebarFilter] ✓ Updated sidebar title to:", title);
          updated = true;
        } else if (textSpan && textSpan.textContent === title) {
          updated = true; // Already correct
        }
      }
    });

    return updated;
  }

  /**
   * Update sidebar title by modifying hass.panels data model
   * This triggers HA's reactive UI update automatically
   */
  function updateSidebarTitleViaHass(lang) {
    const haMain = document.querySelector("home-assistant");
    if (!haMain?.hass?.panels) {
      console.log("[SidebarFilter] updateSidebarTitleViaHass: hass.panels not ready");
      return false;
    }

    const panel = haMain.hass.panels.ha_permission_manager;
    if (!panel) {
      console.log("[SidebarFilter] updateSidebarTitleViaHass: panel not found");
      return false;
    }

    const title = (lang && lang.startsWith("zh")) ? SIDEBAR_TITLES.zh : SIDEBAR_TITLES.en;

    // Only update if title actually changed
    if (panel.title === title) {
      console.log("[SidebarFilter] Sidebar title already correct:", title);
      return true;
    }

    // Update the panel data model - this triggers HA's reactive update
    const updatedPanels = { ...haMain.hass.panels };
    updatedPanels.ha_permission_manager = { ...panel, title: title };

    // Trigger reactive update by assigning new hass object
    haMain.hass = { ...haMain.hass, panels: updatedPanels };

    console.log("[SidebarFilter] ✓ Updated sidebar title via hass.panels:", title);
    return true;
  }

  /**
   * Initialize sidebar title with retry mechanism
   * Uses DOM manipulation directly (updateSidebarTitleViaHass doesn't work for title updates)
   */
  function initSidebarTitle() {
    let attempts = 0;
    const maxAttempts = 30;

    // 嘗試立即更新（使用 DOM 操作）
    if (updateSidebarTitle()) {
      console.log("[SidebarFilter] Sidebar title updated on first attempt");
      return;
    }

    // 重試機制
    const interval = setInterval(() => {
      attempts++;
      if (updateSidebarTitle()) {
        console.log("[SidebarFilter] Sidebar title updated after", attempts, "attempts");
        clearInterval(interval);
      } else if (attempts >= maxAttempts) {
        console.log("[SidebarFilter] Sidebar title update failed after", maxAttempts, "attempts");
        clearInterval(interval);
      }
    }, 2000);
  }

  /**
   * Watch for navigation
   */
  function watchNavigation() {
    window.addEventListener("popstate", () => checkCurrentPanelAccess());

    document.addEventListener("click", (e) => {
      const link = e.target.closest("a");
      if (link && link.href && link.href.startsWith(window.location.origin)) {
        setTimeout(() => checkCurrentPanelAccess(), 150);
      }
    });

    const originalPushState = history.pushState;
    history.pushState = function(...args) {
      originalPushState.apply(this, args);
      setTimeout(() => checkCurrentPanelAccess(), 150);
    };
  }

  /**
   * Initialize
   */
  async function init() {
    if (initialized) return;
    initialized = true;

    console.log("[SidebarFilter] Initializing v2.9.9");

    // Wait a bit for HA to fully load
    await new Promise(r => setTimeout(r, 500));

    // Initialize lastLanguage from current hass state
    const hass = await waitForHass();
    if (hass) {
      lastLanguage = hass.language || "en";
      console.log("[SidebarFilter] Initial language:", lastLanguage);
    }

    await applySidebarFilter();
    watchNavigation();
    await subscribeToChanges();
    await checkCurrentPanelAccess();

    // Initialize sidebar title - prefer hass.panels method, fallback to DOM
    if (!updateSidebarTitleViaHass(lastLanguage)) {
      initSidebarTitle(); // Fallback to DOM manipulation
    }

    console.log("[SidebarFilter] Initialization complete");
  }

  // Start when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    // Small delay to ensure HA is ready
    setTimeout(init, 500);
  }

  // Expose for debugging
  window.__permissionManagerSidebar = {
    refresh: applySidebarFilter,
    getOriginalPanels: () => originalPanels,
    getState: () => ({ isAdmin, currentUserId, initialized, lastLanguage }),
    updateSidebarTitle: updateSidebarTitle,
    updateSidebarTitleViaHass: updateSidebarTitleViaHass,
    initSidebarTitle: initSidebarTitle,
  };
})();
