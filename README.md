# HA Permission Manager

A Home Assistant custom component that provides granular permission management for users, allowing administrators to control access to areas, labels, panels (dashboards), and other resources.

## Features

- **User-Based Permission Control**: Manage permissions for each user individually
- **Resource Types Supported**:
  - **Areas**: Control access to different areas in your home
  - **Labels**: Manage visibility of labeled entities
  - **Panels/Dashboards**: Control which sidebar panels users can see
  - **Automations & Scripts**: Control access to automations and scripts
  - **Custom Resources**: Define your own custom resources
- **Permission Levels**:
  - `0 - Closed`: Hidden / No Access
  - `1 - View`: Read Only
  - `2 - Limited`: Control entities, no config changes
  - `3 - Edit`: Full Admin access
- **Admin Protection**: Admin users automatically have full access to all resources
- **Sidebar Filtering**: Automatically hides panels from the sidebar based on permissions
- **Access Denied Page**: Shows a friendly message when users try to access restricted panels
- **Real-time Updates**: Permissions are applied immediately when changed
- **Multi-language Support**: English, Simplified Chinese, and Traditional Chinese

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/WOOWTECH/ha_permission_manager` as a custom repository (Category: Integration)
6. Search for "Permission Manager" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/WOOWTECH/ha_permission_manager/releases)
2. Extract the `custom_components/ha_permission_manager` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** -> **Devices & Services** -> **Add Integration**
2. Search for "Permission Manager" and click to add it
3. Follow the setup wizard

Once configured, a new "Permission Manager" panel will appear in your sidebar (visible to admin users only).

## Usage

### Permission Matrix

The Permission Manager panel displays a matrix where:
- **Rows** represent users
- **Columns** represent resources (areas, labels, panels, etc.)
- Each cell contains a permission level selector

### Managing Permissions

1. Navigate to the Permission Manager panel in the sidebar
2. Select a resource type tab (Areas, Labels, Panels, etc.)
3. Use the dropdown selectors to set permission levels for each user-resource combination
4. Changes are saved automatically

### Protected Permissions

Some permissions are protected and cannot be changed:
- Admin users always have full access (`3 - Edit`) to all resources
- The Profile panel is always accessible to all users (required for logout)
- The Permission Manager panel is only accessible to admin users

## Architecture

### Backend Components

- `__init__.py`: Main integration setup, event listeners, panel registration
- `config_flow.py`: Configuration flow for setting up the integration
- `const.py`: Constants, permission levels, and helper functions
- `discovery.py`: Resource discovery (areas, labels, panels, automations, scripts)
- `users.py`: User discovery and management
- `select.py`: Select entity platform for permission entities
- `websocket_api.py`: WebSocket API for frontend communication

### Frontend Components

- `ha_permission_manager.js`: Main admin panel UI (Lit Element)
- `ha_sidebar_filter.js`: Sidebar filtering script (hides restricted panels)
- `ha_access_denied.js`: Access denied page component
- `ha_lovelace_filter.js`: Lovelace dashboard content filtering

## Requirements

- Home Assistant 2026.1.0 or newer
- Admin access to configure the integration

## Troubleshooting

### Panels not hiding

1. Clear your browser cache
2. Reload the Home Assistant page
3. Check the browser console for errors

### Permission changes not taking effect

1. Wait a few seconds for the changes to propagate
2. Refresh the page
3. Check if the user has admin privileges (admins always have full access)

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/WOOWTECH/ha_permission_manager/issues) on GitHub.
