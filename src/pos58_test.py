#!/usr/bin/env python3
"""
PT-210 / POS58 Thermal Printer Test Script
===========================================

This script tests printing with the GOOJPRT PT-210 thermal printer
after installing the POS58 driver on Windows.

PT-210 Printer Specifications:
- Model: GOOJPRT PT-210 (portable thermal printer)
- Windows Printer Name: POS58 Printer
- Driver: POS58ENG
- Port: USB002
- Print Width: 58mm (48mm printable area)
- Resolution: 203 DPI

Usage:
    python pos58_test.py                    # Print test receipt
    python pos58_test.py --raw              # Test raw ESC/POS commands
    python pos58_test.py --info             # Show printer info only

Requirements:
    pip install pywin32

Driver Installation:
    Download from: https://github.com/1rfsNet/GOOJPRT-Printer-Driver
    Use: Portable Bluetooth printer/MTP-II 58mm Bluetooth Printer/POS58Setup_20190329.exe
"""

import sys
import os
from datetime import datetime
import time

# Printer configuration
PRINTER_NAME = "POS58 Printer"
PRINTER_WIDTH_MM = 58
PRINTABLE_WIDTH_MM = 48


def get_printer_info():
    """Get information about the POS58 printer."""
    print("=" * 50)
    print("POS58 Printer Information")
    print("=" * 50)
    
    try:
        import win32print
        
        # List all printers
        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        
        print("\nInstalled printers:")
        pos58_found = False
        for flags, desc, name, comment in printers:
            marker = " ← PT-210" if "POS58" in name else ""
            print(f"  • {name}{marker}")
            if "POS58" in name:
                pos58_found = True
        
        if not pos58_found:
            print("\n❌ POS58 Printer not found!")
            print("   Please install the driver from:")
            print("   https://github.com/1rfsNet/GOOJPRT-Printer-Driver")
            return False
        
        # Get default printer
        default = win32print.GetDefaultPrinter()
        print(f"\nDefault printer: {default}")
        
        # Get POS58 printer handle for more info
        try:
            handle = win32print.OpenPrinter(PRINTER_NAME)
            info = win32print.GetPrinter(handle, 2)
            
            print(f"\n📋 POS58 Printer Details:")
            print(f"   Name: {info['pPrinterName']}")
            print(f"   Port: {info['pPortName']}")
            print(f"   Driver: {info['pDriverName']}")
            print(f"   Status: {info['Status']}")
            
            win32print.ClosePrinter(handle)
        except Exception as e:
            print(f"   (Could not get detailed info: {e})")
        
        return True
        
    except ImportError:
        print("❌ pywin32 not installed!")
        print("   Install with: pip install pywin32")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_test_receipt():
    """Print a test receipt using Windows print spooler."""
    print("\n" + "=" * 50)
    print("Print Test Receipt (Image-based)")
    print("=" * 50)
    
    try:
        import win32print
        import win32ui
        from PIL import Image, ImageDraw, ImageFont
        from PIL import ImageWin
        
        print(f"Printing to: {PRINTER_NAME}")
        
        # Create a test image for the receipt
        # 48mm printable width at 203 DPI = ~384 pixels
        dpi = 203
        width_pixels = int((PRINTABLE_WIDTH_MM / 25.4) * dpi)  # ~384 pixels
        height_pixels = 600  # Adjust as needed
        
        print(f"Creating receipt image ({width_pixels}x{height_pixels} pixels)...")
        
        # Create image
        img = Image.new('RGB', (width_pixels, height_pixels), 'white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_medium = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = font_large
            font_small = font_large
        
        y = 10
        
        # Header
        draw.text((width_pixels//2, y), "=" * 20, fill='black', font=font_small, anchor='mt')
        y += 20
        draw.text((width_pixels//2, y), "PT-210 TEST", fill='black', font=font_large, anchor='mt')
        y += 30
        draw.text((width_pixels//2, y), "=" * 20, fill='black', font=font_small, anchor='mt')
        y += 30
        
        # Date and time
        now = datetime.now()
        draw.text((10, y), f"Date: {now.strftime('%Y-%m-%d')}", fill='black', font=font_medium)
        y += 25
        draw.text((10, y), f"Time: {now.strftime('%H:%M:%S')}", fill='black', font=font_medium)
        y += 35
        
        # Separator
        draw.text((10, y), "-" * 32, fill='black', font=font_small)
        y += 25
        
        # Success message
        draw.text((width_pixels//2, y), "PRINT TEST", fill='black', font=font_large, anchor='mt')
        y += 30
        draw.text((width_pixels//2, y), "SUCCESSFUL!", fill='black', font=font_large, anchor='mt')
        y += 40
        
        # Printer info
        draw.text((10, y), "Printer Info:", fill='black', font=font_medium)
        y += 25
        draw.text((10, y), f"  Model: PT-210", fill='black', font=font_small)
        y += 18
        draw.text((10, y), f"  Driver: POS58", fill='black', font=font_small)
        y += 18
        draw.text((10, y), f"  Width: {PRINTER_WIDTH_MM}mm", fill='black', font=font_small)
        y += 30
        
        # Separator
        draw.text((10, y), "-" * 32, fill='black', font=font_small)
        y += 25
        
        # Footer
        draw.text((width_pixels//2, y), "KitchenTabs", fill='black', font=font_medium, anchor='mt')
        y += 25
        draw.text((width_pixels//2, y), "www.kitchntabs.com", fill='black', font=font_small, anchor='mt')
        
        # Crop to actual content
        img = img.crop((0, 0, width_pixels, y + 50))
        
        print("Sending to printer...")
        
        # Print using Windows GDI
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(PRINTER_NAME)
        
        # Get printer capabilities
        HORZRES = 8
        VERTRES = 10
        LOGPIXELSX = 88
        LOGPIXELSY = 90
        
        printer_width = hDC.GetDeviceCaps(HORZRES)
        printer_height = hDC.GetDeviceCaps(VERTRES)
        printer_dpi_x = hDC.GetDeviceCaps(LOGPIXELSX)
        printer_dpi_y = hDC.GetDeviceCaps(LOGPIXELSY)
        
        print(f"Printer resolution: {printer_width}x{printer_height} @ {printer_dpi_x}x{printer_dpi_y} DPI")
        
        # Start print job
        hDC.StartDoc("PT-210 Test Receipt")
        hDC.StartPage()
        
        # Calculate scaling
        scale_x = printer_width / img.width
        scale_y = scale_x  # Maintain aspect ratio
        
        dest_width = int(img.width * scale_x)
        dest_height = int(img.height * scale_y)
        
        # Draw image
        dib = ImageWin.Dib(img)
        dib.draw(hDC.GetHandleOutput(), (0, 0, dest_width, dest_height))
        
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        
        print("✅ Test receipt printed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install with: pip install pywin32 pillow")
        return False
    except Exception as e:
        print(f"❌ Print error: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_raw_escpos():
    """Print using raw ESC/POS commands via Windows printer."""
    print("\n" + "=" * 50)
    print("Raw ESC/POS Print Test")
    print("=" * 50)
    
    try:
        import win32print
        
        print(f"Sending raw ESC/POS to: {PRINTER_NAME}")
        
        # ESC/POS Commands
        ESC = b'\x1b'
        GS = b'\x1d'
        LF = b'\x0a'
        
        # Build the receipt
        data = b''
        
        # Initialize printer
        data += ESC + b'@'
        
        # Center alignment
        data += ESC + b'a\x01'
        
        # Double height + width
        data += ESC + b'!\x30'
        data += b'PT-210 TEST' + LF
        
        # Normal size
        data += ESC + b'!\x00'
        data += b'=' * 32 + LF + LF
        
        # Left alignment
        data += ESC + b'a\x00'
        
        # Date/time
        now = datetime.now()
        data += f"Date: {now.strftime('%Y-%m-%d')}\n".encode('cp437')
        data += f"Time: {now.strftime('%H:%M:%S')}\n".encode('cp437')
        data += b'-' * 32 + LF + LF
        
        # Center
        data += ESC + b'a\x01'
        data += b'RAW ESCPOS TEST' + LF
        data += b'SUCCESSFUL!' + LF + LF
        
        # Left alignment for info
        data += ESC + b'a\x00'
        data += b'Printer: POS58' + LF
        data += b'Method: Raw ESC/POS' + LF + LF
        
        # Style tests
        data += b'-' * 32 + LF
        data += b'Style Tests:' + LF
        
        # Bold
        data += ESC + b'E\x01'
        data += b'  Bold Text' + LF
        data += ESC + b'E\x00'
        
        # Underline
        data += ESC + b'-\x01'
        data += b'  Underlined' + LF
        data += ESC + b'-\x00'
        
        data += b'-' * 32 + LF + LF
        
        # Footer centered
        data += ESC + b'a\x01'
        data += b'KitchenTabs' + LF
        data += b'www.kitchntabs.com' + LF
        
        # Feed paper
        data += LF * 4
        
        # Partial cut
        data += GS + b'V\x01'
        
        # Open printer and send raw data
        handle = win32print.OpenPrinter(PRINTER_NAME)
        try:
            job = win32print.StartDocPrinter(handle, 1, ("ESC/POS Test", None, "RAW"))
            try:
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(handle, data)
                win32print.EndPagePrinter(handle)
            finally:
                win32print.EndDocPrinter(handle)
        finally:
            win32print.ClosePrinter(handle)
        
        print("✅ Raw ESC/POS test printed successfully!")
        return True
        
    except ImportError:
        print("❌ pywin32 not installed!")
        print("   Install with: pip install pywin32")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run PT-210/POS58 printer tests."""
    print("\n")
    print("╔" + "═" * 48 + "╗")
    print("║" + " PT-210 / POS58 Printer Test ".center(48) + "║")
    print("╚" + "═" * 48 + "╝")
    print()
    
    # Parse command line args
    args = sys.argv[1:]
    
    if '--info' in args:
        get_printer_info()
        return True
    
    if '--raw' in args:
        if get_printer_info():
            return print_raw_escpos()
        return False
    
    # Default: show info and print test
    results = {}
    
    # Get printer info
    results['printer_found'] = get_printer_info()
    
    if not results['printer_found']:
        print("\n❌ Cannot proceed - printer not found")
        return False
    
    # Ask to print
    print("\n" + "=" * 50)
    print("PRINT OPTIONS")
    print("=" * 50)
    print("\nPOS58 Printer detected!")
    print("\nSelect print test:")
    print("  1. Image-based receipt (Windows GDI)")
    print("  2. Raw ESC/POS commands")
    print("  3. Both")
    print("  4. Skip printing")
    print("\nEnter choice (1-4): ", end="")
    
    try:
        choice = input().strip()
        
        if choice == '1':
            results['gdi_print'] = print_test_receipt()
        elif choice == '2':
            results['raw_print'] = print_raw_escpos()
        elif choice == '3':
            results['gdi_print'] = print_test_receipt()
            results['raw_print'] = print_raw_escpos()
        elif choice == '4':
            print("Skipping print tests.")
        else:
            print("Invalid choice. Skipping.")
            
    except EOFError:
        print("\n(Non-interactive mode)")
        # In non-interactive mode, run raw ESC/POS test
        results['raw_print'] = print_raw_escpos()
    
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
