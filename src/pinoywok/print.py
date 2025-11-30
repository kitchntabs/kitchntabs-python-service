from datetime import datetime, timedelta
import platform
import time
import os
from os import path
from pinoywok.parse import format_date
import subprocess
import sys
import json
import requests
from pdf2image import convert_from_path
from escpos.printer import Usb, Network, File
import usb.backend.libusb1 as libusb1

# Import cross-platform thermal printer
from pinoywok.thermal_printer import ThermalPrinter, print_pdf_crossplatform

# Define flag for tracking if win32print is available
_WIN32PRINT_AVAILABLE = False

WINDOWS_OS = False
LINUX_OS = False
MACOS_OS = False

if platform.system() == 'Windows' or os.name == 'nt':
    WINDOWS_OS = True
elif platform.system() == 'Darwin':
    MACOS_OS = True
elif platform.system() == 'Linux':
    LINUX_OS = True

if WINDOWS_OS:
    try:
        import win32print
        _WIN32PRINT_AVAILABLE = True
    except ImportError:
        print('Warning: missing lib... win32print')

    try:
        import win32ui
    except ImportError:
        print('Warning: missing lib... win32ui')
        _WIN32PRINT_AVAILABLE = False
        pass

from PIL import Image

# printorder.py
from pinoywok.logging import log
from pinoywok.api import api
from PIL import ImageWin
import pdfkit
import os
from pinoywok.parsers import default
from pinoywok.parsers import jumpseller
import pinoywok.helpers
from pinoywok.logging import log
import subprocess

from pinoywok.config import config

def print_order(tab_id, token, output, log_file, config_file):
    
    config.load_config(config_file)
    API = f"{config.get_config('API_SCHEME')}://{config.get_config('API_HOST')}{':' + str(config.get_config('API_PORT')) if config.get_config('WS_PORT') else ''}/api/"

    download_url = f"{API}tab/tab/{tab_id}/download"
    output_file = os.path.join(output, f"tab_{tab_id}.pdf")
    
    response = requests.get(download_url, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, stream=True)    
    log(f"Download URL: {download_url}")
    log(f"Bearer Token: {token}")
    log(f"Output File: {output_file}")
    log(f"Tab ID: {tab_id}")
    
    # Check response status and content type
    log(f"Response status code: {response.status_code}")
    log(f"Response content type: {response.headers.get('Content-Type', 'unknown')}")
    
    # If not a successful response or not a PDF, log the content
    if response.status_code != 200 or 'application/pdf' not in response.headers.get('Content-Type', ''):
        log(f"Error response content: {response.text[:500]}...")  # Log first 500 chars
        return False
        
    # Save the PDF file
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    # Use cross-platform thermal printer
    try:
        # Initialize thermal printer with config
        thermal_printer = ThermalPrinter(config)
        
        # Log printer status
        status = thermal_printer.get_status()
        log(f"Printer status: platform={status['platform']}, is_arm={status['is_arm']}, recommended={status['recommended']}")
        log(f"Available methods: {status['methods']}")
        
        # Print the PDF
        success = thermal_printer.print_pdf(output_file)
        
        if success:
            log(f"Successfully printed tab {tab_id}")
            return True
        else:
            log(f"Failed to print via thermal printer, trying fallback...")
            # Fallback to opening the file
            return _fallback_open_pdf(output_file)
        
    except Exception as e:
        log(f"Error with thermal printer: {e}")
        # Fallback to original behavior
        return _fallback_open_pdf(output_file)


def _fallback_open_pdf(output_file):
    """Fallback method to open PDF when thermal printing fails."""
    try:
        if WINDOWS_OS:
            subprocess.call(['start', output_file], shell=True)
        elif MACOS_OS:
            subprocess.call(['open', output_file])
        elif LINUX_OS:
            subprocess.call(['xdg-open', output_file])
        else:
            log("Unsupported platform for fallback")
            return False
        log(f"Opened PDF with system viewer: {output_file}")
        return True
    except Exception as e:
        log(f"Fallback open failed: {e}")
        return False
              
def printer(image):
    # Check if win32print is available
    if not _WIN32PRINT_AVAILABLE:
        log("win32print module is not available. Cannot print.")
        return False
        
    #https://github.com/grantgeorge/pythonPrinting/blob/master/printTest.py
    #https://gist.github.com/buptxge/2fc61a3f914645cf8ae2c9a258ca06c9?permalink_comment_id=3971565
    
    #PRINTER_NAME = 'EPSON TM-m30 Receipt'
    
    PHYSICALWIDTH = 110
    PHYSICALHEIGHT = 111

    
    printer_name = win32print.GetDefaultPrinter()

    bmp = Image.open(image)
        #width,height = bmp.size

    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)
    printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)

        #if bmp.size[0] < bmp.size[1]:
        #    bmp = bmp.rotate(90)

    hDC.StartDoc(image)
    hDC.StartPage()

    
    dib = ImageWin.Dib(bmp)
    dib.draw(hDC.GetHandleOutput(), (0,0,printer_size[0],printer_size[1]))

    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()
    #else:
    #    open_pdf()

    return True

def printPil(image):
    # Check if win32print is available
    if not _WIN32PRINT_AVAILABLE:
        log("win32print module is not available. Cannot print.")
        return False
        
    PHYSICALWIDTH = 110
    PHYSICALHEIGHT = 111
    HORZRES = 8       # Width of printable area in pixels
    VERTRES = 10      # Height of printable area in pixels
    LOGPIXELSX = 88   # Logical pixels per inch in X
    LOGPIXELSY = 90   # Logical pixels per inch in Y
    
    printer_name = win32print.GetDefaultPrinter()
    print(f"Using printer: {printer_name}")
    
    # If image is a string (file path), open it as an image
    if isinstance(image, str):
        bmp = Image.open(image)
    else:
        # It's already a PIL Image object
        bmp = image
    
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)
    
    # Get printer capabilities
    physical_width = hDC.GetDeviceCaps(PHYSICALWIDTH)
    physical_height = hDC.GetDeviceCaps(PHYSICALHEIGHT)
    printable_width = hDC.GetDeviceCaps(HORZRES)
    printable_height = hDC.GetDeviceCaps(VERTRES)
    dpi_x = hDC.GetDeviceCaps(LOGPIXELSX)
    dpi_y = hDC.GetDeviceCaps(LOGPIXELSY)
    
    # Print capabilities
    print(f"Printer capabilities:")
    print(f"  Physical width: {physical_width} pixels ({physical_width/dpi_x:.2f} inches)")
    print(f"  Physical height: {physical_height} pixels ({physical_height/dpi_y:.2f} inches)")
    print(f"  Printable width: {printable_width} pixels ({printable_width/dpi_x:.2f} inches)")
    print(f"  Printable height: {printable_height} pixels ({printable_height/dpi_y:.2f} inches)")
    print(f"  DPI X: {dpi_x}")
    print(f"  DPI Y: {dpi_y}")
    
    # Calculate 5cm width in pixels
    # 1 inch = 2.54 cm, so 5cm = 5/2.54 inches
    target_width_inches = 5 / 2.54
    target_width_pixels = int(target_width_inches * dpi_x)
    
    # Calculate height to maintain aspect ratio
    aspect_ratio = bmp.height / bmp.width
    target_height_pixels = int(target_width_pixels * aspect_ratio)
    
    print(f"Target dimensions for 5cm width:")
    print(f"  Width: {target_width_pixels} pixels ({target_width_inches:.2f} inches)")
    print(f"  Height: {target_height_pixels} pixels ({target_height_pixels/dpi_y:.2f} inches)")
    
    # Use a unique document name
    doc_name = f"receipt_{int(time.time())}"
    hDC.StartDoc(doc_name)
    hDC.StartPage()
    
    # Draw the image with the specified width (5cm)
    dib = ImageWin.Dib(bmp)
    dib.draw(hDC.GetHandleOutput(), (0, 0, target_width_pixels, target_height_pixels))
    
    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()
    
    return True

def open_pdf(pdf_file):
    #acrobat = r'C:\\Program Files\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe'
    acrobat = config.get_acrobat_path()
    printer = "EPSON TM-m30 Receipt"
    cmd = '"{}" /N /T "{}" "{}"'.format(acrobat, pdf_file, printer)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = proc.communicate()
    exit_code = proc.wait()
    
    if exit_code != 0:
        raise Exception(f"PDF printing failed with exit code {exit_code}. Error: {errors.decode()}")
    
    return exit_code




def pdf2png(tab_id, pdf_path, output_dir):
    try:
        # First try with pdf2image/poppler
        images = convert_from_path(pdf_path, 600, poppler_path=config.get('POPPLER_PATH'))
        
        # Save the images
        png_files = []
        for i, image in enumerate(images):
            file_path = os.path.join(output_dir, f'tab_{tab_id}_page_{i+1}.png')
            image.save(file_path, 'PNG')
            png_files.append(file_path)
        
        return png_files
    except Exception as e:
        log(f"Error converting PDF with pdf2image: {e}")
        
        # Fallback to alternative method: PyMuPDF
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            png_files = []
            
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=203)
                file_path = os.path.join(output_dir, f'tab_{tab_id}_page_{i+1}.png')
                pix.save(file_path)
                png_files.append(file_path)
            
            return png_files
        except ImportError:
            log("PyMuPDF not installed. Install with: pip install PyMuPDF")
            raise
        except Exception as e2:
            log(f"Error converting PDF with PyMuPDF: {e2}")
            raise