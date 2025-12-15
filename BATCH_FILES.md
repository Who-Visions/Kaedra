# KAEDRA v0.0.6 - Batch File Reference

## Production Launchers (Python 3.12 - Recommended)

### From `kaedra_v006/` directory:

- **`Launch_Kaedra_v006.bat`** - Full launcher with dependency checking
- **`Launch_Simple.bat`** - Quick launcher
- **`Install_Dependencies.bat`** - Install/update packages

### From `Watchtower/` root:

- **`Launch_Kaedra.bat`** - Auto-navigates to kaedra_v006 and launches
- **`Launch_Kaedra_Simple.bat`** - Simplified root launcher

---

## Test Launchers (Python 3.14 - For Testing Only)

### From `kaedra_v006/` directory:

- **`Launch_Kaedra_v006_py314.bat`** - Full 3.14 test launcher with debug output
- **`Launch_Simple_py314.bat`** - Simple 3.14 test launcher

### From `Watchtower/` root:

- **`Launch_Kaedra_py314_TEST.bat`** - Root 3.14 test launcher

---

## Quick Comparison Test

To test if Python 3.14 has compatibility issues:

### Test 1: Try Python 3.14
```bash
cd kaedra_v006
Launch_Kaedra_v006_py314.bat
```

### Test 2: Try Python 3.12 (if 3.14 fails)
```bash
cd kaedra_v006
Launch_Kaedra_v006.bat
```

If 3.14 fails but 3.12 works, it confirms compatibility issues with Python 3.14.

---

## What Each Launcher Does

### `Launch_Kaedra_v006.bat` (Python 3.12)
- ✅ Checks for Python 3.12 or 3.11
- ✅ Verifies dependencies installed
- ✅ Offers to install missing packages
- ✅ Shows version info
- ✅ **Recommended for production use**

### `Launch_Kaedra_v006_py314.bat` (Python 3.14 TEST)
- ⚠️ Forces Python 3.14
- ⚠️ Shows debug messages
- ⚠️ Warns about compatibility issues
- ⚠️ **For testing only**

### `Launch_Simple.bat` / `Launch_Simple_py314.bat`
- Minimal output
- Quick launch
- Good for when you know everything is set up

### `Install_Dependencies.bat`
- Just installs packages
- Uses Python 3.12 by default
- Run once before first use

---

## Troubleshooting

### "Python 3.14 not found"
You do have 3.14 installed. This means the launcher can't execute it. Try:
```bash
py -3.14 --version
```

### Packages fail to install with 3.14
Some packages may not support Python 3.14 yet. Use 3.12:
```bash
Launch_Kaedra_v006.bat
```

### Import errors
```bash
cd kaedra_v006
Install_Dependencies.bat
```

---

**KAEDRA v0.0.6** | Shadow Tactician | Who Visions LLC
