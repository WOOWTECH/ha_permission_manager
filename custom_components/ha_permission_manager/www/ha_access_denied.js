/**
 * HA Permission Manager - Access Denied Panel
 * Shown when user navigates to a panel they don't have access to
 * v2.9.13 - Added custom sidebar overlay
 */
import {
  LitElement,
  html,
  css,
} from "https://unpkg.com/lit@2.8.0/index.js?module";

// Internationalization
const I18N = {
  en: {
    accessDenied: "Access Denied",
    message: "You don't have permission to view this panel.",
    returnHome: "Go to Profile",
    contact: "Contact your administrator if you believe this is an error.",
  },
  "zh-Hans": {
    accessDenied: "访问被拒绝",
    message: "您没有权限查看此面板。",
    returnHome: "前往個人設定",
    contact: "如果您认为这是一个错误，请联系您的管理员。",
  },
  "zh-Hant": {
    accessDenied: "存取被拒絕",
    message: "您沒有權限檢視此面板。",
    returnHome: "前往個人設定",
    contact: "如果您認為這是一個錯誤，請聯繫您的管理員。",
  },
};

const getI18n = (lang) => {
  if (I18N[lang]) return I18N[lang];
  if (lang && lang.startsWith("zh")) return I18N["zh-Hant"];
  return I18N.en;
};

class HaAccessDenied extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      narrow: { type: Boolean },
      panel: { type: Object },
      _sidebarOpen: { type: Boolean, state: true },
      _accessiblePanels: { type: Array, state: true },
    };
  }

  constructor() {
    super();
    this._sidebarOpen = false;
    this._accessiblePanels = [];
  }

  async connectedCallback() {
    super.connectedCallback();
    await this._loadAccessiblePanels();
  }

  get _i18n() {
    const lang = this.hass?.language || "en";
    return getI18n(lang);
  }

  async _loadAccessiblePanels() {
    if (!this.hass) {
      console.log("[AccessDenied] hass not available, using fallback panels");
      this._accessiblePanels = this._getFallbackPanels();
      return;
    }

    try {
      const result = await this.hass.callWS({
        type: "permission_manager/get_panel_permissions",
      });

      const permissions = result.permissions || {};
      const panels = this.hass.panels || {};

      console.log("[AccessDenied] Loaded permissions:", permissions);
      console.log("[AccessDenied] Available panels:", Object.keys(panels));

      // Filter panels user has access to
      this._accessiblePanels = Object.entries(panels)
        .filter(([id, panel]) => {
          // Always show profile
          if (id === "profile") return true;
          // Skip our own panel
          if (id === "ha_permission_manager") return false;
          // Check permission level > 0 (0 = denied)
          const permKey = `panel_${id}`;
          const level = permissions[permKey];
          return level !== undefined && level > 0;
        })
        .map(([id, panel]) => ({
          id,
          title: panel.title || id,
          icon: panel.icon || "mdi:view-dashboard",
          url: `/${panel.url_path || id}`,
        }))
        .sort((a, b) => {
          // Profile at the end
          if (a.id === "profile") return 1;
          if (b.id === "profile") return -1;
          return a.title.localeCompare(b.title);
        });

      console.log("[AccessDenied] Accessible panels:", this._accessiblePanels);

      // Ensure at least profile is available
      if (this._accessiblePanels.length === 0) {
        this._accessiblePanels = this._getFallbackPanels();
      }
    } catch (err) {
      console.error("[AccessDenied] Failed to load permissions:", err);
      this._accessiblePanels = this._getFallbackPanels();
    }
  }

  _getFallbackPanels() {
    return [{
      id: "profile",
      title: "Profile",
      icon: "mdi:account",
      url: "/profile/general",
    }];
  }

  _handleReturnHome() {
    console.log("[AccessDenied] Navigating to /profile/general");
    window.location.href = "/profile/general";
  }

  _toggleSidebar() {
    this._sidebarOpen = !this._sidebarOpen;
    console.log("[AccessDenied] Sidebar toggled:", this._sidebarOpen);
  }

  _closeSidebar() {
    this._sidebarOpen = false;
  }

  _navigateTo(url) {
    console.log("[AccessDenied] Navigating to:", url);
    window.location.href = url;
  }

  static get styles() {
    return css`
      :host {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        background: var(--primary-background-color, #fafafa);
        font-family: var(--paper-font-body1_-_font-family, "Roboto", sans-serif);
        color: var(--primary-text-color, #212121);
        padding: 24px;
        padding-top: 80px;
        box-sizing: border-box;
      }

      /* Top Bar */
      .top-bar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 56px;
        display: flex;
        align-items: center;
        padding: 0 8px;
        background: var(--app-header-background-color, var(--primary-color, #03a9f4));
        color: var(--app-header-text-color, white);
        z-index: 5;
      }

      .menu-btn {
        width: 48px;
        height: 48px;
        border: none;
        background: transparent;
        color: inherit;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background 0.2s;
      }

      .menu-btn:hover {
        background: rgba(255, 255, 255, 0.1);
      }

      .menu-btn svg {
        width: 24px;
        height: 24px;
      }

      /* Sidebar Overlay */
      .sidebar-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s, visibility 0.3s;
        z-index: 10;
      }

      .sidebar-overlay.open {
        opacity: 1;
        visibility: visible;
      }

      /* Sidebar Panel */
      .sidebar-panel {
        position: fixed;
        top: 0;
        left: 0;
        bottom: 0;
        width: 280px;
        max-width: 80vw;
        background: var(--sidebar-background-color, var(--card-background-color, white));
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.2);
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        z-index: 11;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
      }

      .sidebar-panel.open {
        transform: translateX(0);
      }

      /* Sidebar Header */
      .sidebar-header {
        display: flex;
        align-items: center;
        height: 56px;
        padding: 0 16px;
        background: var(--app-header-background-color, var(--primary-color, #03a9f4));
        color: var(--app-header-text-color, white);
        gap: 12px;
        flex-shrink: 0;
      }

      .sidebar-header ha-icon {
        --mdc-icon-size: 24px;
      }

      .sidebar-title {
        font-size: 18px;
        font-weight: 500;
      }

      /* Sidebar Items */
      .sidebar-items {
        flex: 1;
        padding: 8px 0;
        overflow-y: auto;
      }

      .sidebar-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        cursor: pointer;
        transition: background 0.2s;
        text-decoration: none;
        color: var(--primary-text-color, #212121);
        gap: 16px;
      }

      .sidebar-item:hover {
        background: var(--secondary-background-color, rgba(0, 0, 0, 0.05));
      }

      .sidebar-item ha-icon {
        --mdc-icon-size: 24px;
        color: var(--secondary-text-color, #757575);
        flex-shrink: 0;
      }

      .sidebar-item-text {
        font-size: 14px;
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      /* Main Content */
      .container {
        text-align: center;
        max-width: 400px;
      }

      .icon {
        --mdc-icon-size: 96px;
        color: var(--error-color, #db4437);
        margin-bottom: 24px;
      }

      h1 {
        margin: 0 0 16px;
        font-size: 28px;
        font-weight: 500;
        color: var(--primary-text-color, #212121);
      }

      .message {
        font-size: 16px;
        color: var(--secondary-text-color, #757575);
        margin-bottom: 8px;
        line-height: 1.5;
      }

      .contact {
        font-size: 14px;
        color: var(--secondary-text-color, #757575);
        margin-bottom: 32px;
        line-height: 1.5;
      }

      button.action-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 12px 24px;
        background: var(--primary-color, #03a9f4);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
      }

      button.action-btn:hover {
        background: var(--dark-primary-color, #0288d1);
      }

      button.action-btn:focus {
        outline: 2px solid var(--primary-color, #03a9f4);
        outline-offset: 2px;
      }
    `;
  }

  render() {
    const i18n = this._i18n;
    const sidebarOpenClass = this._sidebarOpen ? "open" : "";

    return html`
      <!-- Sidebar Overlay -->
      <div
        class="sidebar-overlay ${sidebarOpenClass}"
        @click=${this._closeSidebar}
      ></div>

      <!-- Sidebar Panel -->
      <div class="sidebar-panel ${sidebarOpenClass}">
        <div class="sidebar-header">
          <ha-icon icon="mdi:home-assistant"></ha-icon>
          <span class="sidebar-title">Home Assistant</span>
        </div>
        <div class="sidebar-items">
          ${this._accessiblePanels.map(panel => html`
            <div class="sidebar-item" @click=${() => this._navigateTo(panel.url)}>
              <ha-icon icon="${panel.icon}"></ha-icon>
              <span class="sidebar-item-text">${panel.title}</span>
            </div>
          `)}
        </div>
      </div>

      <!-- Top Bar -->
      <div class="top-bar">
        <button class="menu-btn" @click=${this._toggleSidebar}>
          <svg viewBox="0 0 24 24"><path fill="currentColor" d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"/></svg>
        </button>
      </div>

      <!-- Main Content -->
      <div class="container">
        <ha-icon class="icon" icon="mdi:shield-lock"></ha-icon>
        <h1>${i18n.accessDenied}</h1>
        <p class="message">${i18n.message}</p>
        <p class="contact">${i18n.contact}</p>
        <button class="action-btn" @click=${this._handleReturnHome}>
          <ha-icon icon="mdi:account-cog"></ha-icon>
          ${i18n.returnHome}
        </button>
      </div>
    `;
  }
}

customElements.define("ha-access-denied", HaAccessDenied);
