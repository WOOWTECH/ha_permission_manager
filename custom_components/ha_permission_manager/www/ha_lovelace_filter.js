/**
 * HA Permission Manager - Lovelace Filter
 * Hides dashboard content for users with restricted permissions
 *
 * v2.7.9 - Fixed permission check logic
 */
(function() {
  "use strict";

  const PERM_DENY = 0;

  // State
  let permissions = null;
  let isAdmin = false;
  let initialized = false;
  let contentHidden = false;
  let hideAttempts = 0;

  /**
   * Wait for Home Assistant frontend to be ready
   */
  function waitForHass(maxWait = 15000) {
    return new Promise((resolve) => {
      const start = Date.now();

      function check() {
        const haMain = document.querySelector("home-assistant");
        if (haMain && haMain.hass && haMain.hass.user) {
          resolve(haMain.hass);
          return;
        }

        if (Date.now() - start > maxWait) {
          console.warn("[LovelaceFilter] Timeout waiting for hass");
          resolve(null);
          return;
        }

        setTimeout(check, 100);
      }

      check();
    });
  }

  /**
   * Fetch all permissions from WebSocket API
   */
  async function fetchAllPermissions() {
    try {
      const hass = await waitForHass();
      if (!hass) return null;

      const result = await hass.callWS({
        type: "permission_manager/get_all_permissions",
      });

      isAdmin = result.is_admin || false;
      permissions = result;

      console.log("[LovelaceFilter] v2.7.9 Fetched permissions:", {
        is_admin: isAdmin,
        panels: result.panels,
        areas: result.areas,
        labels: result.labels,
      });

      return result;
    } catch (err) {
      console.error("[LovelaceFilter] Failed to fetch permissions:", err);
      return null;
    }
  }

  /**
   * Check if user should see lovelace content
   * Returns TRUE if content should be VISIBLE
   */
  function shouldShowContent() {
    // Admin always sees everything
    if (isAdmin) {
      console.log("[LovelaceFilter] Admin user - show content");
      return true;
    }

    // No permissions loaded yet - fail-secure: hide content
    if (!permissions) {
      console.log("[LovelaceFilter] No permissions loaded - hide content (fail-secure)");
      return false;
    }

    // Check lovelace panel permission specifically
    // The panel key could be "lovelace" or other variants
    const panelKeys = Object.keys(permissions.panels || {});
    console.log("[LovelaceFilter] Panel keys:", panelKeys);

    // Find lovelace permission
    let lovelaceLevel = null;
    for (const key of panelKeys) {
      if (key === "lovelace" || key.includes("lovelace")) {
        lovelaceLevel = permissions.panels[key];
        console.log(`[LovelaceFilter] Found lovelace key "${key}" with level ${lovelaceLevel}`);
        break;
      }
    }

    // If lovelace permission is 0 (DENY), hide content
    if (lovelaceLevel !== null && lovelaceLevel === PERM_DENY) {
      console.log("[LovelaceFilter] Lovelace permission is DENY - hide content");
      return false;
    }

    // If we have lovelace permission > 0, check areas/labels
    if (lovelaceLevel !== null && lovelaceLevel > PERM_DENY) {
      // Has lovelace access, now check if has any area or label access
      const hasAreaAccess = Object.values(permissions.areas || {}).some(v => v > PERM_DENY);
      const hasLabelAccess = Object.values(permissions.labels || {}).some(v => v > PERM_DENY);

      console.log(`[LovelaceFilter] lovelace=${lovelaceLevel}, hasAreaAccess=${hasAreaAccess}, hasLabelAccess=${hasLabelAccess}`);

      // If no area and no label access, hide content
      if (!hasAreaAccess && !hasLabelAccess) {
        console.log("[LovelaceFilter] No area/label access - hide content");
        return false;
      }

      return true;
    }

    // Default: fail-secure - hide content if no explicit lovelace permission found
    console.log("[LovelaceFilter] No lovelace permission found - hide content (fail-secure)");
    return false;
  }

  /**
   * Find and hide lovelace content by traversing Shadow DOM
   */
  function hideLovelaceContent() {
    const show = shouldShowContent();

    if (show) {
      removeContentHiding();
      return;
    }

    hideAttempts++;
    console.log(`[LovelaceFilter] Hiding lovelace content (attempt ${hideAttempts})`);

    // Traverse Shadow DOM to find hui-root
    const haMain = document.querySelector("home-assistant");
    if (!haMain || !haMain.shadowRoot) {
      console.log("[LovelaceFilter] No home-assistant shadowRoot");
      return;
    }

    const homeAssistantMain = haMain.shadowRoot.querySelector("home-assistant-main");
    if (!homeAssistantMain || !homeAssistantMain.shadowRoot) {
      console.log("[LovelaceFilter] No home-assistant-main shadowRoot");
      return;
    }

    const haDrawer = homeAssistantMain.shadowRoot.querySelector("ha-drawer");
    if (!haDrawer) {
      console.log("[LovelaceFilter] No ha-drawer");
      return;
    }

    const partialPanelResolver = haDrawer.querySelector("partial-panel-resolver");
    if (!partialPanelResolver || !partialPanelResolver.shadowRoot) {
      console.log("[LovelaceFilter] No partial-panel-resolver shadowRoot");
      return;
    }

    const haPanelLovelace = partialPanelResolver.shadowRoot.querySelector("ha-panel-lovelace");
    if (!haPanelLovelace || !haPanelLovelace.shadowRoot) {
      console.log("[LovelaceFilter] No ha-panel-lovelace shadowRoot");
      return;
    }

    const huiRoot = haPanelLovelace.shadowRoot.querySelector("hui-root");
    if (!huiRoot || !huiRoot.shadowRoot) {
      console.log("[LovelaceFilter] No hui-root shadowRoot");
      return;
    }

    // Hide the view content
    const viewContainer = huiRoot.shadowRoot.querySelector("#view");
    if (viewContainer) {
      viewContainer.style.display = "none";
      console.log("[LovelaceFilter] Hidden #view container");
    }

    // Hide the toolbar action items (right side buttons including ... menu)
    const toolbar = huiRoot.shadowRoot.querySelector(".toolbar");
    if (toolbar) {
      // Hide all action items in the toolbar
      const actionItems = toolbar.querySelectorAll("ha-icon-button, ha-button-menu, mwc-icon-button");
      actionItems.forEach(item => {
        item.style.display = "none";
      });
      console.log(`[LovelaceFilter] Hidden ${actionItems.length} toolbar action items`);
    }

    // Also check for app-toolbar and its action items
    const appToolbar = huiRoot.shadowRoot.querySelector("app-toolbar");
    if (appToolbar) {
      const toolbarActions = appToolbar.querySelectorAll('[slot="actionItems"], ha-icon-button, ha-button-menu');
      toolbarActions.forEach(item => {
        item.style.display = "none";
      });
      console.log(`[LovelaceFilter] Hidden ${toolbarActions.length} app-toolbar items`);
    }

    // Add "no access" message if not already there
    let messageContainer = document.getElementById("perm-manager-no-access-msg");
    if (!messageContainer) {
      messageContainer = document.createElement("div");
      messageContainer.id = "perm-manager-no-access-msg";
      messageContainer.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
        font-size: 18px;
        color: var(--secondary-text-color, #666);
        z-index: 1000;
        padding: 20px;
      `;
      messageContainer.innerHTML = `
        <div style="margin-bottom: 10px;">
          <ha-icon icon="mdi:shield-lock" style="--mdc-icon-size: 48px;"></ha-icon>
        </div>
        <div>無可用內容</div>
        <div style="font-size: 14px; margin-top: 8px;">請聯繫管理員獲取訪問權限</div>
      `;
      document.body.appendChild(messageContainer);
    }

    contentHidden = true;
  }

  /**
   * Remove content hiding
   */
  function removeContentHiding() {
    if (!contentHidden) return;

    console.log("[LovelaceFilter] Removing content hiding");

    // Remove message
    const msg = document.getElementById("perm-manager-no-access-msg");
    if (msg) msg.remove();

    // Try to restore view
    const haMain = document.querySelector("home-assistant");
    if (!haMain || !haMain.shadowRoot) return;

    const homeAssistantMain = haMain.shadowRoot.querySelector("home-assistant-main");
    if (!homeAssistantMain || !homeAssistantMain.shadowRoot) return;

    const haDrawer = homeAssistantMain.shadowRoot.querySelector("ha-drawer");
    if (!haDrawer) return;

    const partialPanelResolver = haDrawer.querySelector("partial-panel-resolver");
    if (!partialPanelResolver || !partialPanelResolver.shadowRoot) return;

    const haPanelLovelace = partialPanelResolver.shadowRoot.querySelector("ha-panel-lovelace");
    if (!haPanelLovelace || !haPanelLovelace.shadowRoot) return;

    const huiRoot = haPanelLovelace.shadowRoot.querySelector("hui-root");
    if (!huiRoot || !huiRoot.shadowRoot) return;

    const viewContainer = huiRoot.shadowRoot.querySelector("#view");
    if (viewContainer) {
      viewContainer.style.display = "";
    }

    const toolbar = huiRoot.shadowRoot.querySelector(".toolbar");
    if (toolbar) {
      const actionItems = toolbar.querySelectorAll("ha-icon-button, ha-button-menu, mwc-icon-button");
      actionItems.forEach(item => {
        item.style.display = "";
      });
    }

    const appToolbar = huiRoot.shadowRoot.querySelector("app-toolbar");
    if (appToolbar) {
      const toolbarActions = appToolbar.querySelectorAll('[slot="actionItems"], ha-icon-button, ha-button-menu');
      toolbarActions.forEach(item => {
        item.style.display = "";
      });
    }

    contentHidden = false;
  }

  /**
   * Check if on lovelace page and apply filter
   */
  function checkAndApplyFilter() {
    const path = window.location.pathname;
    const isLovelacePage = path === "/" || path === "" || path.startsWith("/lovelace");

    if (isLovelacePage) {
      hideLovelaceContent();
    } else {
      removeContentHiding();
    }
  }

  /**
   * Subscribe to permission changes
   */
  async function subscribeToChanges() {
    const hass = await waitForHass();
    if (!hass || !hass.connection) return;

    hass.connection.subscribeEvents(async (event) => {
      const entityId = event.data?.entity_id;
      if (!entityId || !entityId.startsWith("select.perm_")) return;

      console.log("[LovelaceFilter] Permission changed, re-checking");
      await fetchAllPermissions();
      checkAndApplyFilter();
    }, "state_changed");

    console.log("[LovelaceFilter] Subscribed to permission changes");
  }

  /**
   * Initialize
   */
  async function init() {
    if (initialized) return;
    initialized = true;

    console.log("[LovelaceFilter] Initializing v2.7.9");

    // Wait for HA to fully load
    await new Promise(r => setTimeout(r, 2000));

    await fetchAllPermissions();
    checkAndApplyFilter();
    await subscribeToChanges();

    // Watch for navigation
    window.addEventListener("popstate", () => {
      setTimeout(checkAndApplyFilter, 500);
    });

    // Re-check periodically (to catch dynamic DOM changes)
    setInterval(checkAndApplyFilter, 1000);

    // Also observe DOM changes to catch when lovelace loads
    const observer = new MutationObserver(() => {
      if (window.location.pathname === "/" || window.location.pathname.startsWith("/lovelace")) {
        checkAndApplyFilter();
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    console.log("[LovelaceFilter] Initialization complete");
  }

  // Start when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    setTimeout(init, 2000);
  }

  // Expose for debugging
  window.__permissionManagerLovelace = {
    refresh: checkAndApplyFilter,
    getPermissions: () => permissions,
    isAdmin: () => isAdmin,
    shouldShowContent: shouldShowContent,
    hideContent: hideLovelaceContent,
    forceHide: () => {
      isAdmin = false;
      permissions = { panels: { lovelace: 0 }, areas: {}, labels: {} };
      hideLovelaceContent();
    }
  };
})();
