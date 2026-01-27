# PRD: 儀表板自動同步 Permission Manager

## 1. 概述

當在 Home Assistant 中新增或刪除 Lovelace 儀表板或 Panel 時，Permission Manager 自動同步建立或移除對應的權限實體。

**目標：**
- 新增儀表板 → 自動為所有使用者建立權限實體（預設關閉）
- 刪除儀表板 → 自動移除所有使用者的權限實體

**預設權限規則：**
- 管理員使用者：預設 `"3"` (Edit)，且為 protected（不可修改）
- 普通使用者：預設 `"0"` (Closed)，需管理員手動開啟

---

## 2. 技術架構

### 事件監聽機制

Home Assistant 的 Lovelace 儀表板儲存在 `lovelace_dashboards` registry 中。當新增/刪除儀表板時，會觸發 `lovelace_updated` 事件。

### 需要監聽的事件

| 事件類型 | 觸發時機 | 處理動作 |
|---------|---------|---------|
| `lovelace_updated` | 新增/刪除 Lovelace 儀表板 | 同步權限實體 |
| `component_loaded` | 新 Panel 註冊 | 檢查並同步新 Panel |

### 資料流

```
HA 新增儀表板 → lovelace_updated 事件 → Permission Manager 監聽
    → 呼叫 async_add_entities_for_resource()
    → 為所有使用者建立權限實體（預設值 = 0）
```

---

## 3. 實作細節

### 3.1 新增事件監聽器 (`__init__.py`)

```python
# 新增事件類型
EVENT_LOVELACE_UPDATED = "lovelace_updated"
EVENT_PANELS_UPDATED = "panels_updated"

async def _handle_lovelace_updated(event: Event) -> None:
    """Handle lovelace dashboard changes."""
    action = event.data.get("action")  # "create" | "delete" | "update"
    url_path = event.data.get("url_path")  # dashboard URL (e.g., "security")

    if action == "create":
        # 取得 dashboard 名稱
        resource_id = f"panel_{url_path}"
        resource_name = event.data.get("title", url_path)
        await async_add_entities_for_resource(
            hass, resource_id, resource_name, "panel"
        )
    elif action == "delete":
        resource_id = f"panel_{url_path}"
        await async_remove_entities_for_resource(hass, resource_id)
```

### 3.2 預設權限邏輯 (`select.py`)

修改 `async_add_entities_for_resource()` 確保：
- 管理員使用者：預設 `"3"` (Edit)，且為 protected
- 普通使用者：預設 `"0"` (Closed)

---

## 4. 前端同步 (`ha_sidebar_filter.js`)

**問題：** 新增儀表板後，前端的 `originalPanels` 是在初次載入時快取的，不會自動更新。

**解決方案：** 監聽 `lovelace_updated` 事件，更新 `originalPanels` 並重新套用過濾。

```javascript
// 訂閱 lovelace 儀表板變更
hass.connection.subscribeEvents(async (event) => {
  const action = event.data?.action;
  if (action === "create" || action === "delete") {
    console.log("[SidebarFilter] Dashboard changed, refreshing panels");
    // 重新取得最新 panels
    originalPanels = JSON.parse(JSON.stringify(haMain.hass.panels));
    await applySidebarFilter();
  }
}, "lovelace_updated");
```

---

## 5. 實作步驟

| 步驟 | 檔案 | 描述 |
|-----|------|------|
| 1 | `__init__.py` | 新增 `lovelace_updated` 事件監聽器 |
| 2 | `__init__.py` | 新增 `panels_updated` 事件監聽器（或輪詢檢查） |
| 3 | `select.py` | 確保新資源的預設權限為 `"0"`（普通使用者） |
| 4 | `ha_sidebar_filter.js` | 監聯 `lovelace_updated` 事件，更新 `originalPanels` |
| 5 | `discovery.py` | 確保 `discover_panels()` 正確識別 Lovelace 儀表板 |

---

## 6. 測試案例

| 測試 | 預期結果 |
|-----|---------|
| 新增 Lovelace 儀表板 "Security" | 自動為所有使用者建立 `panel_security` 權限實體，普通使用者預設 `0` |
| 刪除 Lovelace 儀表板 "Security" | 自動移除所有使用者的 `panel_security` 權限實體 |
| 普通使用者登入 | 新增的儀表板不會出現在 sidebar（因為預設 `0`） |
| 管理員開啟權限後 | 使用者可以看到該儀表板 |

---

## 7. 版本資訊

- **目標版本：** v2.9.0
- **建立日期：** 2026-01-25
- **狀態：** 待實作
