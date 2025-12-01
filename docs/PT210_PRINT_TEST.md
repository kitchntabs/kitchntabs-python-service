# PT-210 / POS58 Thermal Printer Setup & Testing Guide

This document describes how to set up and test the GOOJPRT PT-210 portable thermal printer with the KitchenTabs Python service on **Windows** and **Linux (Raspberry Pi)**.

## Table of Contents

- [PT-210 / POS58 Thermal Printer Setup \& Testing Guide](#pt-210--pos58-thermal-printer-setup--testing-guide)
  - [Table of Contents](#table-of-contents)
  - [Printer Specifications](#printer-specifications)
  - [Windows Setup](#windows-setup)
    - [Driver Installation](#driver-installation)
      - [Prerequisites](#prerequisites)
      - [Installation Steps](#installation-steps)
    - [Quick Start (Windows)](#quick-start-windows)
  - [Linux / Raspberry Pi Setup](#linux--raspberry-pi-setup)
    - [Installation](#installation)
    - [USB Permissions](#usb-permissions)
    - [CUPS Setup (Optional)](#cups-setup-optional)
    - [Quick Start (Linux)](#quick-start-linux)
  - [Test Scripts](#test-scripts)
    - [1. Text Print Test (`pos58_text_test.py`)](#1-text-print-test-pos58_text_testpy)
    - [2. PDF Print Test (`pos58_pdf_test.py`)](#2-pdf-print-test-pos58_pdf_testpy)
    - [3. General Test (`pos58_test.py`)](#3-general-test-pos58_testpy)
    - [4. Linux Test (`pos58_linux_test.py`)](#4-linux-test-pos58_linux_testpy)
  - [Test Results Summary](#test-results-summary)
  - [Print Methods](#print-methods)
    - [1. Raw ESC/POS Commands (Text Only)](#1-raw-escpos-commands-text-only)
    - [2. Windows GDI (Image-based)](#2-windows-gdi-image-based)
    - [3. Linux - Device File (Simplest)](#3-linux---device-file-simplest)
    - [4. Linux - python-escpos](#4-linux---python-escpos)
    - [5. Linux - CUPS](#5-linux---cups)
  - [Common ESC/POS Commands](#common-escpos-commands)
  - [Troubleshooting](#troubleshooting)
    - [Printer Not Found](#printer-not-found)
    - [Print Job Stuck](#print-job-stuck)
    - [Paper Not Feeding](#paper-not-feeding)
    - [Garbled Output](#garbled-output)
    - [Linux: Permission Denied](#linux-permission-denied)
    - [Linux: Device Not Found](#linux-device-not-found)
    - [Linux: libusb Error](#linux-libusb-error)
    - [Raspberry Pi: Slow Printing](#raspberry-pi-slow-printing)
  - [Integration with KitchenTabs](#integration-with-kitchentabs)
  - [Files](#files)
  - [References](#references)
- [Stop kt\_service first](#stop-kt_service-first)
- [Test print using the bundled print service](#test-print-using-the-bundled-print-service)
- [Create venv](#create-venv)
- [Activate and install](#activate-and-install)
- [Test](#test)
- [Deactivate when done](#deactivate-when-done)

## Printer Specifications

| Specification | Value |
|--------------|-------|
| Model | GOOJPRT PT-210 |
| Type | Portable Thermal Printer |
| Print Width | 58mm (48mm printable area) |
| Resolution | 203 DPI |
| Interface | USB |
| USB Vendor ID | 0x0FE6 |
| USB Product ID | 0x811E |
| Windows Driver | POS58ENG |
| Windows Printer Name | POS58 Printer |
| Linux Device | /dev/usb/lp0 |

---

## Windows Setup

### Driver Installation

#### Prerequisites
- Windows 10 or 11
- PT-210 printer connected via USB and powered on

#### Installation Steps

1. **Download the driver** from the GitHub repository:
   - URL: https://github.com/1rfsNet/GOOJPRT-Printer-Driver
   - Navigate to: `Portable Bluetooth printer/MTP-II 58mm Bluetooth Printer/`
   - Download: `POS58Setup_20190329.exe`
   - Direct link: [Download POS58Setup_20190329.exe](https://github.com/1rfsNet/GOOJPRT-Printer-Driver/blob/main/Portable%20Bluetooth%20printer/MTP-II%2058mm%20Bluetooth%20Printer/POS58Setup_20190329.exe)

2. **Run the installer**:
   - Double-click `POS58Setup_20190329.exe`
   - Select **English** as the language
   - Select **USB** as the connection type
   - Click **SEARCH USB** to auto-detect the printer
   - Click **Next** to complete installation

3. **Verify installation**:
   ```powershell
   Get-Printer | Where-Object { $_.Name -like "*POS58*" }
   ```
   
   Expected output:
   ```
   Name           DriverName  PortName
   ----           ----------  --------
   POS58 Printer  POS58ENG    USB002
   ```

### Quick Start (Windows)

```powershell
# Activate the Python environment
& C:/Users/USER/DASH/dash-python-service/pw_env/Scripts/Activate.ps1

# Run text print test (no dependencies required)
python src/pos58_text_test.py

# Run PDF print test (requires Poppler)
python src/pos58_pdf_test.py

# Run interactive test suite
python src/pos58_test.py
```

---

## Linux / Raspberry Pi Setup

The PT-210 printer works on Raspberry Pi (Debian ARM 32-bit/64-bit) using different methods than Windows.

### Installation

```bash
# Update package list
sudo apt-get update

# Install system dependencies
sudo apt-get install -y libusb-1.0-0-dev poppler-utils

# Install Python packages
pip3 install pyusb python-escpos pdf2image pillow
```

### USB Permissions

By default, USB devices require root access. Create a udev rule for non-root access:

```bash
# Create udev rule file
sudo nano /etc/udev/rules.d/99-pos58.rules
```

Add this line:
```
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fe6", ATTRS{idProduct}=="811e", MODE="0666", GROUP="plugdev"
```

Apply the rules:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add your user to plugdev group
sudo usermod -aG plugdev $USER
```

**Quick fix (temporary):**
```bash
sudo chmod 666 /dev/usb/lp0
```

### CUPS Setup (Optional)

CUPS provides print queue management and supports PDF printing directly:

```bash
# Install CUPS
sudo apt-get install -y cups cups-client

# Add user to lpadmin group
sudo usermod -aG lpadmin $USER

# Enable remote access (optional)
sudo cupsctl --remote-any

# Start CUPS
sudo systemctl enable cups
sudo systemctl start cups
```

Access the CUPS web interface at `http://raspberrypi.local:631` to add the printer.

### Quick Start (Linux)

```bash
cd /path/to/dash-python-service

# Show setup instructions
python3 src/pos58_linux_test.py --setup

# Check available print methods
python3 src/pos58_linux_test.py

# Print via device file (simplest method)
python3 src/pos58_linux_test.py --device

# Print via python-escpos USB
python3 src/pos58_linux_test.py --usb

# Print via CUPS
python3 src/pos58_linux_test.py --cups

# Print a PDF file
python3 src/pos58_linux_test.py --pdf ./output/tab_39.pdf

# Quick test (direct)
echo "Hello Raspberry Pi!" > /dev/usb/lp0
```

---

## Test Scripts

### 1. Text Print Test (`pos58_text_test.py`)

**Purpose:** Prints a sample receipt using pure ESC/POS text commands. No image conversion, no external dependencies beyond pywin32.

**Requirements:**
- `pip install pywin32`

**Usage:**
```powershell
python src/pos58_text_test.py
```

**What it prints:**
- KitchenTabs header with store name
- Date and time
- Sample order items with prices
- Subtotal, tax calculation, and total
- Payment information
- Footer with website

**Output Example:**
```
╔════════════════════════════════════════════════╗
║         PT-210 / POS58 TEXT Print Test         ║
╚════════════════════════════════════════════════╝

==================================================
POS58 Text Print Test
==================================================
✅ Printer found: POS58 Printer
Sending text receipt...
✅ Sent 736 bytes to printer
✅ Text receipt printed successfully!

==================================================
RESULT: ✅ PASS
==================================================
```

**Sample Receipt Output:**
```
        KITCHNTABS
        Point of Sale
================================
Date: 2025-11-29
Time: 17:45:30
Receipt #: 174530
--------------------------------
ORDER DETAILS:

2x Burger Classic         $17.98
2x French Fries            $7.00
3x Coca Cola               $7.50
1x Chicken Wings          $12.99
--------------------------------
Subtotal:                 $45.47
Tax (10%):                 $4.55
--------------------------------
TOTAL:                    $50.02
================================

Payment Method: CASH
Amount Paid:              $50.00
Change:                   -$0.02

--------------------------------
   Thank you for your order!

   www.kitchntabs.com

   *** TEXT PRINT TEST ***
      *** SUCCESSFUL ***
```

---

### 2. PDF Print Test (`pos58_pdf_test.py`)

**Purpose:** Converts a PDF file to images and prints them on the thermal printer using Windows GDI. Useful for printing receipts, tickets, or any document generated as PDF.

**Requirements:**
- `pip install pywin32 pillow pdf2image`
- **Poppler** for Windows (PDF to image conversion)
  - Install via Chocolatey: `choco install poppler`
  - Or download from: https://github.com/oschwartz10612/poppler-windows/releases
  - Extract to: `C:\poppler-24.08.0\Library\bin`

**Usage:**
```powershell
# Use default sample PDF (./output/tab_39.pdf)
python src/pos58_pdf_test.py

# Use specific PDF file
python src/pos58_pdf_test.py path/to/receipt.pdf
```

**Output Example:**
```
╔════════════════════════════════════════════════╗
║         PT-210 / POS58 PDF Print Test          ║
╚════════════════════════════════════════════════╝

Checking dependencies...
  ✅ pywin32
  ✅ win32ui
  ✅ pillow
  ✅ pdf2image
  ✅ poppler (C:\poppler-24.08.0\Library\bin)

==================================================
PDF Print Test
==================================================
PDF file: ./output/tab_39.pdf
File size: 17,249 bytes
✅ Printer found: POS58 Printer
Converting PDF to images (DPI: 203)...
✅ Converted to 1 page(s)
Target width: 383 pixels (48mm)

Processing page 1/1...
  Image size: 383x2289 pixels
  Sending to printer...
  ✅ Page 1 printed

✅ PDF printed successfully! (1 page(s))

==================================================
RESULT: ✅ PASS
==================================================
```

**How it works:**
1. Loads the PDF file
2. Converts each page to an image at 203 DPI (thermal printer resolution)
3. Resizes the image to fit the 48mm printable width
4. Converts to grayscale for better thermal printing
5. Sends to printer via Windows GDI

---

### 3. General Test (`pos58_test.py`)

**Purpose:** Interactive test suite with multiple options for testing different print methods.

**Usage:**
```powershell
# Show printer information only
python src/pos58_test.py --info

# Run raw ESC/POS print test
python src/pos58_test.py --raw

# Interactive mode
python src/pos58_test.py
```

**Options:**
| Option | Description |
|--------|-------------|
| `--info` | Display printer information without printing |
| `--raw` | Send raw ESC/POS commands to the printer |
| (no args) | Interactive mode - choose between GDI or ESC/POS test |

---

### 4. Linux Test (`pos58_linux_test.py`)

**Purpose:** Cross-platform test script for Linux/Raspberry Pi with multiple print methods.

**Requirements:**
- `pip3 install pyusb python-escpos pdf2image pillow`
- `sudo apt-get install libusb-1.0-0-dev poppler-utils`

**Usage:**
```bash
# Show setup instructions
python3 src/pos58_linux_test.py --setup

# Auto-detect and test all available methods
python3 src/pos58_linux_test.py

# Print via device file (/dev/usb/lp0)
python3 src/pos58_linux_test.py --device

# Print via python-escpos USB
python3 src/pos58_linux_test.py --usb

# Print via CUPS
python3 src/pos58_linux_test.py --cups

# Print a PDF file
python3 src/pos58_linux_test.py --pdf ./output/tab_39.pdf
```

**Print Methods on Linux:**

| Method | Device | Best For |
|--------|--------|----------|
| Device File | `/dev/usb/lp0` | Simple text, raw ESC/POS |
| python-escpos USB | libusb | Full ESC/POS with images |
| python-escpos File | `/dev/usb/lp0` | ESC/POS without libusb |
| CUPS | Print queue | PDFs, system integration |

---

## Test Results Summary

| Test | File | Platform | Method | Status |
|------|------|----------|--------|--------|
| Text Print | `pos58_text_test.py` | Windows | Raw ESC/POS | ✅ PASS |
| PDF Print | `pos58_pdf_test.py` | Windows | PDF→Image→GDI | ✅ PASS |
| General Test | `pos58_test.py` | Windows | Interactive | ✅ PASS |
| Linux Test | `pos58_linux_test.py` | Linux/RPi | Multi-method | ⏳ To test |

## Print Methods

### 1. Raw ESC/POS Commands (Text Only)

Direct ESC/POS commands provide the best control over the thermal printer:

```python
import win32print

PRINTER_NAME = "POS58 Printer"

# ESC/POS Commands
ESC = b'\x1b'
GS = b'\x1d'
LF = b'\x0a'

data = b''
data += ESC + b'@'          # Initialize
data += ESC + b'a\x01'      # Center align
data += b'Hello World!' + LF
data += ESC + b'E\x01'      # Bold on
data += b'Bold Text' + LF
data += ESC + b'E\x00'      # Bold off
data += LF * 4              # Feed paper
data += GS + b'V\x01'       # Paper cut

# Send to printer
handle = win32print.OpenPrinter(PRINTER_NAME)
job = win32print.StartDocPrinter(handle, 1, ("Test", None, "RAW"))
win32print.StartPagePrinter(handle)
win32print.WritePrinter(handle, data)
win32print.EndPagePrinter(handle)
win32print.EndDocPrinter(handle)
win32print.ClosePrinter(handle)
```

### 2. Windows GDI (Image-based)

For printing images, PDFs, or complex layouts:

```python
import win32ui
from PIL import Image, ImageWin

PRINTER_NAME = "POS58 Printer"

# Create or load an image
img = Image.open("receipt.png")

# Print via GDI
hDC = win32ui.CreateDC()
hDC.CreatePrinterDC(PRINTER_NAME)
hDC.StartDoc("Receipt")
hDC.StartPage()

dib = ImageWin.Dib(img)
dib.draw(hDC.GetHandleOutput(), (0, 0, img.width, img.height))

hDC.EndPage()
hDC.EndDoc()
hDC.DeleteDC()
```

### 3. Linux - Device File (Simplest)

Direct write to the USB device file:

```python
DEVICE_PATH = "/dev/usb/lp0"

# ESC/POS data
data = b'\x1b@'              # Initialize
data += b'Hello Linux!\n'
data += b'\n\n\n'            # Feed paper
data += b'\x1dV\x01'         # Cut

# Write directly to device
with open(DEVICE_PATH, 'wb') as f:
    f.write(data)
```

### 4. Linux - python-escpos

Using the python-escpos library (supports images):

```python
from escpos.printer import File, Usb

# Method A: Via device file
p = File("/dev/usb/lp0")

# Method B: Via USB (requires libusb)
# p = Usb(0x0FE6, 0x811E)

p.text("Hello from python-escpos!\n")
p.image("receipt.png")  # Supports images!
p.cut()
p.close()
```

### 5. Linux - CUPS

Using the system print queue:

```bash
# Print text
echo "Hello CUPS!" | lp -d POS58

# Print PDF
lp -d POS58 receipt.pdf
```

```python
import subprocess

# Print via CUPS from Python
subprocess.run(['lp', '-d', 'POS58', 'receipt.pdf'])
```

## Common ESC/POS Commands

| Command | Hex | Description |
|---------|-----|-------------|
| Initialize | `ESC @` | `1B 40` | Reset printer to defaults |
| Align Left | `ESC a 0` | `1B 61 00` | Left alignment |
| Align Center | `ESC a 1` | `1B 61 01` | Center alignment |
| Align Right | `ESC a 2` | `1B 61 02` | Right alignment |
| Bold On | `ESC E 1` | `1B 45 01` | Enable bold |
| Bold Off | `ESC E 0` | `1B 45 00` | Disable bold |
| Underline On | `ESC - 1` | `1B 2D 01` | Enable underline |
| Underline Off | `ESC - 0` | `1B 2D 00` | Disable underline |
| Double Height | `ESC ! 16` | `1B 21 10` | Double height text |
| Double Width | `ESC ! 32` | `1B 21 20` | Double width text |
| Normal | `ESC ! 0` | `1B 21 00` | Normal text |
| Paper Cut | `GS V 1` | `1D 56 01` | Partial cut |
| Full Cut | `GS V 0` | `1D 56 00` | Full cut |

## Troubleshooting

### Printer Not Found

1. Check USB connection
2. Ensure printer is powered on
3. Verify driver installation in Device Manager
4. Try a different USB port

### Print Job Stuck

1. Clear the print queue:
   ```powershell
   Get-PrintJob -PrinterName "POS58 Printer" | Remove-PrintJob
   ```

2. Restart the Print Spooler:
   ```powershell
   Restart-Service Spooler
   ```

### Paper Not Feeding

- Check paper roll is installed correctly
- Ensure paper sensor is not blocked
- Try power cycling the printer

### Garbled Output

- Verify you're using the correct character encoding (CP437 for ESC/POS)
- Check that ESC/POS commands are properly formatted
- Initialize printer with `ESC @` before sending data

### Linux: Permission Denied

```bash
# Quick fix (temporary)
sudo chmod 666 /dev/usb/lp0

# Permanent fix: Create udev rule
sudo nano /etc/udev/rules.d/99-pos58.rules
# Add: SUBSYSTEM=="usb", ATTRS{idVendor}=="0fe6", ATTRS{idProduct}=="811e", MODE="0666"
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Linux: Device Not Found

```bash
# Check if printer is connected
lsusb | grep -i "0fe6"

# Check device files
ls -la /dev/usb/lp*

# Load usblp kernel module
sudo modprobe usblp
```

### Linux: libusb Error

```bash
# Install libusb development files
sudo apt-get install libusb-1.0-0-dev

# Reinstall pyusb
pip3 install --force-reinstall pyusb
```

### Raspberry Pi: Slow Printing

- Use device file method instead of libusb (faster)
- Reduce DPI for image conversion (150 instead of 203)
- Ensure good USB power supply

## Integration with KitchenTabs

The PT-210/POS58 printer can be used with the KitchenTabs print service by updating the configuration:

```yaml
# config.prod.yaml (Windows)
PRINTER_VENDOR: 0x0FE6
PRINTER_PRODUCT: 0x811E
PRINTER_NAME: "POS58 Printer"
PRINTER_MAX_WIDTH: 384  # 48mm at 203 DPI

# config.prod.yaml (Linux/Raspberry Pi)
PRINTER_DEVICE: "/dev/usb/lp0"
PRINTER_METHOD: "device"  # or "escpos", "cups"
```

## Files

| File | Description | Platform |
|------|-------------|----------|
| `src/pos58_text_test.py` | Text-only print test using raw ESC/POS | Windows |
| `src/pos58_pdf_test.py` | PDF print test using pdf2image and GDI | Windows |
| `src/pos58_test.py` | Interactive test with multiple options | Windows |
| `src/pos58_linux_test.py` | Multi-method print test for Linux | Linux/RPi |
| `src/print_service.py` | KitchenTabs print service | Cross-platform |
| `src/pinoywok/print.py` | Print utility module | Cross-platform |
| `docs/PT210_PRINT_TEST.md` | This documentation file | - |

## References

- [GOOJPRT Printer Driver Repository](https://github.com/1rfsNet/GOOJPRT-Printer-Driver)
- [ESC/POS Command Reference](https://reference.epson-biz.com/modules/ref_escpos/index.php)
- [python-escpos Documentation](https://python-escpos.readthedocs.io/)
- [pywin32 Documentation](https://github.com/mhammond/pywin32)

---

**Last Updated:** November 29, 2025  
**Tested On:** Windows 10, Python 3.11, GOOJPRT PT-210



In raspberry

On newer Raspberry Pi OS (Bookworm), Python packages need to be installed in a virtual environment. But since the KitchnTabs app already has its Python bundled, let's use the bundled print service instead:

Option 1: Use the bundled print_service directly
# Stop kt_service first
pkill -f kt_service

# Test print using the bundled print service
/opt/kitchntabs/resources/python-service/print_service test


# Create venv
python3 -m venv ~/printer_test

# Activate and install
source ~/printer_test/bin/activate
pip install python-escpos pyusb

# Test
python3 -c "
from escpos.printer import Usb
p = Usb(0x0fe6, 0x811e)
p.text('Hello PT-210!\n')
p.cut()
p.close()
print('Success!')
"

# Deactivate when done
deactivate

or: sudo apt install python3-usb python3-escpos


