# PRD: Access Denied 頁面優化

## 版本資訊
- **當前版本**: 2.9.21
- **目標版本**: 2.9.22
- **建立日期**: 2026-02-01

---

## 問題摘要

### 問題 1: 頁面載入緩慢（5+ 秒延遲）

**現象**: 用戶導航到被禁止的面板時，需要等待 5 秒以上才能看到「存取被拒絕」頁面。

**根本原因分析**:

1. **`waitForPartialPanelResolver()` 函數設計問題**:
   ```javascript
   function waitForPartialPanelResolver(maxWait = 5000) {
     // 固定 5000ms 超時
     // 每 100ms 輪詢一次
     // 需要穿透 4 層 Shadow DOM
   }
   ```

2. **DOM 遍歷路徑過深**:
   ```
   home-assistant → shadowRoot → home-assistant-main → shadowRoot → ha-drawer → partial-panel-resolver → shadowRoot
   ```

3. **競態條件**: `showAccessDenied()` 在權限檢查後立即調用，但 DOM 結構尚未完全初始化。

4. **`partial-panel-resolver` 的 `shadowRoot` 實際上可能永遠不存在**:
   - Home Assistant 的某些版本或配置下，`partial-panel-resolver` 可能不使用 Shadow DOM
   - 導致函數永遠超時

### 問題 2: 漢堡按鈕無法開啟側邊欄

**現象**: 手機/平板上點擊漢堡按鈕（☰），側邊欄沒有反應。

**根本原因分析**:

1. **事件派發位置錯誤**:
   ```javascript
   _toggleSidebar() {
     this.dispatchEvent(new CustomEvent("hass-toggle-menu", {
       bubbles: true,
       composed: true
     }));
   }
   ```

2. **Standalone 模式下的組件隔離**:
   - `ha-access-denied` 被附加到 `document.body`
   - 事件路徑: `button → ha-access-denied → body`
   - Home Assistant 的側邊欄監聽器在 `home-assistant-main` 內部
   - 事件無法到達監聽器

3. **Shadow DOM 邊界問題**:
   - 側邊欄位於: `home-assistant > shadowRoot > home-assistant-main > shadowRoot > ha-drawer`
   - 事件從 `body` 派發，完全在該樹之外

---

## 技術架構分析

### 當前流程

```
用戶導航到被禁止面板
       ↓
checkCurrentPanelAccess() 檢測權限
       ↓ (權限被拒)
showAccessDenied() 被調用
       ↓
載入 ha-access-denied 組件腳本
       ↓
創建 ha-access-denied 元素
       ↓
waitForPartialPanelResolver(5000) 等待
       ↓ (5秒超時)
使用 standalone 模式
       ↓
附加到 document.body
       ↓
漢堡按鈕無法工作
```

### 問題點識別

| 步驟 | 問題 | 影響 |
|-----|------|-----|
| waitForPartialPanelResolver | 5秒固定超時 | 用戶體驗差 |
| partial-panel-resolver.shadowRoot | 可能不存在 | 永遠超時 |
| standalone 模式 | 組件隔離 | 事件無法傳遞 |
| hass-toggle-menu 事件 | 派發位置錯誤 | 側邊欄無反應 |

---

## 解決方案

### 方案 A: 快速顯示 + 直接操作側邊欄（推薦）

**核心思路**:
1. 不等待 `partial-panel-resolver`，直接使用 standalone 模式
2. 直接操作 `ha-drawer` 元素來切換側邊欄

**優點**:
- 即時顯示（<100ms）
- 側邊欄切換可靠
- 代碼簡化

**實現細節**:

#### 1. 簡化 `showAccessDenied()` - 移除等待邏輯

```javascript
async function showAccessDenied() {
  // 檢查是否已存在
  if (document.querySelector("ha-access-denied")) return;

  // 載入組件
  if (!customElements.get("ha-access-denied")) {
    const script = document.createElement("script");
    script.type = "module";
    script.src = "/local/ha_access_denied.js?v=" + Date.now();
    document.head.appendChild(script);
  }

  // 獲取 DOM 引用
  const haMain = document.querySelector("home-assistant");
  const homeAssistantMain = haMain?.shadowRoot?.querySelector("home-assistant-main");
  const haDrawer = homeAssistantMain?.shadowRoot?.querySelector("ha-drawer");
  const haSidebar = haDrawer?.querySelector("ha-sidebar");

  // 計算側邊欄寬度
  const sidebarWidth = haSidebar?.offsetWidth || 0;

  // 創建並配置組件
  const accessDenied = document.createElement("ha-access-denied");
  accessDenied.setAttribute("standalone", "true");
  if (haMain?.hass) {
    accessDenied.hass = haMain.hass;
  }

  // 定位組件
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

  // 隱藏原有面板
  const partialPanelResolver = haDrawer?.querySelector("partial-panel-resolver");
  if (partialPanelResolver) {
    partialPanelResolver.style.visibility = 'hidden';
  }

  console.log("[SidebarFilter] Access denied displayed immediately (sidebar width: " + sidebarWidth + "px)");
}
```

#### 2. 修改側邊欄切換邏輯 - 直接操作 `ha-drawer`

```javascript
_toggleSidebar() {
  // 方法 1: 直接找到並操作 ha-drawer
  const haMain = document.querySelector("home-assistant");
  const homeAssistantMain = haMain?.shadowRoot?.querySelector("home-assistant-main");
  const haDrawer = homeAssistantMain?.shadowRoot?.querySelector("ha-drawer");

  if (haDrawer) {
    // ha-drawer 有 open 屬性控制側邊欄
    const isOpen = haDrawer.hasAttribute("open") || haDrawer.open;
    if (isOpen) {
      haDrawer.removeAttribute("open");
      haDrawer.open = false;
    } else {
      haDrawer.setAttribute("open", "");
      haDrawer.open = true;
    }
    return;
  }

  // 方法 2: 回退到派發事件到正確的目標
  if (haMain) {
    haMain.dispatchEvent(new CustomEvent("hass-toggle-menu", {
      bubbles: true,
      composed: true
    }));
  }
}
```

#### 3. 監聽側邊欄寬度變化 - 動態調整位置

```javascript
connectedCallback() {
  super.connectedCallback();

  if (this.standalone) {
    this._observeSidebarWidth();
  }
}

_observeSidebarWidth() {
  const updatePosition = () => {
    const haMain = document.querySelector("home-assistant");
    const homeAssistantMain = haMain?.shadowRoot?.querySelector("home-assistant-main");
    const haDrawer = homeAssistantMain?.shadowRoot?.querySelector("ha-drawer");
    const haSidebar = haDrawer?.querySelector("ha-sidebar");

    const width = haSidebar?.offsetWidth || 0;
    this.style.left = width + "px";
  };

  // 初始更新
  updatePosition();

  // 監聽 resize 和 transitionend 事件
  window.addEventListener("resize", updatePosition);

  // MutationObserver 監聽 ha-drawer 的 open 屬性變化
  const haMain = document.querySelector("home-assistant");
  const homeAssistantMain = haMain?.shadowRoot?.querySelector("home-assistant-main");
  const haDrawer = homeAssistantMain?.shadowRoot?.querySelector("ha-drawer");

  if (haDrawer) {
    this._drawerObserver = new MutationObserver(updatePosition);
    this._drawerObserver.observe(haDrawer, { attributes: true, attributeFilter: ["open"] });

    // 監聽 transitionend 以獲取精確的最終寬度
    haDrawer.addEventListener("transitionend", updatePosition);
  }
}

disconnectedCallback() {
  super.disconnectedCallback();
  this._drawerObserver?.disconnect();
}
```

---

### 方案 B: 優化等待邏輯（備選）

如果需要保留嘗試整合到 `partial-panel-resolver` 的邏輯：

#### 1. 減少超時時間並使用更積極的策略

```javascript
function waitForPartialPanelResolver(maxWait = 500) {  // 減少到 500ms
  return new Promise((resolve) => {
    const start = Date.now();
    let resolved = false;
    let attempts = 0;
    const maxAttempts = 10;  // 最多嘗試 10 次

    function check() {
      if (resolved) return;
      attempts++;

      const haMain = document.querySelector("home-assistant");
      const homeAssistantMain = haMain?.shadowRoot?.querySelector("home-assistant-main");
      const haDrawer = homeAssistantMain?.shadowRoot?.querySelector("ha-drawer");
      const resolver = haDrawer?.querySelector("partial-panel-resolver");

      // 檢查 shadowRoot 或 直接子元素
      if (resolver?.shadowRoot || (resolver && resolver.children.length > 0)) {
        resolved = true;
        resolve(resolver.shadowRoot || resolver);
        return;
      }

      if (attempts >= maxAttempts || Date.now() - start > maxWait) {
        resolved = true;
        resolve(null);
        return;
      }

      setTimeout(check, 50);  // 減少到 50ms
    }

    check();
  });
}
```

---

## 實施計畫

### 階段 1: 修改 `ha_sidebar_filter.js`

1. **移除 `waitForPartialPanelResolver()` 函數**
2. **簡化 `showAccessDenied()` 函數**:
   - 移除等待邏輯
   - 直接使用 standalone 模式
   - 立即顯示組件
3. **更新版本註釋**

### 階段 2: 修改 `ha_access_denied.js`

1. **重寫 `_toggleSidebar()` 方法**:
   - 直接操作 `ha-drawer.open` 屬性
   - 回退到派發事件到 `home-assistant` 元素
2. **添加 `_observeSidebarWidth()` 方法**:
   - 監聽側邊欄寬度變化
   - 動態調整組件位置
3. **添加生命週期方法** (`connectedCallback`, `disconnectedCallback`)
4. **更新版本註釋**

### 階段 3: 更新版本號

- `const.py`: `PANEL_VERSION = "2.9.22"`

### 階段 4: 測試驗證

| 測試場景 | 預期結果 |
|---------|---------|
| 桌面版載入速度 | <100ms 顯示 Access Denied |
| 平板版載入速度 | <100ms 顯示 Access Denied |
| 手機版載入速度 | <100ms 顯示 Access Denied |
| 桌面版漢堡按鈕 | 點擊後側邊欄收起/展開 |
| 平板版漢堡按鈕 | 點擊後側邊欄收起/展開 |
| 手機版漢堡按鈕 | 點擊後側邊欄滑入/滑出 |
| 側邊欄展開時的位置 | Access Denied 內容正確偏移 |
| 側邊欄收起時的位置 | Access Denied 內容佔滿寬度 |

---

## 風險評估

| 風險 | 可能性 | 影響 | 緩解措施 |
|-----|-------|-----|---------|
| ha-drawer API 不穩定 | 低 | 高 | 提供多種回退方案 |
| Shadow DOM 結構變更 | 中 | 中 | 使用可選鏈操作符，優雅降級 |
| 事件監聽器洩漏 | 低 | 低 | 在 disconnectedCallback 中清理 |

---

## 驗收標準

1. [ ] Access Denied 頁面在 500ms 內顯示
2. [ ] 漢堡按鈕在所有視口（桌面/平板/手機）都能正常切換側邊欄
3. [ ] 側邊欄展開/收起時，Access Denied 內容位置正確調整
4. [ ] 無 JavaScript 錯誤
5. [ ] 無記憶體洩漏

---

## 附錄: 關鍵代碼位置

### `ha_sidebar_filter.js`
- `waitForPartialPanelResolver()`: 行 197-229
- `showAccessDenied()`: 行 235-340

### `ha_access_denied.js`
- `_toggleSidebar()`: 行 61-66
- `render()`: 行 224-252
