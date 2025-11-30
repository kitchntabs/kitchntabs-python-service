"""
Cross-Platform Thermal Printer Support
======================================

This module provides unified thermal printing across Windows, macOS, and Linux (including Raspberry Pi).

Supported methods:
- Windows: win32print/GDI (primary), CUPS (fallback)
- macOS: CUPS (primary), lp command (fallback)
- Linux: pyusb direct USB (primary for ARM), CUPS (fallback), /dev/usb/lp0 (fallback)

Usage:
    from pinoywok.thermal_printer import ThermalPrinter
    
    printer = ThermalPrinter(config)
    printer.print_pdf('/path/to/file.pdf')
    printer.print_image(pil_image)
"""

import os
import sys
import platform
import subprocess
from typing import Optional, List, Tuple, Union
from PIL import Image

# Platform detection
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == 'windows' or os.name == 'nt'
IS_MACOS = PLATFORM == 'darwin'
IS_LINUX = PLATFORM == 'linux'
IS_ARM = platform.machine().lower() in ('armv7l', 'armv6l', 'aarch64', 'arm64')

# Optional imports based on platform
_WIN32_AVAILABLE = False
_PYUSB_AVAILABLE = False
_ESCPOS_AVAILABLE = False
_CUPS_AVAILABLE = False

if IS_WINDOWS:
    try:
        import win32print
        import win32ui
        from PIL import ImageWin
        _WIN32_AVAILABLE = True
    except ImportError:
        pass

try:
    import usb.core
    import usb.util
    _PYUSB_AVAILABLE = True
except ImportError:
    pass

try:
    from escpos.printer import Usb, File, Network
    _ESCPOS_AVAILABLE = True
except ImportError:
    pass

# Check CUPS availability on Unix systems
if not IS_WINDOWS:
    try:
        result = subprocess.run(['which', 'lp'], capture_output=True)
        _CUPS_AVAILABLE = result.returncode == 0
    except:
        pass


class ThermalPrinter:
    """Cross-platform thermal printer handler."""
    
    # Default POS58/PT-210 printer IDs
    DEFAULT_VENDOR = 0x0FE6
    DEFAULT_PRODUCT = 0x811E
    
    # ESC/POS commands
    ESC = b'\x1b'
    GS = b'\x1d'
    LF = b'\x0a'
    
    # Printer settings
    PRINTER_WIDTH_PIXELS = 384  # 48mm at 203 DPI
    DPI = 203
    
    def __init__(self, config=None):
        """Initialize thermal printer with optional config."""
        self.config = config
        self.vendor_id = self.DEFAULT_VENDOR
        self.product_id = self.DEFAULT_PRODUCT
        self.printer_name = None
        self.device_path = '/dev/usb/lp0'
        self.poppler_path = None
        
        # Load from config if provided
        if config:
            self._load_config(config)
        
        # Detect available print methods
        self.available_methods = self._detect_methods()
        
    def _load_config(self, config):
        """Load printer settings from config."""
        try:
            vendor = config.get('PRINTER_VENDOR')
            if vendor:
                self.vendor_id = int(vendor, 16) if isinstance(vendor, str) else vendor
                
            product = config.get('PRINTER_PRODUCT')
            if product:
                self.product_id = int(product, 16) if isinstance(product, str) else product
                
            self.printer_name = config.get('PRINTER_NAME')
            self.poppler_path = config.get('POPPLER_PATH')
            
            device = config.get('PRINTER_DEVICE_PATH')
            if device:
                self.device_path = device
        except Exception as e:
            print(f"Warning: Error loading printer config: {e}")
    
    def _detect_methods(self) -> dict:
        """Detect which printing methods are available."""
        methods = {
            'win32': False,
            'pyusb': False,
            'escpos_usb': False,
            'escpos_file': False,
            'cups': False,
            'device_file': False
        }
        
        # Windows GDI
        if IS_WINDOWS and _WIN32_AVAILABLE:
            methods['win32'] = True
            
        # PyUSB direct
        if _PYUSB_AVAILABLE:
            try:
                dev = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
                methods['pyusb'] = dev is not None
            except:
                pass
                
        # python-escpos USB
        if _ESCPOS_AVAILABLE:
            methods['escpos_usb'] = _PYUSB_AVAILABLE
            
        # Device file (Linux)
        if IS_LINUX and os.path.exists(self.device_path):
            methods['device_file'] = True
            methods['escpos_file'] = _ESCPOS_AVAILABLE
            
        # CUPS
        methods['cups'] = _CUPS_AVAILABLE
        
        return methods
    
    def get_status(self) -> dict:
        """Get printer status and available methods."""
        return {
            'platform': PLATFORM,
            'is_arm': IS_ARM,
            'vendor_id': hex(self.vendor_id),
            'product_id': hex(self.product_id),
            'methods': self.available_methods,
            'recommended': self._get_recommended_method()
        }
    
    def _get_recommended_method(self) -> str:
        """Get the recommended print method for this platform."""
        if IS_WINDOWS:
            return 'win32' if self.available_methods['win32'] else 'cups'
        elif IS_LINUX and IS_ARM:
            # For Raspberry Pi, pyusb is most reliable
            if self.available_methods['pyusb']:
                return 'pyusb'
            elif self.available_methods['device_file']:
                return 'device_file'
            return 'cups'
        elif IS_LINUX:
            return 'cups' if self.available_methods['cups'] else 'pyusb'
        elif IS_MACOS:
            # For macOS, prefer direct pyusb over escpos_usb (more reliable)
            # escpos_usb can have timeout issues with certain USB thermal printers
            if self.available_methods['pyusb']:
                return 'pyusb'
            elif self.available_methods['escpos_usb']:
                return 'escpos_usb'
            return 'cups'
        return 'cups'
    
    def print_pdf(self, pdf_path: str, method: str = 'auto') -> bool:
        """
        Print a PDF file to the thermal printer.
        
        Args:
            pdf_path: Path to the PDF file
            method: Print method ('auto', 'win32', 'pyusb', 'cups', 'device_file')
            
        Returns:
            True if printing was successful
        """
        if not os.path.exists(pdf_path):
            print(f"Error: PDF file not found: {pdf_path}")
            return False
            
        # Convert PDF to images
        images = self._pdf_to_images(pdf_path)
        if not images:
            print("Error: Failed to convert PDF to images")
            return False
            
        # Print each page
        success = True
        for i, img in enumerate(images):
            print(f"Printing page {i+1}/{len(images)}...")
            if not self.print_image(img, method):
                success = False
                
        return success
    
    def print_image(self, image: Union[Image.Image, str], method: str = 'auto') -> bool:
        """
        Print an image to the thermal printer.
        
        Args:
            image: PIL Image object or path to image file
            method: Print method ('auto', 'win32', 'pyusb', 'cups', 'device_file')
            
        Returns:
            True if printing was successful
        """
        # Load image if path provided
        if isinstance(image, str):
            image = Image.open(image)
            
        # Select method
        if method == 'auto':
            method = self._get_recommended_method()
            
        print(f"Using print method: {method}")
        
        # Route to appropriate method
        if method == 'win32':
            return self._print_win32(image)
        elif method == 'pyusb':
            return self._print_pyusb(image)
        elif method == 'device_file':
            return self._print_device_file(image)
        elif method == 'cups':
            return self._print_cups(image)
        elif method == 'escpos_usb':
            return self._print_escpos_usb(image)
        else:
            print(f"Unknown print method: {method}")
            return False
    
    def _pdf_to_images(self, pdf_path: str) -> Optional[List[Image.Image]]:
        """Convert PDF to list of PIL Images."""
        # Try PyMuPDF first (no external dependencies like poppler)
        try:
            import fitz
            print(f"Converting PDF using PyMuPDF...")
            doc = fitz.open(pdf_path)
            images = []
            for page in doc:
                pix = page.get_pixmap(dpi=self.DPI)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            doc.close()
            print(f"Successfully converted {len(images)} page(s) using PyMuPDF")
            return images
        except ImportError:
            print("PyMuPDF not available, trying pdf2image...")
        except Exception as e:
            print(f"PyMuPDF failed: {e}, trying pdf2image...")
        
        # Fallback to pdf2image (requires poppler)
        try:
            from pdf2image import convert_from_path
            
            kwargs = {'dpi': self.DPI}
            if self.poppler_path and os.path.exists(self.poppler_path):
                kwargs['poppler_path'] = self.poppler_path
                
            return convert_from_path(pdf_path, **kwargs)
        except ImportError:
            print("Error: Neither PyMuPDF nor pdf2image available")
            return None
        except Exception as e:
            print(f"Error converting PDF with pdf2image: {e}")
            return None
    
    def _trim_whitespace(self, image: Image.Image) -> Image.Image:
        """Remove whitespace from bottom (and optionally top) of image."""
        # Convert to grayscale for analysis
        gray = image.convert('L')
        pixels = list(gray.getdata())
        width = gray.width
        height = gray.height
        
        # Find the last row that has non-white pixels (threshold 250)
        last_content_row = height - 1
        for y in range(height - 1, -1, -1):
            row_start = y * width
            row_pixels = pixels[row_start:row_start + width]
            # Check if row has any non-white pixels
            if any(p < 250 for p in row_pixels):
                last_content_row = y
                break
        
        # Add a small margin at the bottom (e.g., 20 pixels)
        margin = 20
        crop_bottom = min(last_content_row + margin, height)
        
        # Crop the image if we found whitespace
        if crop_bottom < height:
            original_height = height
            image = image.crop((0, 0, width, crop_bottom))
            print(f"Trimmed whitespace: {original_height} -> {crop_bottom} pixels (saved {original_height - crop_bottom}px)")
        
        return image
    
    def _prepare_image(self, image: Image.Image) -> Image.Image:
        """Prepare image for thermal printing (trim whitespace, resize, convert to B&W)."""
        # First trim whitespace from bottom
        image = self._trim_whitespace(image)
        
        # Resize to printer width
        if image.width != self.PRINTER_WIDTH_PIXELS:
            ratio = self.PRINTER_WIDTH_PIXELS / image.width
            new_height = int(image.height * ratio)
            image = image.resize((self.PRINTER_WIDTH_PIXELS, new_height), Image.LANCZOS)
        
        # Convert to grayscale then 1-bit
        image = image.convert('L')
        image = image.point(lambda x: 0 if x < 128 else 255, '1')
        
        return image
    
    def _image_to_raster(self, image: Image.Image) -> bytes:
        """Convert image to ESC/POS raster format."""
        img = self._prepare_image(image)
        
        width_bytes = (img.width + 7) // 8
        height = img.height
        pixels = list(img.getdata())
        
        data = bytearray()
        
        # Process in chunks for stability
        chunk_height = 128
        for y_start in range(0, height, chunk_height):
            y_end = min(y_start + chunk_height, height)
            chunk_lines = y_end - y_start
            
            raster_data = bytearray()
            for y in range(y_start, y_end):
                row_data = bytearray(width_bytes)
                for x in range(img.width):
                    pixel = pixels[y * img.width + x]
                    if pixel == 0:  # Black pixel
                        byte_index = x // 8
                        bit_index = 7 - (x % 8)
                        row_data[byte_index] |= (1 << bit_index)
                raster_data.extend(row_data)
            
            # GS v 0 command
            cmd = bytearray([
                0x1d, 0x76, 0x30, 0x00,
                width_bytes & 0xff, (width_bytes >> 8) & 0xff,
                chunk_lines & 0xff, (chunk_lines >> 8) & 0xff,
            ])
            cmd.extend(raster_data)
            data.extend(cmd)
        
        return bytes(data)
    
    # ==================== PRINT METHODS ====================
    
    def _print_win32(self, image: Image.Image) -> bool:
        """Print using Windows GDI."""
        if not _WIN32_AVAILABLE:
            print("Error: win32print not available")
            return False
            
        try:
            import time
            
            HORZRES = 8
            VERTRES = 10
            LOGPIXELSX = 88
            LOGPIXELSY = 90
            
            printer_name = win32print.GetDefaultPrinter()
            print(f"Using printer: {printer_name}")
            
            # Convert to RGB for Windows printing
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            
            printable_width = hDC.GetDeviceCaps(HORZRES)
            dpi_x = hDC.GetDeviceCaps(LOGPIXELSX)
            dpi_y = hDC.GetDeviceCaps(LOGPIXELSY)
            
            # Scale to 48mm width
            target_width_inches = 48 / 25.4
            target_width_pixels = int(target_width_inches * dpi_x)
            aspect_ratio = image.height / image.width
            target_height_pixels = int(target_width_pixels * aspect_ratio)
            
            doc_name = f"thermal_print_{int(time.time())}"
            hDC.StartDoc(doc_name)
            hDC.StartPage()
            
            dib = ImageWin.Dib(image)
            dib.draw(hDC.GetHandleOutput(), (0, 0, target_width_pixels, target_height_pixels))
            
            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()
            
            print("[OK] Printed via Windows GDI")
            return True
            
        except Exception as e:
            print(f"Error printing via win32: {e}")
            return False
    
    def _print_pyusb(self, image: Image.Image) -> bool:
        """Print using direct USB access (pyusb) - RECOMMENDED for Raspberry Pi."""
        if not _PYUSB_AVAILABLE:
            print("Error: pyusb not available. Install with: pip install pyusb")
            return False
            
        try:
            dev = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
            if dev is None:
                print(f"Error: Printer not found (VID:{hex(self.vendor_id)} PID:{hex(self.product_id)})")
                return False
            
            print(f"Found printer: {dev.product} by {dev.manufacturer}")
            
            # Detach kernel driver if attached
            try:
                if dev.is_kernel_driver_active(0):
                    dev.detach_kernel_driver(0)
                    print("Detached kernel driver")
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
            
            # Initialize printer
            dev.write(ep_addr, b'\x1b\x40')
            
            # Convert and send image
            raster_data = self._image_to_raster(image)
            
            # Send in chunks
            packet_size = 512
            for i in range(0, len(raster_data), packet_size):
                dev.write(ep_addr, raster_data[i:i+packet_size])
            
            # Feed and cut
            dev.write(ep_addr, b'\n\n\n')
            dev.write(ep_addr, b'\x1d\x56\x01')  # Partial cut
            
            print(f"[OK] Printed via pyusb ({len(raster_data)} bytes)")
            return True
            
        except Exception as e:
            print(f"Error printing via pyusb: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _print_device_file(self, image: Image.Image) -> bool:
        """Print directly to /dev/usb/lp0 device file."""
        if not os.path.exists(self.device_path):
            print(f"Error: Device not found: {self.device_path}")
            return False
            
        try:
            # Initialize + raster data + feed + cut
            data = b'\x1b\x40'  # Initialize
            data += self._image_to_raster(image)
            data += b'\n\n\n'
            data += b'\x1d\x56\x01'  # Partial cut
            
            with open(self.device_path, 'wb') as f:
                f.write(data)
            
            print(f"[OK] Printed via device file ({len(data)} bytes)")
            return True
            
        except PermissionError:
            print(f"Error: Permission denied. Run: sudo chmod 666 {self.device_path}")
            return False
        except Exception as e:
            print(f"Error printing via device file: {e}")
            return False
    
    def _print_cups(self, image: Image.Image) -> bool:
        """Print using CUPS (lp command)."""
        if not _CUPS_AVAILABLE:
            print("Error: CUPS not available")
            return False
            
        try:
            import tempfile
            
            # Save image to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name
                image.save(f, 'PNG')
            
            # Build lp command
            cmd = ['lp']
            if self.printer_name:
                cmd.extend(['-d', self.printer_name])
            cmd.append(temp_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if result.returncode == 0:
                print(f"[OK] Printed via CUPS")
                return True
            else:
                print(f"Error: CUPS print failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error printing via CUPS: {e}")
            return False
    
    def _print_escpos_usb(self, image: Image.Image) -> bool:
        """Print using python-escpos USB."""
        if not _ESCPOS_AVAILABLE:
            print("Error: python-escpos not available")
            return False
            
        try:
            from escpos.printer import Usb
            
            p = Usb(self.vendor_id, self.product_id)
            
            # Prepare image
            img = self._prepare_image(image)
            
            # Print using escpos
            p.image(img)
            p.cut()
            p.close()
            
            print("[OK] Printed via python-escpos USB")
            return True
            
        except Exception as e:
            print(f"Error printing via escpos: {e}")
            return False
    
    def test_print(self) -> bool:
        """Print a test receipt."""
        from datetime import datetime
        
        # Create test image
        img = Image.new('RGB', (self.PRINTER_WIDTH_PIXELS, 300), 'white')
        
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            y = 10
            draw.text((img.width//2, y), "THERMAL PRINTER TEST", fill='black', anchor='mt')
            y += 30
            draw.line([(10, y), (img.width-10, y)], fill='black')
            y += 20
            draw.text((10, y), f"Platform: {PLATFORM}", fill='black')
            y += 20
            draw.text((10, y), f"Architecture: {platform.machine()}", fill='black')
            y += 20
            draw.text((10, y), f"Python: {platform.python_version()}", fill='black')
            y += 20
            draw.text((10, y), f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill='black')
            y += 30
            draw.line([(10, y), (img.width-10, y)], fill='black')
            y += 20
            draw.text((img.width//2, y), "Test Successful!", fill='black', anchor='mt')
            
        except Exception as e:
            print(f"Warning: Could not draw text: {e}")
        
        return self.print_image(img)


# Convenience function for backward compatibility
def print_pdf_crossplatform(pdf_path: str, config=None) -> bool:
    """Print a PDF file using the best available method."""
    printer = ThermalPrinter(config)
    return printer.print_pdf(pdf_path)


def print_image_crossplatform(image: Union[Image.Image, str], config=None) -> bool:
    """Print an image using the best available method."""
    printer = ThermalPrinter(config)
    return printer.print_image(image)
