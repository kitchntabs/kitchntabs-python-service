#!/usr/bin/env python3
"""
PT-210 / POS58 Print Test for Linux (Raspberry Pi / Debian ARM)

This script provides multiple methods for printing on Linux:
1. python-escpos with USB (requires libusb)
2. python-escpos with /dev/usb/lp0 (file-based)
3. CUPS (Common UNIX Printing System)

For Raspberry Pi 32-bit (armhf), use method 2 or 3.
"""

import os
import sys
import subprocess
from datetime import datetime

# Printer constants
PRINTER_VENDOR = 0x0FE6   # GOOJPRT/PT-210
PRINTER_PRODUCT = 0x811E
PRINTER_NAME = "POS58"     # CUPS printer name (after setup)
DEVICE_PATH = "/dev/usb/lp0"  # Direct USB device path

# ESC/POS Commands
ESC = b'\x1b'
GS = b'\x1d'
LF = b'\x0a'

def check_dependencies():
    """Check which printing methods are available."""
    print("Checking available print methods...\n")
    
    methods = {}
    
    # Check pyusb (PRIMARY METHOD)
    try:
        import usb.core
        dev = usb.core.find(idVendor=PRINTER_VENDOR, idProduct=PRINTER_PRODUCT)
        methods['pyusb'] = dev is not None
        if dev:
            print(f"  ✅ pyusb - Printer found (VID:{hex(PRINTER_VENDOR)} PID:{hex(PRINTER_PRODUCT)})")
            try:
                print(f"      Product: {dev.product}")
                print(f"      Manufacturer: {dev.manufacturer}")
            except:
                pass
        else:
            print(f"  ❌ pyusb - Printer not found")
    except ImportError:
        methods['pyusb'] = False
        print("  ❌ pyusb not installed (pip3 install pyusb)")
    except Exception as e:
        methods['pyusb'] = False
        print(f"  ❌ pyusb error: {e}")
    
    # Check python-escpos
    try:
        from escpos.printer import Usb, File
        methods['escpos'] = True
        print("  ✅ python-escpos installed")
    except ImportError:
        methods['escpos'] = False
        print("  ⚪ python-escpos not installed (optional)")
    
    # Check device file
    methods['device'] = os.path.exists(DEVICE_PATH)
    if methods['device']:
        print(f"  ✅ Device file exists: {DEVICE_PATH}")
    else:
        print(f"  ❌ Device file not found: {DEVICE_PATH}")
    
    # Check CUPS
    try:
        result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
        methods['cups'] = result.returncode == 0
        if methods['cups']:
            print(f"  ✅ CUPS available")
            # List printers
            for line in result.stdout.strip().split('\n'):
                if line:
                    print(f"      {line}")
        else:
            print("  ❌ CUPS not available")
    except FileNotFoundError:
        methods['cups'] = False
        print("  ❌ CUPS not installed")
    
    return methods


def build_test_receipt():
    """Build a test receipt using ESC/POS commands."""
    data = b''
    
    # Initialize printer
    data += ESC + b'@'
    
    # Header (centered, bold, double size)
    data += ESC + b'a\x01'      # Center
    data += ESC + b'!\x30'      # Double width+height
    data += b'RASPBERRY PI' + LF
    data += ESC + b'!\x00'      # Normal
    data += b'PT-210 Test' + LF
    data += b'=' * 32 + LF
    
    # Date/time
    data += ESC + b'a\x00'      # Left align
    now = datetime.now()
    data += f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}".encode() + LF
    data += LF
    
    # Test items
    data += b'Platform: Linux ARM' + LF
    
    # Get system info
    try:
        import platform
        data += f"Arch: {platform.machine()}".encode() + LF
        data += f"Python: {platform.python_version()}".encode() + LF
    except:
        pass
    
    data += LF
    data += b'-' * 32 + LF
    
    # Print methods section
    data += ESC + b'E\x01'      # Bold on
    data += b'PRINT METHODS:' + LF
    data += ESC + b'E\x00'      # Bold off
    data += b'1. python-escpos USB' + LF
    data += b'2. /dev/usb/lp0' + LF
    data += b'3. CUPS lp command' + LF
    data += LF
    
    # Footer
    data += b'-' * 32 + LF
    data += ESC + b'a\x01'      # Center
    data += b'Test Complete!' + LF
    data += LF * 3
    
    # Cut paper (if supported)
    data += GS + b'V\x01'
    
    return data


def print_via_pyusb():
    """Print using direct pyusb access (RECOMMENDED for Raspberry Pi)."""
    print("\n--- Method: Direct USB (pyusb) [RECOMMENDED] ---")
    
    try:
        import usb.core
        import usb.util
        
        dev = usb.core.find(idVendor=PRINTER_VENDOR, idProduct=PRINTER_PRODUCT)
        if dev is None:
            print("❌ Printer not found")
            return False
        
        print(f"   Found: {dev.product} by {dev.manufacturer}")
        
        # Detach kernel driver if attached
        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
                print("   Detached kernel driver")
        except:
            pass
        
        # Set configuration
        try:
            dev.set_configuration()
        except usb.core.USBError:
            pass  # Already configured
        
        # Find OUT endpoint
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]
        ep_out = None
        for ep in intf:
            if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                ep_out = ep
                break
        
        ep_addr = ep_out.bEndpointAddress if ep_out else 0x01
        
        # Build and send receipt
        data = build_test_receipt()
        bytes_sent = dev.write(ep_addr, data)
        
        print(f"✅ Sent {bytes_sent} bytes via pyusb")
        return True
        
    except ImportError:
        print("❌ pyusb not installed. Run: pip3 install pyusb")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Try running with: sudo python3")
        return False


def print_via_escpos_usb():
    """Print using python-escpos USB method."""
    print("\n--- Method 1: python-escpos USB ---")
    try:
        from escpos.printer import Usb
        
        p = Usb(PRINTER_VENDOR, PRINTER_PRODUCT)
        p.text("RASPBERRY PI\n")
        p.text("python-escpos USB Test\n")
        p.text("=" * 32 + "\n")
        p.text(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")
        p.text("\n")
        p.text("Test successful!\n")
        p.cut()
        p.close()
        
        print("✅ Printed via python-escpos USB")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_via_device_file():
    """Print directly to /dev/usb/lp0 device file."""
    print("\n--- Method 2: Device File (/dev/usb/lp0) ---")
    
    if not os.path.exists(DEVICE_PATH):
        print(f"❌ Device not found: {DEVICE_PATH}")
        print("   Try: sudo chmod 666 /dev/usb/lp0")
        return False
    
    try:
        data = build_test_receipt()
        
        with open(DEVICE_PATH, 'wb') as f:
            f.write(data)
        
        print(f"✅ Sent {len(data)} bytes to {DEVICE_PATH}")
        return True
    except PermissionError:
        print(f"❌ Permission denied. Run: sudo chmod 666 {DEVICE_PATH}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_via_escpos_file():
    """Print using python-escpos File method."""
    print("\n--- Method 2b: python-escpos File ---")
    
    if not os.path.exists(DEVICE_PATH):
        print(f"❌ Device not found: {DEVICE_PATH}")
        return False
    
    try:
        from escpos.printer import File
        
        p = File(DEVICE_PATH)
        p.text("RASPBERRY PI\n")
        p.text("python-escpos File Test\n")
        p.text("=" * 32 + "\n")
        p.text(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")
        p.text("\n")
        p.text("Test successful!\n")
        p.cut()
        p.close()
        
        print("✅ Printed via python-escpos File")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_via_cups(pdf_path=None):
    """Print using CUPS lp command."""
    print("\n--- Method 3: CUPS ---")
    
    # Check if CUPS is available
    try:
        result = subprocess.run(['lpstat', '-d'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ CUPS not configured or no default printer")
            return False
    except FileNotFoundError:
        print("❌ CUPS not installed")
        return False
    
    if pdf_path and os.path.exists(pdf_path):
        # Print PDF file
        try:
            result = subprocess.run(
                ['lp', '-d', PRINTER_NAME, pdf_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ Printed PDF via CUPS: {pdf_path}")
                return True
            else:
                print(f"❌ CUPS error: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    else:
        # Print text
        try:
            text = """
RASPBERRY PI
CUPS Print Test
================================
Time: {}

This is a test print via CUPS.

Test successful!
""".format(datetime.now().strftime('%H:%M:%S'))
            
            result = subprocess.run(
                ['lp', '-d', PRINTER_NAME],
                input=text.encode(),
                capture_output=True
            )
            if result.returncode == 0:
                print("✅ Printed text via CUPS")
                return True
            else:
                # Try default printer
                result = subprocess.run(
                    ['lp'],
                    input=text.encode(),
                    capture_output=True
                )
                if result.returncode == 0:
                    print("✅ Printed text via CUPS (default printer)")
                    return True
                print(f"❌ CUPS error: {result.stderr.decode()}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


def print_pdf_via_pyusb(pdf_path):
    """Print a PDF file using pyusb (RECOMMENDED for Raspberry Pi)."""
    print(f"\n{'='*52}")
    print("PDF Print Test (pyusb)")
    print('='*52)
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return False
    
    print(f"PDF file: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path):,} bytes")
    
    # Check dependencies
    print("\nChecking dependencies...")
    try:
        import usb.core
        import usb.util
        print("  ✅ pyusb")
    except ImportError:
        print("  ❌ pyusb - Run: pip3 install pyusb")
        return False
    
    try:
        from pdf2image import convert_from_path
        print("  ✅ pdf2image")
    except ImportError:
        print("  ❌ pdf2image - Run: pip3 install pdf2image")
        return False
    
    try:
        from PIL import Image
        print("  ✅ pillow")
    except ImportError:
        print("  ❌ pillow - Run: pip3 install pillow")
        return False
    
    # Find printer
    dev = usb.core.find(idVendor=PRINTER_VENDOR, idProduct=PRINTER_PRODUCT)
    if dev is None:
        print("❌ Printer not found")
        return False
    print(f"  ✅ Printer: {dev.product}")
    
    # Convert PDF to images
    print(f"\nConverting PDF to images (DPI: 203)...")
    try:
        images = convert_from_path(pdf_path, dpi=203)
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        print("   Install poppler: sudo apt-get install poppler-utils")
        return False
    
    print(f"  ✅ Converted to {len(images)} page(s)")
    
    # Setup USB
    try:
        if dev.is_kernel_driver_active(0):
            dev.detach_kernel_driver(0)
    except:
        pass
    
    try:
        dev.set_configuration()
    except:
        pass
    
    # Find OUT endpoint
    cfg = dev.get_active_configuration()
    intf = cfg[(0, 0)]
    ep_out = None
    for ep in intf:
        if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
            ep_out = ep
            break
    ep_addr = ep_out.bEndpointAddress if ep_out else 0x01
    
    # Printer settings
    PRINTER_WIDTH = 384  # 48mm at 203 DPI
    
    # Initialize printer
    dev.write(ep_addr, b'\x1b\x40')  # ESC @ - Initialize
    
    # Process each page
    for page_num, img in enumerate(images, 1):
        print(f"\nProcessing page {page_num}/{len(images)}...")
        
        # Resize to printer width
        ratio = PRINTER_WIDTH / img.width
        new_height = int(img.height * ratio)
        img_resized = img.resize((PRINTER_WIDTH, new_height), Image.LANCZOS)
        
        # Convert to grayscale then to 1-bit (black/white)
        img_bw = img_resized.convert('L')  # Grayscale
        img_1bit = img_bw.point(lambda x: 0 if x < 128 else 255, '1')
        
        print(f"  Image size: {PRINTER_WIDTH}x{new_height} pixels")
        
        # Convert to ESC/POS raster format
        # Using GS v 0 command (raster bit image)
        width_bytes = (PRINTER_WIDTH + 7) // 8
        
        # Process image in chunks (max ~256 lines at a time for stability)
        chunk_height = 128
        pixels = list(img_1bit.getdata())
        
        for y_start in range(0, new_height, chunk_height):
            y_end = min(y_start + chunk_height, new_height)
            chunk_lines = y_end - y_start
            
            # Build raster data for this chunk
            raster_data = bytearray()
            
            for y in range(y_start, y_end):
                row_bytes = bytearray(width_bytes)
                for x in range(PRINTER_WIDTH):
                    pixel = pixels[y * PRINTER_WIDTH + x]
                    if pixel == 0:  # Black pixel
                        byte_idx = x // 8
                        bit_idx = 7 - (x % 8)
                        row_bytes[byte_idx] |= (1 << bit_idx)
                raster_data.extend(row_bytes)
            
            # Send GS v 0 command
            # Format: GS v 0 m xL xH yL yH [data]
            # m = 0 (normal), xL xH = width in bytes, yL yH = height in lines
            cmd = bytearray([
                0x1d, 0x76, 0x30, 0x00,  # GS v 0 m
                width_bytes & 0xff, (width_bytes >> 8) & 0xff,  # xL xH
                chunk_lines & 0xff, (chunk_lines >> 8) & 0xff,  # yL yH
            ])
            cmd.extend(raster_data)
            
            # Send in smaller USB packets if needed
            packet_size = 512
            for i in range(0, len(cmd), packet_size):
                dev.write(ep_addr, bytes(cmd[i:i+packet_size]))
        
        print(f"  ✅ Page {page_num} sent")
    
    # Feed and cut
    dev.write(ep_addr, b'\n\n\n')
    dev.write(ep_addr, b'\x1d\x56\x01')  # Partial cut
    
    print(f"\n✅ PDF printed successfully! ({len(images)} page(s))")
    return True


def print_pdf_linux(pdf_path):
    """Print a PDF file on Linux using available methods."""
    print(f"\n=== Printing PDF: {pdf_path} ===")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return False
    
    # Try pyusb first (RECOMMENDED - works on Raspberry Pi)
    if print_pdf_via_pyusb(pdf_path):
        return True
    
    # Try CUPS as fallback
    print("\nTrying CUPS...")
    if print_via_cups(pdf_path):
        return True
    
    print("❌ All PDF print methods failed")
    return False


def setup_instructions():
    """Print setup instructions for Raspberry Pi."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     PT-210 / POS58 Setup Guide for Raspberry Pi (Debian)     ║
╚══════════════════════════════════════════════════════════════╝

1. INSTALL DEPENDENCIES (REQUIRED)
   --------------------------------
   sudo apt-get update
   sudo apt-get install -y libusb-1.0-0-dev
   pip3 install pyusb

2. SET UP USB PERMISSIONS
   -----------------------
   # Create udev rule for non-root access
   echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0fe6", ATTR{idProduct}=="811e", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/99-pos58.rules
   
   # Reload rules
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   
   # Add user to plugdev group
   sudo usermod -aG plugdev $USER
   
   # Unplug and replug the printer, then logout/login

3. TEST THE PRINTER
   -----------------
   # Run this test script:
   python3 pos58_linux_test.py
   
   # Or with sudo if permissions aren't set:
   sudo python3 pos58_linux_test.py

4. OPTIONAL: Additional packages
   ------------------------------
   # For PDF printing support:
   sudo apt-get install -y poppler-utils
   pip3 install pdf2image pillow
   
   # For python-escpos (alternative method):
   pip3 install python-escpos

5. TROUBLESHOOTING
   ----------------
   # Check if printer is detected:
   lsusb | grep "0fe6"
   
   # Should show:
   # Bus 001 Device XXX: ID 0fe6:811e ICS Advent Parallel Adapter
   
   # If permission denied, run with sudo or check udev rules
   
   # Check dmesg for USB events:
   dmesg | grep -i "pos58\\|0fe6"

NOTE: The /dev/usb/lp0 device file method does NOT work with
      this printer on Raspberry Pi. Use pyusb instead!
""")


def main():
    print("╔" + "═" * 50 + "╗")
    print("║" + " PT-210 / POS58 Linux Print Test ".center(50) + "║")
    print("║" + " (Raspberry Pi / Debian ARM Compatible) ".center(50) + "║")
    print("╚" + "═" * 50 + "╝")
    print()
    
    # Default sample PDF path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_pdf = os.path.join(script_dir, '..', 'output', 'tab_39.pdf')
    
    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == '--setup':
            setup_instructions()
            return
        
        if arg == '--cups':
            pdf = sys.argv[2] if len(sys.argv) > 2 else None
            print_via_cups(pdf)
            return
        
        if arg == '--device':
            print_via_device_file()
            return
        
        if arg == '--usb' or arg == '--escpos':
            print_via_escpos_usb()
            return
        
        if arg == '--pdf':
            pdf_path = sys.argv[2] if len(sys.argv) > 2 else default_pdf
            if not os.path.exists(pdf_path):
                print(f"❌ PDF not found: {pdf_path}")
                print(f"\nUsage: python3 {sys.argv[0]} --pdf <path_to_pdf>")
                return
            print_pdf_via_pyusb(pdf_path)
            return
        
        if arg == '--help' or arg == '-h':
            print(f"""
Usage: python3 pos58_linux_test.py [option]

Options:
  --setup      Show setup instructions for Raspberry Pi
  --pyusb      Print TEXT test via direct pyusb (RECOMMENDED)
  --pdf [FILE] Print a PDF file (default: {default_pdf})
  --device     Print test via /dev/usb/lp0 (if available)
  --escpos     Print test via python-escpos USB
  --cups       Print test via CUPS
  --help       Show this help

Examples:
  python3 pos58_linux_test.py              # Run text print test
  python3 pos58_linux_test.py --pdf        # Print default sample PDF
  python3 pos58_linux_test.py --pdf /path/to/file.pdf

Without arguments: Run pyusb text test (recommended method)
""")
            return
        
        if arg == '--pyusb':
            print_via_pyusb()
            return
        
        # If argument looks like a file path, try to print it as PDF
        if os.path.exists(arg) and arg.lower().endswith('.pdf'):
            print_pdf_via_pyusb(arg)
            return
    
    # Check dependencies and available methods
    methods = check_dependencies()
    
    print("\n" + "=" * 52)
    print("Running print test...")
    print("=" * 52)
    
    results = []
    
    # Try pyusb first (RECOMMENDED - works on Raspberry Pi)
    if methods.get('pyusb'):
        results.append(('Direct USB (pyusb)', print_via_pyusb()))
    
    # Fallback methods
    if not results or not results[-1][1]:
        if methods.get('escpos'):
            results.append(('python-escpos USB', print_via_escpos_usb()))
        
        if methods.get('device'):
            results.append(('Device File', print_via_device_file()))
        
        if methods.get('cups'):
            results.append(('CUPS', print_via_cups()))
    
    # Summary
    print("\n" + "=" * 52)
    print("RESULTS SUMMARY")
    print("=" * 52)
    
    if results:
        for name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {name}: {status}")
    else:
        print("  No print methods available!")
        print("\n  Run with --setup for installation instructions")
    
    print()


if __name__ == "__main__":
    main()
