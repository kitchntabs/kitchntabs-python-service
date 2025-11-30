# Cross-Platform Thermal Printing

This document describes the thermal printing system used in the Dash Python Service for printing receipts and order tickets across different platforms.

## Overview

The thermal printing system provides unified printing support across:
- **Windows** (using Windows GDI / win32print)
- **macOS** (using CUPS)
- **Linux x64** (using CUPS)
- **Linux ARM / Raspberry Pi** (using direct USB via pyusb)

The system automatically detects the best available printing method for each platform and falls back to alternatives if the primary method fails.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      print_service.py                        │
│                    (Entry point for printing)                │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      pinoywok/print.py                       │
│              (PDF download and print orchestration)          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                pinoywok/thermal_printer.py                   │
│              (Cross-platform thermal printer class)          │
├─────────────────────────────────────────────────────────────┤
│  Methods:                                                    │
│  ├── win32        (Windows GDI)                             │
│  ├── pyusb        (Direct USB - Raspberry Pi)               │
│  ├── cups         (CUPS printing system)                    │
│  ├── device_file  (/dev/usb/lp0)                           │
│  └── escpos_usb   (python-escpos library)                   │
└─────────────────────────────────────────────────────────────┘
```

## Supported Printers

### Tested Printers

| Printer Model | Vendor ID | Product ID | Notes |
|---------------|-----------|------------|-------|
| EPSON TM-m30 | 0x04b8 | 0x0e20 | Primary production printer |
| POS58 / PT-210 | 0x0FE6 | 0x811E | Budget thermal printer, good for Raspberry Pi |

### Printer Settings

Printer USB IDs are configured in the YAML config files:

```yaml
# EPSON TM-m30
PRINTER_VENDOR: 0x04b8
PRINTER_PRODUCT: 0x0e20

# Or for POS58/PT-210
PRINTER_VENDOR: 0x0FE6
PRINTER_PRODUCT: 0x811E
```

## Print Methods

### 1. Windows GDI (`win32`)

**Platform:** Windows only  
**Dependencies:** `pywin32`

Uses the Windows GDI (Graphics Device Interface) to print through the default Windows printer. This is the most reliable method on Windows as it uses the native printing subsystem.

```python
# Install dependency
pip install pywin32
```

### 2. Direct USB (`pyusb`)

**Platform:** All (recommended for Raspberry Pi)  
**Dependencies:** `pyusb`, `libusb`

Communicates directly with the printer via USB using ESC/POS commands. This bypasses the operating system's print spooler and is the most reliable method for ARM-based systems like Raspberry Pi.

```bash
# Install dependencies
pip install pyusb

# Linux: Install libusb
sudo apt-get install libusb-1.0-0-dev

# macOS: Install libusb
brew install libusb
```

**USB Permissions (Linux):**

Create a udev rule to allow non-root access to the printer:

```bash
# For POS58/PT-210
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0fe6", ATTR{idProduct}=="811e", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/99-thermal-printer.rules

# For EPSON TM-m30
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04b8", ATTR{idProduct}=="0e20", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/99-thermal-printer.rules

# Reload rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add user to plugdev group
sudo usermod -aG plugdev $USER
```

### 3. CUPS (`cups`)

**Platform:** Linux, macOS  
**Dependencies:** CUPS installed on system

Uses the Common UNIX Printing System to send print jobs. This is the standard printing method for Linux and macOS desktop systems.

```bash
# Linux: Install CUPS
sudo apt-get install cups

# Check available printers
lpstat -p

# Set default printer
lpoptions -d "PrinterName"
```

### 4. Device File (`device_file`)

**Platform:** Linux only  
**Dependencies:** None (uses /dev/usb/lp0)

Writes ESC/POS commands directly to the USB device file. This is a fallback method that works when other methods fail.

```bash
# Set permissions
sudo chmod 666 /dev/usb/lp0
```

### 5. python-escpos (`escpos_usb`)

**Platform:** All  
**Dependencies:** `python-escpos`

Uses the python-escpos library for printing. This provides a higher-level API but may have compatibility issues on some systems.

```bash
pip install python-escpos
```

## Method Selection Priority

The system automatically selects the best method based on the platform:

| Platform | Priority Order |
|----------|---------------|
| Windows | win32 → cups |
| Linux ARM (Raspberry Pi) | pyusb → device_file → cups |
| Linux x64 | cups → pyusb |
| macOS | cups |

## Configuration

### Config File Options

```yaml
# Poppler path for PDF conversion
# Windows: Specify full path to poppler binaries
# Linux/Mac: Leave empty to use system poppler-utils
POPPLER_PATH: ""

# Printer USB IDs (hex format)
PRINTER_VENDOR: 0x04b8
PRINTER_PRODUCT: 0x0e20

# Linux device path (for device_file method)
PRINTER_DEVICE_PATH: "/dev/usb/lp0"

# CUPS printer name (optional - uses default if empty)
PRINTER_NAME: ""
```

### Environment Requirements

#### Windows
```
- Python 3.8+
- pywin32
- pillow
- pdf2image
- Poppler for Windows (for PDF conversion)
```

#### Linux (including Raspberry Pi)
```bash
# System packages
sudo apt-get update
sudo apt-get install -y \
    libusb-1.0-0-dev \
    poppler-utils \
    cups

# Python packages
pip install pyusb pillow pdf2image
```

#### macOS
```bash
# System packages
brew install libusb poppler

# Python packages
pip install pyusb pillow pdf2image
```

## Usage

### Programmatic Usage

```python
from pinoywok.thermal_printer import ThermalPrinter

# Initialize with config
printer = ThermalPrinter(config)

# Check printer status
status = printer.get_status()
print(f"Platform: {status['platform']}")
print(f"Recommended method: {status['recommended']}")
print(f"Available methods: {status['methods']}")

# Print a PDF
printer.print_pdf('/path/to/receipt.pdf')

# Print an image
from PIL import Image
img = Image.open('/path/to/image.png')
printer.print_image(img)

# Force specific method
printer.print_pdf('/path/to/receipt.pdf', method='pyusb')

# Run test print
printer.test_print()
```

### Command Line Testing

```bash
# Show printer status
python src/test_thermal_printer.py --status

# Run test print
python src/test_thermal_printer.py

# Print specific PDF
python src/test_thermal_printer.py --pdf /path/to/file.pdf

# Force specific method
python src/test_thermal_printer.py --method pyusb

# Use specific printer IDs
python src/test_thermal_printer.py --vendor 0x0FE6 --product 0x811E
```

## Raspberry Pi Setup Guide

### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    libusb-1.0-0-dev \
    poppler-utils \
    python3-pip
```

### 2. Install Python Packages

```bash
pip3 install pyusb pillow pdf2image
```

### 3. Configure USB Permissions

```bash
# Create udev rule
sudo tee /etc/udev/rules.d/99-thermal-printer.rules << EOF
# POS58/PT-210
SUBSYSTEM=="usb", ATTR{idVendor}=="0fe6", ATTR{idProduct}=="811e", MODE="0666", GROUP="plugdev"
# EPSON TM-m30
SUBSYSTEM=="usb", ATTR{idVendor}=="04b8", ATTR{idProduct}=="0e20", MODE="0666", GROUP="plugdev"
EOF

# Reload rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add user to plugdev group
sudo usermod -aG plugdev $USER

# Logout and login again for group changes to take effect
```

### 4. Verify Printer Detection

```bash
# Check if printer is detected
lsusb | grep -i "0fe6\|04b8"

# Should show something like:
# Bus 001 Device 004: ID 0fe6:811e ICS Advent Parallel Adapter
```

### 5. Test Printing

```bash
cd /path/to/dash-python-service
python3 src/test_thermal_printer.py --status
python3 src/test_thermal_printer.py
```

## Troubleshooting

### Printer Not Found

**Symptom:** `Error: Printer not found (VID:0x0fe6 PID:0x811e)`

**Solutions:**
1. Check USB connection: `lsusb`
2. Verify vendor/product IDs match your printer
3. Check udev rules are loaded: `sudo udevadm control --reload-rules`
4. Try running with sudo: `sudo python3 test_thermal_printer.py`

### Permission Denied

**Symptom:** `Error: Permission denied`

**Solutions:**
1. Check udev rules are in place
2. Verify user is in plugdev group: `groups`
3. Logout and login again after adding to group
4. As a workaround: `sudo chmod 666 /dev/usb/lp0`

### PDF Conversion Failed

**Symptom:** `Error: PDF conversion failed`

**Solutions:**
1. Install poppler-utils: `sudo apt-get install poppler-utils`
2. On Windows, download Poppler and set `POPPLER_PATH` in config
3. Try installing PyMuPDF as fallback: `pip install PyMuPDF`

### Garbled Output / Wrong Characters

**Symptom:** Printer outputs garbage or wrong characters

**Solutions:**
1. Verify printer DPI setting (default: 203)
2. Check printer width setting (default: 384 pixels for 48mm)
3. Try a different print method
4. Ensure image is converted to 1-bit black/white

### GLIBC Errors on Raspberry Pi

**Symptom:** `version GLIBC_2.XX not found`

**Solutions:**
1. Use Buster-compatible binaries for older Raspberry Pi OS
2. Build with `USE_BUSTER_BINARIES=true`
3. See `ELECTRON_BUILD_PROCESS.md` for details

## File Reference

| File | Description |
|------|-------------|
| `src/pinoywok/thermal_printer.py` | Cross-platform thermal printer class |
| `src/pinoywok/print.py` | PDF download and print orchestration |
| `src/print_service.py` | Print service entry point |
| `src/test_thermal_printer.py` | Command-line testing utility |
| `src/pos58_linux_test.py` | Linux-specific POS58 test script |
| `src/pos58_pdf_test.py` | Windows PDF printing test script |

## API Reference

### ThermalPrinter Class

```python
class ThermalPrinter:
    def __init__(self, config=None):
        """Initialize printer with optional config."""
    
    def get_status(self) -> dict:
        """Get printer status and available methods."""
    
    def print_pdf(self, pdf_path: str, method: str = 'auto') -> bool:
        """Print a PDF file."""
    
    def print_image(self, image: Union[Image, str], method: str = 'auto') -> bool:
        """Print a PIL Image or image file."""
    
    def test_print(self) -> bool:
        """Print a test receipt."""
```

### Status Dictionary

```python
{
    'platform': 'linux',           # 'windows', 'darwin', 'linux'
    'is_arm': True,                # True for ARM architecture
    'vendor_id': '0xfe6',          # Printer vendor ID
    'product_id': '0x811e',        # Printer product ID
    'recommended': 'pyusb',        # Recommended print method
    'methods': {
        'win32': False,
        'pyusb': True,
        'escpos_usb': True,
        'escpos_file': False,
        'cups': True,
        'device_file': True
    }
}
```
