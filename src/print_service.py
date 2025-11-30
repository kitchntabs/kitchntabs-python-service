import os
import threading
import sys
import json as json_module
import platform
import requests
import time
from datetime import datetime
from pinoywok import printer as pinoywok_printer
from pinoywok.args import args
from pinoywok.config import config
from pinoywok.logging import log
from pinoywok.thermal_printer import ThermalPrinter

# Parse arguments - supports three modes:
# Mode 1 (Test mode): print_service.py "test" <config_file> <log_file>
# Mode 2 (URL mode): print_service.py <url> <config_file> <log_file>
# Mode 3 (Tab mode): print_service.py <tab_id> <token> <config_file> <log_file>

# Detect mode based on first argument
first_arg = sys.argv[1] if len(sys.argv) > 1 else None
is_test_mode = first_arg is None or first_arg == "" or first_arg.lower() == "test"
is_url_mode = first_arg and (first_arg.startswith('http://') or first_arg.startswith('https://'))

if is_test_mode:
    # Test mode: print a test page
    args.set_key("test", True)
    args.set_key("url", None)
    args.set_key("tab_id", None)
    args.set_key("token", None)
    args.set_key("config", sys.argv[2] if len(sys.argv) > 2 else 'config.yaml')
    args.set_key("log", sys.argv[3] if len(sys.argv) > 3 else 'log.txt')
elif is_url_mode:
    # URL mode: direct PDF URL
    args.set_key("test", False)
    args.set_key("url", first_arg)
    args.set_key("tab_id", None)
    args.set_key("token", None)
    args.set_key("config", sys.argv[2] if len(sys.argv) > 2 else 'config.yaml')
    args.set_key("log", sys.argv[3] if len(sys.argv) > 3 else 'log.txt')
else:
    # Tab mode: tab_id + token to construct API URL
    args.set_key("test", False)
    args.set_key("url", None)
    args.set_key("tab_id", first_arg)
    args.set_key("token", sys.argv[2] if len(sys.argv) > 2 else None)
    args.set_key("config", sys.argv[3] if len(sys.argv) > 3 else 'config.yaml')
    args.set_key("log", sys.argv[4] if len(sys.argv) > 4 else 'log.txt')

#Load config
_args = args.get_args()
config.load_config(_args.config)

def print_startup_info():
    """Print diagnostic information about the print service."""
    print("=" * 50, flush=True)
    print("Print Service Starting", flush=True)
    print("=" * 50, flush=True)
    print(f"Platform: {platform.system()}", flush=True)
    print(f"Architecture: {platform.machine()}", flush=True)
    print(f"Python: {platform.python_version()}", flush=True)
    
    # Check thermal printer capabilities
    try:
        printer = ThermalPrinter(config)
        status = printer.get_status()
        print(f"Printer Status:", flush=True)
        print(f"  Vendor ID: {status['vendor_id']}", flush=True)
        print(f"  Product ID: {status['product_id']}", flush=True)
        print(f"  Recommended method: {status['recommended']}", flush=True)
        print(f"  Available methods:", flush=True)
        for method, available in status['methods'].items():
            icon = "✅" if available else "❌"
            print(f"    {icon} {method}", flush=True)
    except Exception as e:
        print(f"Warning: Could not check printer status: {e}", flush=True)
    
    print("=" * 50, flush=True)

def print_order_threaded(tab_id, token, output, log, cfg):
    print(f"tab_id: {tab_id}", flush=True)
    if tab_id is not None:
        threading.Thread(target=pinoywok_printer.print_order, args=(tab_id,token,output,log,cfg)).start()
    else:
        print("Error: tab_id not found", flush=True)

def print_order(tab_id,token,log,cfg):
        folder = log
        parent_folder = os.path.dirname(folder)
        grandparent_folder = os.path.dirname(parent_folder)
        output = os.path.join(grandparent_folder,"./output/")
        if not os.path.exists(output):
            os.mkdir(output)
        try:
            print_order_threaded(tab_id,token,output,log,cfg)
            return
        except Exception as e:
            print(f"print_order - Error Printing: {e}", flush=True)

def print_from_url(url, log_path, cfg):
    """Download and print a PDF from a URL."""
    print(f"Downloading PDF from: {url}", flush=True)
    
    # Create output directory
    folder = log_path
    parent_folder = os.path.dirname(folder)
    grandparent_folder = os.path.dirname(parent_folder)
    output = os.path.join(grandparent_folder, "./output/")
    if not os.path.exists(output):
        os.makedirs(output, exist_ok=True)
    
    # Generate output filename from URL or timestamp
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    output_file = os.path.join(output, f"print_{url_hash}_{int(time.time())}.pdf")
    
    try:
        # Download PDF
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        print(f"Response status: {response.status_code}", flush=True)
        print(f"Content-Type: {content_type}", flush=True)
        
        # Save PDF to file
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"PDF saved to: {output_file}", flush=True)
        
        # Print using thermal printer
        printer = ThermalPrinter(config)
        status = printer.get_status()
        print(f"Printer Status:", flush=True)
        print(f"  Recommended method: {status['recommended']}", flush=True)
        
        success = printer.print_pdf(output_file)
        
        if success:
            print(f"✅ Successfully printed PDF from URL", flush=True)
        else:
            print(f"❌ Failed to print PDF", flush=True)
        
        return success
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading PDF: {e}", flush=True)
        return False
    except Exception as e:
        print(f"❌ Error printing PDF: {e}", flush=True)
        return False


def print_test_page():
    """Print a test page to verify printer connectivity using ThermalPrinter.test_print()."""
    print("=" * 50, flush=True)
    print("🖨️  PRINTING TEST PAGE", flush=True)
    print("=" * 50, flush=True)
    
    try:
        printer = ThermalPrinter(config)
        status = printer.get_status()
        
        print(f"Printer Status:", flush=True)
        print(f"  Vendor ID: {status['vendor_id']}", flush=True)
        print(f"  Product ID: {status['product_id']}", flush=True)
        print(f"  Recommended method: {status['recommended']}", flush=True)
        print(f"  Available methods:", flush=True)
        for method, available in status['methods'].items():
            icon = "✅" if available else "❌"
            print(f"    {icon} {method}", flush=True)
        
        # Use the built-in test_print() method from ThermalPrinter
        print(f"\nSending test page to printer...", flush=True)
        success = printer.test_print()
        
        if success:
            print(f"\n✅ Test page printed successfully!", flush=True)
        else:
            print(f"\n❌ Failed to print test page", flush=True)
        
        return success
        
    except Exception as e:
        print(f"❌ Error printing test page: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    print_startup_info()
    
    # Check which mode we're in
    if _args.test:
        # Test mode: print a test page
        print_test_page()
    elif _args.url:
        # URL mode: print directly from URL
        print_from_url(_args.url, _args.log, _args.config)
    elif _args.tab_id:
        # Tab mode: print order by tab_id
        print_order(_args.tab_id, _args.token, _args.log, _args.config)
    else:
        # Fallback to test mode if nothing provided
        print("No URL or tab_id provided - printing test page", flush=True)
        print_test_page()

if __name__ == "__main__":
    main()