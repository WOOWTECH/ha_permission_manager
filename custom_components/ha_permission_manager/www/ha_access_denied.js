/**
 * HA Permission Manager - Access Denied Panel
 * Shown when user navigates to a panel they don't have access to
 * v2.9.20 - Added standalone mode with built-in header for hamburger menu
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
    contact: "Contact your administrator if you believe this is an error.",
    menu: "Menu",
  },
  "zh-Hans": {
    accessDenied: "访问被拒绝",
    message: "您没有权限查看此面板。",
    contact: "如果您认为这是一个错误，请联系您的管理员。",
    menu: "菜单",
  },
  "zh-Hant": {
    accessDenied: "存取被拒絕",
    message: "您沒有權限檢視此面板。",
    contact: "如果您認為這是一個錯誤，請聯繫您的管理員。",
    menu: "選單",
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
      standalone: { type: Boolean, reflect: true },
    };
  }

  constructor() {
    super();
    this.standalone = false;
  }

  get _i18n() {
    const lang = this.hass?.language || "en";
    return getI18n(lang);
  }

  _toggleSidebar() {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", {
      bubbles: true,
      composed: true
    }));
  }

  static get styles() {
    return css`
      :host {
        display: flex;
        flex-direction: column;
        min-height: 100%;
        height: 100%;
        background: var(--primary-background-color, #fafafa);
        font-family: var(--paper-font-body1_-_font-family, "Roboto", sans-serif);
        color: var(--primary-text-color, #212121);
        box-sizing: border-box;
      }

      /* Normal mode: center content */
      :host(:not([standalone])) {
        align-items: center;
        justify-content: center;
        padding: 24px;
      }

      /* Standalone mode: has header */
      :host([standalone]) {
        padding: 0;
      }

      /* Header - only visible in standalone mode */
      .header {
        display: none;
        align-items: center;
        height: var(--header-height, 56px);
        padding: 0 16px;
        background: var(--app-header-background-color, var(--primary-color, #03a9f4));
        color: var(--app-header-text-color, var(--text-primary-color, white));
        position: sticky;
        top: 0;
        z-index: 100;
        gap: 12px;
        flex-shrink: 0;
      }

      :host([standalone]) .header {
        display: flex;
      }

      .menu-btn {
        width: 40px;
        height: 40px;
        border: none;
        background: transparent;
        color: inherit;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background 0.2s;
        flex-shrink: 0;
        padding: 0;
      }

      .menu-btn:hover {
        background: rgba(255, 255, 255, 0.1);
      }

      .menu-btn:active {
        background: rgba(255, 255, 255, 0.2);
      }

      .menu-btn svg {
        width: 24px;
        height: 24px;
      }

      .header-title {
        flex: 1;
        font-size: 20px;
        font-weight: 500;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: inherit;
      }

      /* Content area */
      .content {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 24px;
      }

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
        line-height: 1.5;
      }

      /* Mobile responsive */
      @media (max-width: 600px) {
        .header {
          height: 48px;
          padding: 0 8px;
        }

        .header-title {
          font-size: 18px;
        }

        .menu-btn {
          width: 36px;
          height: 36px;
        }

        .icon {
          --mdc-icon-size: 72px;
        }

        h1 {
          font-size: 24px;
        }

        .message {
          font-size: 14px;
        }
      }
    `;
  }

  render() {
    const i18n = this._i18n;

    return html`
      <!-- Header - only visible in standalone mode -->
      <div class="header">
        <button
          class="menu-btn"
          @click=${this._toggleSidebar}
          title="${i18n.menu}"
        >
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"/>
          </svg>
        </button>
        <h1 class="header-title">${i18n.accessDenied}</h1>
      </div>

      <!-- Main content -->
      <div class="content">
        <div class="container">
          <ha-icon class="icon" icon="mdi:shield-lock"></ha-icon>
          <h1>${i18n.accessDenied}</h1>
          <p class="message">${i18n.message}</p>
          <p class="contact">${i18n.contact}</p>
        </div>
      </div>
    `;
  }
}

customElements.define("ha-access-denied", HaAccessDenied);
