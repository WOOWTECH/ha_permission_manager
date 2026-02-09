# Permission Manager - User Guide
# 權限管理器 - 使用者指南

---

## Table of Contents / 目錄

### English
1. [Introduction](#introduction)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Initial Setup](#initial-setup)
6. [Understanding Permission Levels](#understanding-permission-levels)
7. [Resource Types](#resource-types)
8. [Using the Admin Panel](#using-the-admin-panel)
9. [Protected Permissions](#protected-permissions)
10. [How It Works](#how-it-works)
11. [Troubleshooting & FAQ](#troubleshooting--faq)

### 繁體中文
1. [簡介](#簡介)
2. [功能特色](#功能特色)
3. [系統需求](#系統需求)
4. [安裝方式](#安裝方式)
5. [初始設定](#初始設定)
6. [權限等級說明](#權限等級說明)
7. [資源類型](#資源類型)
8. [管理面板操作](#管理面板操作)
9. [受保護的權限](#受保護的權限)
10. [運作原理](#運作原理)
11. [疑難排解與常見問題](#疑難排解與常見問題)

---

# English Documentation

## Introduction

**Permission Manager** is a custom component for Home Assistant that provides granular, user-based permission control. It allows administrators to control which users can access specific areas, labels, panels, dashboards, automations, scripts, and custom resources in their Home Assistant instance.

### Key Benefits

- **Fine-grained control**: Set permissions per user for each resource
- **Multiple permission levels**: From complete restriction to full admin access
- **Real-time updates**: Permission changes take effect immediately
- **Easy management**: Intuitive admin panel with permission matrix
- **Automatic sync**: Automatically detects new areas, labels, users, and dashboards

---

## Features

- **User-based permissions**: Control access for each individual user
- **Multiple resource types**: Areas, Labels, Panels/Dashboards, Automations, Scripts, Custom resources
- **Four permission levels**: Closed, View, Limited, Edit
- **Admin panel**: Web-based permission management interface
- **Sidebar filtering**: Automatically hide unauthorized panels from users
- **Access denied pages**: Graceful handling when users try to access restricted resources
- **Auto-discovery**: Automatically discovers and tracks new resources
- **Real-time sync**: Changes apply immediately without restart
- **Bilingual support**: English and Traditional Chinese interface

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Home Assistant | 2024.1.0 or newer |
| User Role | Administrator access required for setup |

**Dependencies** (automatically handled):
- `frontend` - For panel registration
- `auth` - For user management

---

## Installation

### Method 1: HACS (Recommended)

HACS (Home Assistant Community Store) is the recommended installation method.

#### Adding as Custom Repository

1. Open **HACS** in your Home Assistant sidebar
2. Click the **three dots menu** (⋮) in the top right
3. Select **"Custom repositories"**
4. Enter the repository URL:
   ```
   https://github.com/WOOWTECH/ha_permission_manager
   ```
5. Select **Category**: `Integration`
6. Click **"Add"**
7. Search for **"Permission Manager"** in HACS
8. Click **"Download"**
9. **Restart Home Assistant**

### Method 2: Manual Installation

1. Download the latest release from [GitHub](https://github.com/WOOWTECH/ha_permission_manager)
2. Extract the `ha_permission_manager` folder
3. Copy it to your Home Assistant `custom_components` directory:
   ```
   config/
   └── custom_components/
       └── ha_permission_manager/
           ├── __init__.py
           ├── manifest.json
           ├── const.py
           ├── select.py
           ├── config_flow.py
           ├── websocket_api.py
           ├── strings.json
           ├── translations/
           └── www/
   ```
4. **Restart Home Assistant**

---

## Initial Setup

After installation, you need to add the integration through the Home Assistant UI:

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"** (bottom right)
3. Search for **"Permission Manager"**
4. Click to add it
5. The configuration is automatic - just confirm the setup

Once set up, you'll see a new **"Permission Manager"** item in your sidebar (admin users only).

---

## Understanding Permission Levels

Permission Manager uses four levels to control access:

| Level | Name | Description |
|-------|------|-------------|
| **0** | Closed | Hidden from user / No access |
| **1** | View | Read-only access - can see but not control |
| **2** | Limited | Can control entities, but cannot change configurations |
| **3** | Edit | Full admin access to the resource |

### Level Details

#### Level 0 - Closed
- Resource is completely hidden from the user
- Panel/dashboard won't appear in sidebar
- Direct URL access shows "Access Denied" page
- Entities in area/label are hidden

#### Level 1 - View
- User can see the resource
- Cannot interact with or control entities
- Good for monitoring-only access

#### Level 2 - Limited
- User can see and control entities
- Cannot modify configurations or settings
- Ideal for family members who need to use but not configure

#### Level 3 - Edit
- Full access to the resource
- Can view, control, and configure
- Equivalent to admin access for that resource

---

## Resource Types

Permission Manager supports six types of resources:

### Areas
Physical locations in your home (Living Room, Kitchen, Bedroom, etc.)
- Controls visibility and access to all entities in that area
- Prefix: `area_`

### Labels
Tags applied to entities for organization
- Controls access to entities with specific labels
- Useful for grouping entities by function (Lights, Security, Climate)
- Prefix: `label_`

### Panels / Dashboards
Sidebar items and Lovelace dashboards
- Controls which dashboards appear in user's sidebar
- Unauthorized dashboards are hidden from sidebar
- Direct URL access shows "Access Denied"
- Prefix: `panel_`

### Automations
Home Assistant automations
- Controls who can view/edit/trigger automations
- Prefix: `automation_`

### Scripts
Home Assistant scripts
- Controls who can view/edit/run scripts
- Prefix: `script_`

### Custom Resources
User-defined resources for special cases
- For resources not covered by other types
- Prefix: `custom_`

---

## Using the Admin Panel

The Permission Manager admin panel provides an intuitive interface for managing permissions.

### Accessing the Panel

1. Click **"Permission Manager"** in your sidebar
   - Or navigate to: `http://your-ha-instance/ha_permission_manager`
2. Only administrators can access this panel

### Panel Layout

The admin panel displays a **permission matrix**:
- **Rows**: Users (non-admin users)
- **Columns**: Resources (grouped by type)
- **Cells**: Permission level dropdown (0-3)

### Tab Navigation

Resources are organized into tabs:
- **Areas** - Physical locations
- **Labels** - Entity tags
- **Panels** - Dashboards and sidebar items
- **Automations** - Automation scripts
- **Scripts** - Script entities
- **Custom** - Custom resources

### Changing Permissions

1. Navigate to the appropriate tab
2. Find the user row
3. Find the resource column
4. Select the desired permission level (0-3) from the dropdown
5. Changes are saved automatically

### Search and Filter

- Use the search bar to filter resources by name
- Useful when you have many areas, labels, or dashboards

---

## Protected Permissions

Certain permissions are protected and cannot be changed to ensure system stability and user safety:

### Administrator Protection
- **Admin users always have level 3 (Edit)** for all resources
- Admin permissions cannot be reduced
- This ensures admins always maintain full control

### Profile Panel Protection
- The **Profile** panel is always accessible to all users
- Cannot be set to Closed (level 0)
- Users need access to Profile to log out and manage their account

### Permission Manager Panel
- The **Permission Manager** panel is only visible to administrators
- Non-admin users cannot see or access it regardless of settings
- This is enforced at the panel registration level (`require_admin=True`)

### Why These Protections Exist

1. **Prevent lockouts**: Admins can't accidentally lock themselves out
2. **User safety**: Users can always access their profile to log out
3. **Security**: Only admins can modify permissions

---

## How It Works

### Sidebar Filtering

When a user logs in, Permission Manager:
1. Loads the user's permission settings
2. Filters the sidebar to hide panels with level 0 (Closed)
3. Displays only authorized panels

The filtering happens client-side via JavaScript injection (`ha_sidebar_filter.js`).

### Access Denied Pages

When a user tries to access a restricted resource directly via URL:
1. The system checks the user's permission level
2. If level is 0 (Closed), shows an "Access Denied" page
3. The page informs the user they don't have permission
4. Provides a button to return to the dashboard

### Real-time Updates

Permission changes take effect immediately:
1. Admin changes permission in the panel
2. WebSocket message broadcasts the change
3. User's browser receives the update
4. Sidebar and access controls update without page refresh

### Event Listeners

Permission Manager automatically responds to Home Assistant events:
- **Area created/deleted**: Auto-creates/removes permission entities
- **Label created/deleted**: Auto-creates/removes permission entities
- **User added/removed**: Auto-creates/removes user permission rows
- **Dashboard created/deleted**: Auto-creates/removes panel permissions
- **User promoted to admin**: Auto-upgrades all permissions to level 3

---

## Troubleshooting & FAQ

### Common Issues

#### Panel not appearing in sidebar
1. Ensure you've restarted Home Assistant after installation
2. Check that the integration is properly added in Settings → Devices & Services
3. Verify you're logged in as an administrator

#### Changes not taking effect
1. Try refreshing the browser (Ctrl+F5 / Cmd+Shift+R)
2. Clear browser cache
3. Log out and log back in
4. Restart Home Assistant if issues persist

#### Permission entity not created for a resource
1. The resource may have been created before Permission Manager was installed
2. Remove and re-add the Permission Manager integration to rescan resources

#### User still sees restricted panel
1. Ensure the permission is set to 0 (Closed)
2. Have the user refresh their browser
3. Have the user log out and log back in

### FAQ

**Q: Can I use this to hide entities from users?**
A: Currently, Permission Manager controls access at the area/label/panel level. Individual entity hiding is done through the area and label permissions.

**Q: Does this work with mobile apps?**
A: The sidebar filtering works with the Home Assistant web app. Native mobile apps may have limited support.

**Q: Can non-admin users see they have restricted access?**
A: They see a reduced sidebar and "Access Denied" pages when trying to access restricted resources, but they don't see the full permission matrix.

**Q: How do I grant a user full access to everything?**
A: Either make them an administrator, or set all resources to level 3 (Edit) for that user.

**Q: Will this affect automations and scripts running in the background?**
A: No, Permission Manager only affects UI visibility and user interaction. Backend processes run normally.

**Q: How do I reset all permissions to default?**
A: Remove the Permission Manager integration and re-add it. All permissions will be recreated with default values.

---
---

# 繁體中文文件

## 簡介

**權限管理器 (Permission Manager)** 是一個 Home Assistant 自訂組件，提供精細的使用者權限控制功能。它允許管理員控制哪些使用者可以存取 Home Assistant 中的特定區域、標籤、面板、儀表板、自動化、腳本和自訂資源。

### 主要優點

- **精細控制**：可為每個使用者針對各資源設定權限
- **多層權限等級**：從完全限制到完整管理存取
- **即時更新**：權限變更立即生效
- **簡易管理**：直覺的管理面板與權限矩陣
- **自動同步**：自動偵測新的區域、標籤、使用者和儀表板

---

## 功能特色

- **以使用者為基礎的權限**：為每個使用者個別控制存取權
- **多種資源類型**：區域、標籤、面板/儀表板、自動化、腳本、自訂資源
- **四種權限等級**：關閉、檢視、有限、編輯
- **管理面板**：網頁式權限管理介面
- **側邊欄過濾**：自動對使用者隱藏未授權的面板
- **存取拒絕頁面**：當使用者嘗試存取受限資源時優雅處理
- **自動探索**：自動發現並追蹤新資源
- **即時同步**：變更立即套用，無需重啟
- **雙語支援**：英文和繁體中文介面

---

## 系統需求

| 需求項目 | 版本 |
|----------|------|
| Home Assistant | 2024.1.0 或更新版本 |
| 使用者角色 | 需要管理員權限進行設定 |

**相依套件**（自動處理）：
- `frontend` - 用於面板註冊
- `auth` - 用於使用者管理

---

## 安裝方式

### 方法一：HACS 安裝（推薦）

HACS（Home Assistant 社群商店）是推薦的安裝方式。

#### 新增為自訂儲存庫

1. 在 Home Assistant 側邊欄開啟 **HACS**
2. 點擊右上角的**三點選單** (⋮)
3. 選擇 **「自訂儲存庫」**
4. 輸入儲存庫網址：
   ```
   https://github.com/WOOWTECH/ha_permission_manager
   ```
5. 選擇**類別**：`Integration`（整合）
6. 點擊 **「新增」**
7. 在 HACS 中搜尋 **「Permission Manager」**
8. 點擊 **「下載」**
9. **重新啟動 Home Assistant**

### 方法二：手動安裝

1. 從 [GitHub](https://github.com/WOOWTECH/ha_permission_manager) 下載最新版本
2. 解壓縮 `ha_permission_manager` 資料夾
3. 複製到您的 Home Assistant `custom_components` 目錄：
   ```
   config/
   └── custom_components/
       └── ha_permission_manager/
           ├── __init__.py
           ├── manifest.json
           ├── const.py
           ├── select.py
           ├── config_flow.py
           ├── websocket_api.py
           ├── strings.json
           ├── translations/
           └── www/
   ```
4. **重新啟動 Home Assistant**

---

## 初始設定

安裝完成後，您需要透過 Home Assistant 介面新增整合：

1. 前往**設定** → **裝置與服務**
2. 點擊 **「+ 新增整合」**（右下角）
3. 搜尋 **「Permission Manager」**
4. 點擊新增
5. 設定是自動的 - 只需確認即可

設定完成後，您會在側邊欄看到新的 **「權限管理」** 項目（僅管理員可見）。

---

## 權限等級說明

權限管理器使用四個等級來控制存取：

| 等級 | 名稱 | 說明 |
|------|------|------|
| **0** | 關閉 (Closed) | 對使用者隱藏 / 無法存取 |
| **1** | 檢視 (View) | 唯讀存取 - 可以看但不能控制 |
| **2** | 有限 (Limited) | 可以控制實體，但無法變更設定 |
| **3** | 編輯 (Edit) | 對該資源有完整管理存取權 |

### 等級詳細說明

#### 等級 0 - 關閉
- 資源對使用者完全隱藏
- 面板/儀表板不會出現在側邊欄
- 直接透過網址存取會顯示「存取被拒」頁面
- 該區域/標籤中的實體會被隱藏

#### 等級 1 - 檢視
- 使用者可以看到資源
- 無法與實體互動或控制
- 適合僅需監控的存取權限

#### 等級 2 - 有限
- 使用者可以看到並控制實體
- 無法修改設定或配置
- 適合需要使用但不需要設定的家庭成員

#### 等級 3 - 編輯
- 對資源有完整存取權
- 可以檢視、控制和設定
- 相當於對該資源的管理員存取權

---

## 資源類型

權限管理器支援六種資源類型：

### 區域 (Areas)
您家中的實體位置（客廳、廚房、臥室等）
- 控制該區域中所有實體的可見性和存取權
- 前綴：`area_`

### 標籤 (Labels)
套用於實體的標籤，用於組織管理
- 控制對具有特定標籤的實體的存取
- 適合按功能分組實體（燈光、安全、空調）
- 前綴：`label_`

### 面板/儀表板 (Panels/Dashboards)
側邊欄項目和 Lovelace 儀表板
- 控制哪些儀表板出現在使用者的側邊欄
- 未授權的儀表板會從側邊欄隱藏
- 直接透過網址存取會顯示「存取被拒」
- 前綴：`panel_`

### 自動化 (Automations)
Home Assistant 自動化
- 控制誰可以檢視/編輯/觸發自動化
- 前綴：`automation_`

### 腳本 (Scripts)
Home Assistant 腳本
- 控制誰可以檢視/編輯/執行腳本
- 前綴：`script_`

### 自訂資源 (Custom)
使用者定義的特殊資源
- 用於其他類型未涵蓋的資源
- 前綴：`custom_`

---

## 管理面板操作

權限管理器管理面板提供直覺的權限管理介面。

### 存取面板

1. 點擊側邊欄中的 **「權限管理」**
   - 或導覽至：`http://您的-ha-位址/ha_permission_manager`
2. 只有管理員可以存取此面板

### 面板配置

管理面板顯示一個**權限矩陣**：
- **列**：使用者（非管理員使用者）
- **欄**：資源（按類型分組）
- **儲存格**：權限等級下拉選單 (0-3)

### 分頁導覽

資源被組織成分頁：
- **區域** - 實體位置
- **標籤** - 實體標籤
- **面板** - 儀表板和側邊欄項目
- **自動化** - 自動化腳本
- **腳本** - 腳本實體
- **自訂** - 自訂資源

### 變更權限

1. 導覽到適當的分頁
2. 找到使用者列
3. 找到資源欄
4. 從下拉選單選擇所需的權限等級 (0-3)
5. 變更會自動儲存

### 搜尋和篩選

- 使用搜尋列按名稱篩選資源
- 當您有許多區域、標籤或儀表板時很有用

---

## 受保護的權限

某些權限受到保護，無法變更，以確保系統穩定性和使用者安全：

### 管理員保護
- **管理員使用者對所有資源始終擁有等級 3（編輯）**
- 管理員權限無法被降低
- 這確保管理員始終保持完整控制

### 個人檔案面板保護
- **個人檔案**面板對所有使用者始終可存取
- 不能設定為關閉（等級 0）
- 使用者需要存取個人檔案來登出和管理他們的帳戶

### 權限管理器面板
- **權限管理器**面板僅對管理員可見
- 無論設定如何，非管理員使用者都無法看到或存取它
- 這在面板註冊層級強制執行（`require_admin=True`）

### 為什麼需要這些保護

1. **防止鎖定**：管理員不會意外將自己鎖在外面
2. **使用者安全**：使用者始終可以存取個人檔案來登出
3. **安全性**：只有管理員可以修改權限

---

## 運作原理

### 側邊欄過濾

當使用者登入時，權限管理器：
1. 載入使用者的權限設定
2. 過濾側邊欄以隱藏等級 0（關閉）的面板
3. 僅顯示已授權的面板

過濾透過 JavaScript 注入在客戶端進行（`ha_sidebar_filter.js`）。

### 存取被拒頁面

當使用者嘗試直接透過網址存取受限資源時：
1. 系統檢查使用者的權限等級
2. 如果等級為 0（關閉），顯示「存取被拒」頁面
3. 頁面告知使用者他們沒有權限
4. 提供返回儀表板的按鈕

### 即時更新

權限變更立即生效：
1. 管理員在面板中變更權限
2. WebSocket 訊息廣播變更
3. 使用者的瀏覽器接收更新
4. 側邊欄和存取控制無需重新整理頁面即可更新

### 事件監聽器

權限管理器自動回應 Home Assistant 事件：
- **區域建立/刪除**：自動建立/移除權限實體
- **標籤建立/刪除**：自動建立/移除權限實體
- **使用者新增/移除**：自動建立/移除使用者權限列
- **儀表板建立/刪除**：自動建立/移除面板權限
- **使用者提升為管理員**：自動將所有權限升級為等級 3

---

## 疑難排解與常見問題

### 常見問題

#### 面板未出現在側邊欄
1. 確保安裝後已重新啟動 Home Assistant
2. 檢查整合是否已在「設定 → 裝置與服務」中正確新增
3. 確認您是以管理員身份登入

#### 變更未生效
1. 嘗試重新整理瀏覽器（Ctrl+F5 / Cmd+Shift+R）
2. 清除瀏覽器快取
3. 登出並重新登入
4. 如果問題持續，重新啟動 Home Assistant

#### 資源的權限實體未建立
1. 該資源可能在安裝權限管理器之前就已建立
2. 移除並重新新增權限管理器整合以重新掃描資源

#### 使用者仍然看到受限面板
1. 確保權限已設定為 0（關閉）
2. 讓使用者重新整理瀏覽器
3. 讓使用者登出並重新登入

### 常見問題

**問：我可以用這個對使用者隱藏實體嗎？**
答：目前，權限管理器在區域/標籤/面板層級控制存取。個別實體的隱藏是透過區域和標籤權限完成的。

**問：這在行動應用程式上有效嗎？**
答：側邊欄過濾在 Home Assistant 網頁應用程式上有效。原生行動應用程式可能支援有限。

**問：非管理員使用者會看到他們有存取限制嗎？**
答：他們會看到縮減的側邊欄，並在嘗試存取受限資源時看到「存取被拒」頁面，但他們看不到完整的權限矩陣。

**問：如何授予使用者對所有內容的完整存取權？**
答：要麼將他們設為管理員，要麼為該使用者將所有資源設定為等級 3（編輯）。

**問：這會影響在背景執行的自動化和腳本嗎？**
答：不會，權限管理器只影響 UI 可見性和使用者互動。後端程序正常執行。

**問：如何將所有權限重設為預設值？**
答：移除權限管理器整合並重新新增。所有權限將使用預設值重新建立。

---

## Support / 技術支援

- **GitHub Issues**: [https://github.com/WOOWTECH/ha_permission_manager/issues](https://github.com/WOOWTECH/ha_permission_manager/issues)
- **Documentation / 文件**: [https://github.com/WOOWTECH/ha_permission_manager](https://github.com/WOOWTECH/ha_permission_manager)

---

*Version 2.9.1 | Home Assistant 2024.1.0+*
