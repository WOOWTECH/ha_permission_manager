# PRD: 修復 Access Denied 頁面問題 v2

## 問題描述

### 問題 1: 漢堡按鈕邏輯混亂
**現象**：桌面版本有兩個漢堡按鈕（HA 原生的和 Access Denied 頁面的），操作邏輯很奇怪，無法單純用其中一個簡單開關側邊欄。

**根本原因分析**：
1. **HA 原生漢堡按鈕**：控制 `ha-sidebar.expanded` 屬性（255px ↔ 56px 圖標模式）
2. **我們的漢堡按鈕**：嘗試控制相同的屬性，但判斷邏輯可能有問題
3. 兩個按鈕操作同一個狀態，但初始狀態判斷可能不一致

**解決方案**：
- **移除我們的漢堡按鈕**：當 Access Denied 插入到 `partial-panel-resolver` 時，不需要自己的 header
- 如果必須使用 standalone 模式，則隱藏我們的漢堡按鈕（桌面模式下），只在手機/平板模式顯示

---

### 問題 2: 導航後頁面不更新
**現象**：在 Access Denied 頁面點選側邊欄的其他 panel，URL 已經跳轉但頁面內容沒有更新（還是顯示 Access Denied）。

**根本原因分析**：
1. Access Denied 元素沒有被移除
2. `checkCurrentPanelAccess()` 在導航時被呼叫，但：
   - 如果新面板有權限 → 應該移除 Access Denied
   - 如果新面板沒有權限 → Access Denied 已存在，跳過
3. 原有面板內容被隱藏（`display: none`），導航後沒有恢復

**解決方案**：
1. 當用戶導航到有權限的面板時，移除 Access Denied 元素
2. 恢復原有面板內容的顯示
3. 新增 `hideAccessDenied()` 函數處理清理工作

---

## 實施計劃

### Step 1: 新增 hideAccessDenied() 函數
在 `ha_sidebar_filter.js` 中新增函數：
```javascript
function hideAccessDenied() {
  // 移除 Access Denied 元素
  const accessDeniedInResolver = ...
  const accessDeniedInBody = ...

  // 恢復 partial-panel-resolver 中隱藏的內容
  ...
}
```

### Step 2: 修改 checkCurrentPanelAccess()
當面板有權限時，呼叫 `hideAccessDenied()`：
```javascript
async function checkCurrentPanelAccess() {
  // ... 現有邏輯 ...

  if (permissions[panelToCheck] === PERM_DENY) {
    showAccessDenied();
  } else {
    // 新增：如果有權限，移除 Access Denied
    hideAccessDenied();
  }
}
```

### Step 3: 簡化 Access Denied 組件
移除 standalone 模式的漢堡按鈕邏輯：
- 桌面模式：不顯示 header（使用 HA 原生側邊欄）
- 手機/平板模式：顯示 header 但漢堡按鈕使用正確的邏輯

或者更簡單：**完全移除 standalone 模式**，確保一定插入到 `partial-panel-resolver`。

### Step 4: 確保正確插入到 partial-panel-resolver
如果 `partial-panel-resolver` 在首次呼叫時不存在，使用 MutationObserver 等待它出現。

---

## 關鍵文件

1. `/custom_components/ha_permission_manager/www/ha_sidebar_filter.js`
   - 新增 `hideAccessDenied()` 函數
   - 修改 `checkCurrentPanelAccess()`
   - 改進 `showAccessDenied()` 的 DOM 插入邏輯

2. `/custom_components/ha_permission_manager/www/ha_access_denied.js`
   - 移除或簡化 standalone 模式
   - 移除複雜的漢堡按鈕邏輯

3. `/custom_components/ha_permission_manager/const.py`
   - 更新版本號到 2.9.26

---

## 驗證清單

- [ ] 桌面版：只有一個漢堡按鈕（HA 原生的），能正常開關側邊欄
- [ ] 桌面版：側邊欄下拉選單（個人設定/待辦事項）正常顯示
- [ ] 導航測試：從 Access Denied 頁面點擊有權限的面板，頁面正確更新
- [ ] 導航測試：從有權限的面板點擊無權限的面板，顯示 Access Denied
- [ ] 手機版：漢堡按鈕能正常開關側邊欄（如果需要 standalone 模式）
