# HACS Integration Guide for ha_permission_manager

This guide documents how to make the ha_permission_manager custom component downloadable from HACS (Home Assistant Community Store).

## Table of Contents

1. [Two Installation Paths](#two-installation-paths)
2. [Requirements Overview](#requirements-overview)
3. [Current Project Status](#current-project-status)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Submission to HACS Default](#submission-to-hacs-default)
6. [Checklist](#checklist)

---

## Two Installation Paths

### Path 1: Custom Repository (Quick Start)

Users can install your integration immediately by adding it as a custom repository in HACS:

1. Open HACS in Home Assistant
2. Click the three dots menu → "Custom repositories"
3. Add URL: `https://github.com/WOOWTECH/ha_permission_manager`
4. Category: "Integration"
5. Click "Add"

**Requirements for this path:**
- Valid `manifest.json`
- Proper repository structure
- GitHub releases with version tags

### Path 2: HACS Default Repository (Recommended)

Getting included in the HACS default repository list makes installation easier for users (no custom repo needed). This requires meeting all HACS requirements and submitting a PR.

---

## Requirements Overview

### 1. Repository Structure ✅

The repository must follow this structure:

```
ha_permission_manager/           # Repository root
├── custom_components/           # HACS looks for this!
│   └── ha_permission_manager/   # Your integration folder
│       ├── __init__.py
│       ├── manifest.json
│       └── ...
├── hacs.json                    # HACS metadata
├── README.md
└── ...
```

**Current status:** ✅ Structure is correct. The component is at `ha_permission_manager/` within the repo.

### 2. manifest.json Requirements

Required fields:
```json
{
  "domain": "ha_permission_manager",
  "name": "Permission Manager",
  "version": "2.9.1",
  "documentation": "https://github.com/WOOWTECH/ha_permission_manager",
  "issue_tracker": "https://github.com/WOOWTECH/ha_permission_manager/issues",
  "codeowners": ["@WOOWTECH"],
  "dependencies": ["frontend", "auth"],
  "iot_class": "local_push",
  "homeassistant": "2026.1.0",
  "config_flow": true
}
```

**Current status:** ⚠️ Missing `issue_tracker` field.

### 3. hacs.json File

Create `hacs.json` in the repository root:

```json
{
  "name": "Permission Manager",
  "render_readme": true,
  "homeassistant": "2026.1.0",
  "content_in_root": true
}
```

**Fields explained:**
- `name`: Display name in HACS
- `render_readme`: Show README in HACS UI
- `homeassistant`: Minimum HA version required
- `content_in_root`: Set to `true` because your integration files are directly in `ha_permission_manager/` folder (not nested under `custom_components/`)

**Current status:** ❌ File does not exist.

### 4. GitHub Releases

HACS requires proper GitHub releases with semantic version tags.

**Creating a release:**
1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag version: `v2.9.1` (must match manifest.json version with `v` prefix)
4. Release title: `v2.9.1`
5. Description: Changelog for this version
6. Click "Publish release"

**Current status:** ❌ No releases found.

### 5. GitHub Actions Workflow

Add automated validation to ensure HACS compatibility:

Create `.github/workflows/hacs-validate.yml`:

```yaml
name: HACS Validation

on:
  push:
    branches:
      - main
      - dev
  pull_request:
    branches:
      - main

jobs:
  hacs:
    name: HACS Validation
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: HACS Validation
        uses: hacs/action@main
        with:
          category: integration
```

**Current status:** ❌ Workflow does not exist.

### 6. GitHub Repository Topics

Add these topics to your GitHub repository settings:
- `home-assistant`
- `hacs`
- `home-assistant-custom-component`

**To add topics:**
1. Go to repository main page
2. Click the gear icon next to "About"
3. Add topics in the "Topics" field

**Current status:** ❓ Unknown - check repository settings.

### 7. Home Assistant Brands (Optional)

For a custom icon/logo in Home Assistant, submit to the brands repository:
- Repository: https://github.com/home-assistant/brands
- This is optional but recommended for a polished appearance

---

## Current Project Status

| Requirement | Status | Action Needed |
|-------------|--------|---------------|
| Repository structure | ✅ Pass | None |
| manifest.json | ⚠️ Partial | Add `issue_tracker` field |
| hacs.json | ❌ Missing | Create file |
| GitHub releases | ❌ Missing | Create release v2.9.1 |
| GitHub Actions | ❌ Missing | Add workflow file |
| GitHub topics | ❓ Unknown | Verify and add if needed |
| README.md | ✅ Pass | None |

---

## Step-by-Step Implementation

### Step 1: Update manifest.json

Add the `issue_tracker` field to `ha_permission_manager/manifest.json`:

```json
{
  "domain": "ha_permission_manager",
  "name": "Permission Manager",
  "version": "2.9.1",
  "documentation": "https://github.com/WOOWTECH/ha_permission_manager",
  "issue_tracker": "https://github.com/WOOWTECH/ha_permission_manager/issues",
  "dependencies": ["frontend", "auth"],
  "codeowners": ["@WOOWTECH"],
  "iot_class": "local_push",
  "homeassistant": "2026.1.0",
  "config_flow": true
}
```

### Step 2: Create hacs.json

Create `hacs.json` in the repository root:

```json
{
  "name": "Permission Manager",
  "render_readme": true,
  "homeassistant": "2026.1.0",
  "content_in_root": true
}
```

### Step 3: Create GitHub Actions Workflow

Create `.github/workflows/hacs-validate.yml`:

```yaml
name: HACS Validation

on:
  push:
    branches:
      - main
      - dev
  pull_request:
    branches:
      - main

jobs:
  hacs:
    name: HACS Validation
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: HACS Validation
        uses: hacs/action@main
        with:
          category: integration
```

### Step 4: Create GitHub Release

1. Commit and push all changes to main branch
2. Go to GitHub repository → Releases → "Create a new release"
3. Click "Choose a tag" → Type `v2.9.1` → "Create new tag"
4. Release title: `v2.9.1 - Permission Manager`
5. Description:
   ```markdown
   ## What's New
   - HACS compatibility added
   - [List other changes]

   ## Installation
   ### HACS (Recommended)
   1. Add this repository as a custom repository in HACS
   2. Search for "Permission Manager"
   3. Install and restart Home Assistant

   ### Manual
   Copy `ha_permission_manager` folder to `custom_components/`
   ```
6. Click "Publish release"

### Step 5: Add GitHub Topics

1. Go to repository main page
2. Click gear icon next to "About" section
3. Add topics: `home-assistant`, `hacs`, `home-assistant-custom-component`
4. Save

### Step 6: Verify HACS Validation

After pushing the workflow:
1. Check Actions tab in GitHub
2. Ensure "HACS Validation" workflow passes
3. Fix any issues reported

---

## Submission to HACS Default

Once all requirements are met, submit to the HACS default repository:

### Prerequisites
- All validation checks pass
- At least one GitHub release exists
- Repository is public
- README.md provides clear documentation

### Submission Process

1. **Fork the HACS default repository:**
   ```
   https://github.com/hacs/default
   ```

2. **Add your repository to the integration list:**

   Edit `integration` file and add your repository URL in alphabetical order:
   ```
   WOOWTECH/ha_permission_manager
   ```

3. **Create a Pull Request:**
   - Title: `Add ha_permission_manager`
   - Description: Brief explanation of what your integration does

4. **Wait for Review:**
   - Automated checks will run
   - Maintainers will review
   - Respond to any feedback

### Tips for Approval
- Ensure excellent documentation in README
- Have a clear description of what the integration does
- Include screenshots if applicable
- Be responsive to reviewer feedback

---

## Checklist

Use this checklist before submitting to HACS:

### Repository Setup
- [ ] Repository is public on GitHub
- [ ] Repository structure follows HACS requirements
- [ ] GitHub topics added (`home-assistant`, `hacs`, `home-assistant-custom-component`)

### Required Files
- [ ] `manifest.json` has all required fields including `issue_tracker`
- [ ] `hacs.json` exists in repository root
- [ ] `README.md` provides clear documentation
- [ ] `.github/workflows/hacs-validate.yml` exists

### Releases
- [ ] At least one GitHub release exists
- [ ] Release tag matches version in `manifest.json` (with `v` prefix)
- [ ] Release has meaningful description

### Validation
- [ ] HACS validation GitHub Action passes
- [ ] Integration loads correctly in Home Assistant
- [ ] No errors in Home Assistant logs

### Documentation
- [ ] Installation instructions are clear
- [ ] Configuration steps documented
- [ ] Features/capabilities described
- [ ] Screenshots included (recommended)

---

## Quick Commands

### Validate locally with HACS action (requires Docker)
```bash
docker run --rm -v $(pwd):/github/workspace ghcr.io/hacs/action:main
```

### Check manifest.json syntax
```bash
python -c "import json; json.load(open('ha_permission_manager/manifest.json'))"
```

### Check hacs.json syntax
```bash
python -c "import json; json.load(open('hacs.json'))"
```

---

## Resources

- [HACS Documentation](https://hacs.xyz/)
- [HACS Developer Documentation](https://hacs.xyz/docs/publish/start)
- [HACS Integration Requirements](https://hacs.xyz/docs/publish/integration)
- [Home Assistant Brands](https://github.com/home-assistant/brands)
- [HACS Default Repository](https://github.com/hacs/default)
