#!/usr/bin/env python3
"""
PT-210 / POS58 PDF Print Test
=============================

This script prints a PDF file to the POS58 thermal printer.
It converts the PDF to images and prints them using Windows GDI.

Usage:
    python pos58_pdf_test.py                     # Use default sample PDF
    python pos58_pdf_test.py path/to/file.pdf   # Use specific PDF file

Requirements:
    pip install pywin32 pillow pdf2image

Additional Requirements:
    - Poppler for Windows (for PDF to image conversion)
    - Download from: https://github.com/oschwartz10612/poppler-windows/releases
    - Extract to: C:\\poppler-xx.xx.x\\Library\\bin
    - Or install via: choco install poppler
"""

import sys
import os
from datetime import datetime

# Printer configuration
PRINTER_NAME = "POS58 Printer"
PRINTER_WIDTH_MM = 58
PRINTABLE_WIDTH_MM = 48
DPI = 203

# Default sample PDF
DEFAULT_PDF = "./output/tab_39.pdf"

# Poppler path (adjust if installed elsewhere)
POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    missing = []
    
    try:
        import win32print
        print("  ✅ pywin32")
    except ImportError:
        print("  ❌ pywin32")
        missing.append("pywin32")
    
    try:
        import win32ui
        print("  ✅ win32ui")
    except ImportError:
        print("  ❌ win32ui")
        missing.append("pywin32")
    
    try:
        from PIL import Image
        print("  ✅ pillow")
    except ImportError:
        print("  ❌ pillow")
        missing.append("pillow")
    
    try:
        from pdf2image import convert_from_path
        print("  ✅ pdf2image")
    except ImportError:
        print("  ❌ pdf2image")
        missing.append("pdf2image")
    
    # Check Poppler
    poppler_exe = os.path.join(POPPLER_PATH, "pdftoppm.exe")
    if os.path.exists(poppler_exe):
        print(f"  ✅ poppler ({POPPLER_PATH})")
    else:
        print(f"  ❌ poppler (not found at {POPPLER_PATH})")
        missing.append("poppler")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        if "pywin32" in missing or "pillow" in missing or "pdf2image" in missing:
            print("  pip install pywin32 pillow pdf2image")
        if "poppler" in missing:
            print("  choco install poppler")
            print("  Or download from: https://github.com/oschwartz10612/poppler-windows/releases")
        return False
    
    return True


def print_pdf(pdf_path):
    """Print a PDF file to the POS58 thermal printer."""
    print("\n" + "=" * 50)
    print("PDF Print Test")
    print("=" * 50)
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print(f"PDF file: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path):,} bytes")
    
    try:
        import win32print
        import win32ui
        from PIL import Image, ImageOps
        from PIL import ImageWin
        from pdf2image import convert_from_path
        
        # Check if printer exists
        printers = [p[2] for p in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )]
        
        if PRINTER_NAME not in printers:
            print(f"❌ Printer '{PRINTER_NAME}' not found!")
            return False
        
        print(f"✅ Printer found: {PRINTER_NAME}")
        
        # Convert PDF to images
        print(f"Converting PDF to images (DPI: {DPI})...")
        
        try:
            images = convert_from_path(
                pdf_path,
                dpi=DPI,
                poppler_path=POPPLER_PATH if os.path.exists(POPPLER_PATH) else None
            )
        except Exception as e:
            print(f"❌ PDF conversion failed: {e}")
            print("\nMake sure Poppler is installed:")
            print("  choco install poppler")
            return False
        
        print(f"✅ Converted to {len(images)} page(s)")
        
        # Calculate target width in pixels (48mm at 203 DPI)
        target_width = int((PRINTABLE_WIDTH_MM / 25.4) * DPI)  # ~384 pixels
        print(f"Target width: {target_width} pixels ({PRINTABLE_WIDTH_MM}mm)")
        
        # Print each page
        for i, img in enumerate(images):
            print(f"\nProcessing page {i + 1}/{len(images)}...")
            
            # Convert to grayscale for better thermal printing
            img = img.convert('L')
            
            # Resize to fit printer width while maintaining aspect ratio
            aspect_ratio = img.height / img.width
            new_height = int(target_width * aspect_ratio)
            img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert back to RGB for printing
            img = img.convert('RGB')
            
            print(f"  Image size: {img.width}x{img.height} pixels")
            
            # Print using Windows GDI
            print(f"  Sending to printer...")
            
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(PRINTER_NAME)
            
            # Get printer capabilities
            HORZRES = 8
            VERTRES = 10
            
            printer_width = hDC.GetDeviceCaps(HORZRES)
            printer_height = hDC.GetDeviceCaps(VERTRES)
            
            # Start print job
            hDC.StartDoc(f"PDF Print - Page {i + 1}")
            hDC.StartPage()
            
            # Calculate scaling to fit printer width
            scale = printer_width / img.width
            dest_width = int(img.width * scale)
            dest_height = int(img.height * scale)
            
            # Draw image
            dib = ImageWin.Dib(img)
            dib.draw(hDC.GetHandleOutput(), (0, 0, dest_width, dest_height))
            
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            
            print(f"  ✅ Page {i + 1} printed")
        
        print(f"\n✅ PDF printed successfully! ({len(images)} page(s))")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_sample_pdf():
    """Create a simple sample PDF for testing."""
    print("\n" + "=" * 50)
    print("Creating Sample PDF")
    print("=" * 50)
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        
        # Create output directory if needed
        os.makedirs("./output", exist_ok=True)
        
        # PDF dimensions for 58mm thermal printer
        width = 58 * mm
        height = 150 * mm
        
        pdf_path = "./output/sample_receipt.pdf"
        c = canvas.Canvas(pdf_path, pagesize=(width, height))
        
        y = height - 10 * mm
        
        # Header
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2, y, "KITCHNTABS")
        y -= 6 * mm
        
        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, y, "Sample Receipt")
        y -= 6 * mm
        
        c.line(5 * mm, y, width - 5 * mm, y)
        y -= 6 * mm
        
        # Date
        c.setFont("Helvetica", 8)
        c.drawString(5 * mm, y, datetime.now().strftime("%Y-%m-%d %H:%M"))
        y -= 8 * mm
        
        # Items
        items = [
            ("Item 1", "$10.00"),
            ("Item 2", "$15.00"),
            ("Item 3", "$8.50"),
        ]
        
        for name, price in items:
            c.drawString(5 * mm, y, name)
            c.drawRightString(width - 5 * mm, y, price)
            y -= 5 * mm
        
        y -= 3 * mm
        c.line(5 * mm, y, width - 5 * mm, y)
        y -= 6 * mm
        
        # Total
        c.setFont("Helvetica-Bold", 10)
        c.drawString(5 * mm, y, "TOTAL:")
        c.drawRightString(width - 5 * mm, y, "$33.50")
        y -= 10 * mm
        
        # Footer
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, y, "Thank you!")
        y -= 5 * mm
        c.drawCentredString(width / 2, y, "PDF TEST SUCCESSFUL")
        
        c.save()
        
        print(f"✅ Sample PDF created: {pdf_path}")
        return pdf_path
        
    except ImportError:
        print("❌ reportlab not installed (optional)")
        print("   Using existing sample PDF instead")
        return None


def main():
    """Main entry point."""
    print("\n")
    print("╔" + "═" * 48 + "╗")
    print("║" + " PT-210 / POS58 PDF Print Test ".center(48) + "║")
    print("╚" + "═" * 48 + "╝")
    print()
    
    # Check dependencies first
    if not check_dependencies():
        return False
    
    # Get PDF file path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = DEFAULT_PDF
        
        # If default doesn't exist, try to create a sample
        if not os.path.exists(pdf_path):
            created_pdf = create_sample_pdf()
            if created_pdf:
                pdf_path = created_pdf
            else:
                print(f"❌ No PDF file available")
                print(f"   Provide a PDF path as argument:")
                print(f"   python pos58_pdf_test.py path/to/file.pdf")
                return False
    
    # Print the PDF
    success = print_pdf(pdf_path)
    
    print("\n" + "=" * 50)
    print("RESULT:", "✅ PASS" if success else "❌ FAIL")
    print("=" * 50)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
