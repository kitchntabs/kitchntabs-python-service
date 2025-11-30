#!/usr/bin/env python3
"""
Cross-Platform Thermal Printer Test
====================================

This script tests thermal printing on any platform (Windows, macOS, Linux/ARM).

Usage:
    python test_thermal_printer.py                    # Run diagnostics and test print
    python test_thermal_printer.py --status           # Show printer status only
    python test_thermal_printer.py --pdf <file.pdf>   # Print a specific PDF
    python test_thermal_printer.py --method <method>  # Force specific method
    
Methods:
    auto        - Use best available method (default)
    win32       - Windows GDI printing
    pyusb       - Direct USB (recommended for Raspberry Pi)
    cups        - CUPS printing (Linux/macOS)
    device_file - Direct /dev/usb/lp0
"""

import sys
import os
import argparse

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pinoywok.thermal_printer import ThermalPrinter


def print_banner():
    print()
    print("╔" + "═" * 50 + "╗")
    print("║" + " Cross-Platform Thermal Printer Test ".center(50) + "║")
    print("╚" + "═" * 50 + "╝")
    print()


def show_status(printer: ThermalPrinter):
    """Display detailed printer status."""
    status = printer.get_status()
    
    print("📊 Printer Status")
    print("=" * 40)
    print(f"  Platform:      {status['platform']}")
    print(f"  ARM:           {'Yes' if status['is_arm'] else 'No'}")
    print(f"  Vendor ID:     {status['vendor_id']}")
    print(f"  Product ID:    {status['product_id']}")
    print(f"  Recommended:   {status['recommended']}")
    print()
    print("📋 Available Methods:")
    for method, available in status['methods'].items():
        icon = "✅" if available else "❌"
        print(f"  {icon} {method}")
    print()


def run_test(printer: ThermalPrinter, method: str = 'auto'):
    """Run test print."""
    print(f"🖨️  Running test print (method: {method})...")
    print()
    
    success = printer.test_print()
    
    print()
    if success:
        print("✅ TEST PASSED - Check your printer!")
    else:
        print("❌ TEST FAILED - See errors above")
        print()
        print("💡 Troubleshooting tips:")
        print("   - Check printer is connected and powered on")
        print("   - Run 'lsusb' to verify USB connection")
        print("   - Try running with sudo for permission issues")
        print("   - On Linux, install: sudo apt-get install libusb-1.0-0-dev")
        print("   - Install pyusb: pip install pyusb")
    
    return success


def print_pdf(printer: ThermalPrinter, pdf_path: str, method: str = 'auto'):
    """Print a PDF file."""
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    print(f"📄 Printing PDF: {pdf_path}")
    print(f"   File size: {os.path.getsize(pdf_path):,} bytes")
    print()
    
    return printer.print_pdf(pdf_path, method=method)


def main():
    parser = argparse.ArgumentParser(description='Cross-platform thermal printer test')
    parser.add_argument('--status', action='store_true', help='Show printer status only')
    parser.add_argument('--pdf', type=str, help='PDF file to print')
    parser.add_argument('--method', type=str, default='auto', 
                       choices=['auto', 'win32', 'pyusb', 'cups', 'device_file', 'escpos_usb'],
                       help='Print method to use')
    parser.add_argument('--vendor', type=str, help='Printer vendor ID (hex, e.g., 0x0FE6)')
    parser.add_argument('--product', type=str, help='Printer product ID (hex, e.g., 0x811E)')
    parser.add_argument('--config', type=str, help='Config file path')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Initialize printer
    config = None
    if args.config:
        from pinoywok.config import config as cfg
        cfg.load_config(args.config)
        config = cfg
    
    printer = ThermalPrinter(config)
    
    # Override vendor/product if specified
    if args.vendor:
        printer.vendor_id = int(args.vendor, 16)
    if args.product:
        printer.product_id = int(args.product, 16)
        # Re-detect methods with new IDs
        printer.available_methods = printer._detect_methods()
    
    # Show status
    show_status(printer)
    
    if args.status:
        return 0
    
    # Print PDF or run test
    if args.pdf:
        success = print_pdf(printer, args.pdf, args.method)
    else:
        success = run_test(printer, args.method)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
