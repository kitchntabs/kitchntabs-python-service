#!/usr/bin/env python3
"""
PT-210 Portable Thermal Printer Test Script
============================================

This script tests USB connectivity and printing with the PT-210 thermal printer.

PT-210 Printer Specifications:
- Vendor ID: 0x0FE6
- Product ID: 0x811E
- Print Width: 58mm (48mm printable area)
- Resolution: 203 DPI
- Interface: USB (appears as serial COM port on Windows)

Usage:
    python pt210_test.py

Requirements:
    pip install python-escpos pyserial pillow

On Windows:
    - The PT-210 typically appears as a COM port (e.g., COM3)
    - Check Device Manager > Ports (COM & LPT) for the correct port
"""

import sys
import os
from datetime import datetime
import time

# PT-210 USB IDs
VENDOR_ID = 0x0FE6
PRODUCT_ID = 0x811E

# Default COM port for PT-210 on Windows (change if different)
DEFAULT_COM_PORT = "COM3"
DEFAULT_BAUD_RATE = 9600

def check_usb_device():
    """Check if the PT-210 is connected via USB."""
    print("=" * 50)
    print("PT-210 USB Device Check")
    print("=" * 50)
    
    try:
        import usb.core
        import usb.util
        
        # Find the device
        device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        
        if device is None:
            print(f"❌ PT-210 not found!")
            print(f"   Expected VID: 0x{VENDOR_ID:04X}, PID: 0x{PRODUCT_ID:04X}")
            print("\n   Troubleshooting:")
            print("   1. Check if the printer is powered on")
            print("   2. Check USB cable connection")
            print("   3. Try a different USB port")
            return False
        
        print(f"✅ PT-210 Found!")
        print(f"   Vendor ID:  0x{device.idVendor:04X}")
        print(f"   Product ID: 0x{device.idProduct:04X}")
        print(f"   Bus:        {device.bus}")
        print(f"   Address:    {device.address}")
        
        # Try to get manufacturer and product strings
        try:
            if device.iManufacturer:
                print(f"   Manufacturer: {usb.util.get_string(device, device.iManufacturer)}")
            if device.iProduct:
                print(f"   Product: {usb.util.get_string(device, device.iProduct)}")
        except Exception as e:
            print(f"   (Could not read device strings: {e})")
        
        return True
        
    except ImportError:
        print("❌ pyusb not installed!")
        print("   Install with: pip install pyusb")
        return False
    except Exception as e:
        print(f"❌ Error checking USB device: {e}")
        return False


def test_escpos_print():
    """Test printing with python-escpos library."""
    print("\n" + "=" * 50)
    print("ESC/POS Print Test")
    print("=" * 50)
    
    try:
        from escpos.printer import Usb
        
        print(f"Connecting to PT-210 (VID=0x{VENDOR_ID:04X}, PID=0x{PRODUCT_ID:04X})...")
        
        # Create USB printer connection
        # PT-210 typically uses interface 0, endpoint 0x01 (out)
        # You may need to adjust in_ep and out_ep based on your device
        printer = Usb(
            idVendor=VENDOR_ID,
            idProduct=PRODUCT_ID,
            in_ep=0x81,   # Input endpoint (may vary)
            out_ep=0x01,  # Output endpoint (may vary)
            timeout=5000
        )
        
        print("✅ Connected to printer!")
        
        # Print test receipt
        print("Printing test receipt...")
        
        # Initialize printer
        printer.set(align='center')
        
        # Header
        printer.text("=" * 32 + "\n")
        printer.set(align='center', bold=True, double_height=True)
        printer.text("PT-210 TEST\n")
        printer.set(align='center', bold=False, double_height=False)
        printer.text("=" * 32 + "\n\n")
        
        # Test information
        printer.set(align='left')
        printer.text(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        printer.text(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")
        printer.text("-" * 32 + "\n\n")
        
        # Test content
        printer.set(align='center')
        printer.text("PRINT TEST SUCCESSFUL\n\n")
        
        printer.set(align='left')
        printer.text("Printer Info:\n")
        printer.text(f"  Model: PT-210\n")
        printer.text(f"  VID: 0x{VENDOR_ID:04X}\n")
        printer.text(f"  PID: 0x{PRODUCT_ID:04X}\n\n")
        
        # Text styles test
        printer.text("-" * 32 + "\n")
        printer.text("Style Tests:\n")
        printer.set(bold=True)
        printer.text("  Bold Text\n")
        printer.set(bold=False, underline=1)
        printer.text("  Underlined\n")
        printer.set(underline=0, double_width=True)
        printer.text("  Double Width\n")
        printer.set(double_width=False, double_height=True)
        printer.text("  Double Height\n")
        printer.set(double_height=False)
        printer.text("-" * 32 + "\n\n")
        
        # Footer
        printer.set(align='center')
        printer.text("KitchenTabs\n")
        printer.text("www.kitchntabs.com\n\n")
        
        # Cut paper (if supported)
        try:
            printer.cut()
        except:
            # Some printers don't support cut
            printer.text("\n" * 3)
        
        printer.close()
        
        print("✅ Test receipt printed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install with: pip install python-escpos")
        return False
    except Exception as e:
        print(f"❌ Print error: {e}")
        print("\n   Troubleshooting:")
        print("   1. On Windows, you may need Zadig to install WinUSB driver")
        print("   2. Try running as Administrator")
        print("   3. Check if another application is using the printer")
        return False


def test_win32_print():
    """Test printing with Windows print spooler (if available)."""
    print("\n" + "=" * 50)
    print("Windows Print Spooler Test")
    print("=" * 50)
    
    if sys.platform != 'win32':
        print("⚠️  Skipping - not on Windows")
        return False
    
    try:
        import win32print
        
        # List available printers
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        
        print("Available printers:")
        for flags, desc, name, comment in printers:
            print(f"  - {name}")
        
        # Get default printer
        default_printer = win32print.GetDefaultPrinter()
        print(f"\nDefault printer: {default_printer}")
        
        return True
        
    except ImportError:
        print("⚠️  win32print not available")
        print("   Install with: pip install pywin32")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_simple_text():
    """Print simple text directly to USB endpoint."""
    print("\n" + "=" * 50)
    print("Direct USB Print Test")
    print("=" * 50)
    
    try:
        import usb.core
        import usb.util
        
        device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        
        if device is None:
            print("❌ Device not found")
            return False
        
        # Detach kernel driver if necessary (Linux)
        try:
            if device.is_kernel_driver_active(0):
                device.detach_kernel_driver(0)
        except:
            pass
        
        # Set configuration
        try:
            device.set_configuration()
        except Exception as e:
            print(f"⚠️  Could not set configuration: {e}")
        
        # Get endpoint
        cfg = device.get_active_configuration()
        intf = cfg[(0, 0)]
        
        # Find OUT endpoint
        ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        
        if ep_out is None:
            print("❌ Output endpoint not found")
            return False
        
        print(f"Found endpoint: 0x{ep_out.bEndpointAddress:02X}")
        
        # ESC/POS commands
        ESC = b'\x1b'
        GS = b'\x1d'
        
        # Initialize printer
        ep_out.write(ESC + b'@')
        
        # Center align
        ep_out.write(ESC + b'a' + b'\x01')
        
        # Print text
        text = "=== PT-210 TEST ===\n\n"
        text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        text += "Direct USB Print OK!\n\n"
        text += "KitchenTabs\n"
        text += "\n\n\n"
        
        ep_out.write(text.encode('cp437'))
        
        # Feed and cut
        ep_out.write(GS + b'V' + b'\x00')  # Full cut
        
        print("✅ Direct USB print completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all printer tests."""
    print("\n")
    print("╔" + "═" * 48 + "╗")
    print("║" + " PT-210 Thermal Printer Test Suite ".center(48) + "║")
    print("╚" + "═" * 48 + "╝")
    print()
    
    results = {}
    
    # Test 1: USB Device Check
    results['usb_check'] = check_usb_device()
    
    # Test 2: Windows Print Spooler (if on Windows)
    if sys.platform == 'win32':
        results['win32'] = test_win32_print()
    
    # Test 3: ESC/POS Print
    if results['usb_check']:
        print("\nDo you want to print a test receipt? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                results['escpos'] = test_escpos_print()
                
                if not results['escpos']:
                    print("\nTrying direct USB print...")
                    results['direct_usb'] = print_simple_text()
        except:
            print("Skipping print test (non-interactive mode)")
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test}: {status}")
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
