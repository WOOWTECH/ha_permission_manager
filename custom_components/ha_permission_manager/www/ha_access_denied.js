/**
 * HA Permission Manager - Access Denied Panel
 * Shown when user navigates to a panel they don't have access to
 * v2.9.26 - Simplified: removed standalone mode, no custom header needed
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
  },
  "zh-Hans": {
    accessDenied: "访问被拒绝",
    message: "您没有权限查看此面板。",
    contact: "如果您认为这是一个错误，请联系您的管理员。",
  },
  "zh-Hant": {
    accessDenied: "存取被拒絕",
    message: "您沒有權限檢視此面板。",
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
    };
  }

  get _i18n() {
    const lang = this.hass?.language || "en";
    return getI18n(lang);
  }

  static get styles() {
    return css`
      :host {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100%;
        height: 100%;
        padding: 24px;
        background: var(--primary-background-color, #fafafa);
        font-family: var(--paper-font-body1_-_font-family, "Roboto", sans-serif);
        color: var(--primary-text-color, #212121);
        box-sizing: border-box;
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
      <div class="container">
        <ha-icon class="icon" icon="mdi:shield-lock"></ha-icon>
        <h1>${i18n.accessDenied}</h1>
        <p class="message">${i18n.message}</p>
        <p class="contact">${i18n.contact}</p>
      </div>
    `;
  }
}

customElements.define("ha-access-denied", HaAccessDenied);
