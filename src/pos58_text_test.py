#!/usr/bin/env python3
"""
PT-210 / POS58 Text Print Test
==============================

This script prints a simple text receipt using raw ESC/POS commands.
No images, no PDF conversion - just pure text formatting.

Usage:
    python pos58_text_test.py

Requirements:
    pip install pywin32
"""

import sys
from datetime import datetime

# Printer configuration
PRINTER_NAME = "POS58 Printer"


def print_text_receipt():
    """Print a text-only receipt using raw ESC/POS commands."""
    print("=" * 50)
    print("POS58 Text Print Test")
    print("=" * 50)
    
    try:
        import win32print
        
        # Check if printer exists
        printers = [p[2] for p in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )]
        
        if PRINTER_NAME not in printers:
            print(f"❌ Printer '{PRINTER_NAME}' not found!")
            print(f"   Available: {printers}")
            return False
        
        print(f"✅ Printer found: {PRINTER_NAME}")
        print("Sending text receipt...")
        
        # ESC/POS Commands
        ESC = b'\x1b'
        GS = b'\x1d'
        LF = b'\x0a'
        
        # Build the receipt data
        data = b''
        
        # === INITIALIZE ===
        data += ESC + b'@'  # Initialize printer
        
        # === HEADER ===
        data += ESC + b'a\x01'  # Center alignment
        data += ESC + b'!\x30'  # Double height + Double width
        data += b'KITCHNTABS' + LF
        data += ESC + b'!\x00'  # Normal size
        data += b'Point of Sale' + LF
        data += b'================================' + LF
        
        # === DATE/TIME ===
        data += ESC + b'a\x00'  # Left alignment
        now = datetime.now()
        data += f"Date: {now.strftime('%Y-%m-%d')}".encode('cp437') + LF
        data += f"Time: {now.strftime('%H:%M:%S')}".encode('cp437') + LF
        data += f"Receipt #: {now.strftime('%H%M%S')}".encode('cp437') + LF
        data += b'--------------------------------' + LF
        
        # === ORDER ITEMS ===
        data += ESC + b'E\x01'  # Bold ON
        data += b'ORDER DETAILS:' + LF
        data += ESC + b'E\x00'  # Bold OFF
        data += LF
        
        # Sample items
        items = [
            ("Burger Classic", 2, 8.99),
            ("French Fries", 2, 3.50),
            ("Coca Cola", 3, 2.50),
            ("Chicken Wings", 1, 12.99),
        ]
        
        subtotal = 0
        for name, qty, price in items:
            line_total = qty * price
            subtotal += line_total
            # Format: Item name left, qty x price right
            item_line = f"{qty}x {name}"
            price_str = f"${line_total:.2f}"
            # Pad to fill 32 characters
            padding = 32 - len(item_line) - len(price_str)
            data += f"{item_line}{' ' * padding}{price_str}".encode('cp437') + LF
        
        data += b'--------------------------------' + LF
        
        # === TOTALS ===
        tax = subtotal * 0.10  # 10% tax
        total = subtotal + tax
        
        data += f"{'Subtotal:':<24}${subtotal:>6.2f}".encode('cp437') + LF
        data += f"{'Tax (10%):':<24}${tax:>6.2f}".encode('cp437') + LF
        data += b'--------------------------------' + LF
        
        data += ESC + b'!\x10'  # Double height
        data += f"{'TOTAL:':<24}${total:>6.2f}".encode('cp437') + LF
        data += ESC + b'!\x00'  # Normal size
        
        data += b'================================' + LF
        
        # === PAYMENT INFO ===
        data += LF
        data += b'Payment Method: CASH' + LF
        data += f"{'Amount Paid:':<24}${50.00:>6.2f}".encode('cp437') + LF
        data += f"{'Change:':<24}${50.00-total:>6.2f}".encode('cp437') + LF
        
        # === FOOTER ===
        data += LF
        data += b'--------------------------------' + LF
        data += ESC + b'a\x01'  # Center alignment
        data += b'Thank you for your order!' + LF
        data += LF
        data += ESC + b'-\x01'  # Underline ON
        data += b'www.kitchntabs.com' + LF
        data += ESC + b'-\x00'  # Underline OFF
        data += LF
        data += b'*** TEXT PRINT TEST ***' + LF
        data += b'*** SUCCESSFUL ***' + LF
        
        # === FEED AND CUT ===
        data += LF * 4  # Feed paper
        data += GS + b'V\x01'  # Partial cut
        
        # Send to printer
        handle = win32print.OpenPrinter(PRINTER_NAME)
        try:
            job = win32print.StartDocPrinter(handle, 1, ("Text Receipt Test", None, "RAW"))
            try:
                win32print.StartPagePrinter(handle)
                bytes_written = win32print.WritePrinter(handle, data)
                win32print.EndPagePrinter(handle)
                print(f"✅ Sent {bytes_written} bytes to printer")
            finally:
                win32print.EndDocPrinter(handle)
        finally:
            win32print.ClosePrinter(handle)
        
        print("✅ Text receipt printed successfully!")
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
    """Main entry point."""
    print("\n")
    print("╔" + "═" * 48 + "╗")
    print("║" + " PT-210 / POS58 TEXT Print Test ".center(48) + "║")
    print("╚" + "═" * 48 + "╝")
    print()
    
    success = print_text_receipt()
    
    print("\n" + "=" * 50)
    print("RESULT:", "✅ PASS" if success else "❌ FAIL")
    print("=" * 50)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
