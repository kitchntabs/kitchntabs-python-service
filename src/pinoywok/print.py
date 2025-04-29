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

WINDOWS_OS = False
if platform.system() == 'Windows' or os.name == 'nt':
    WINDOWS_OS = True

if WINDOWS_OS:
    try:
        import win32print
        _WIN32PRINT = True
    except ImportError:
        print('Warning: missing lib... win32print')

    try:
        import win32ui
    except ImportError:
        print('Warning: missing lib... win32ui')
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
#from pinoywok.asset import pdf2png
import pinoywok.helpers
from pinoywok.logging import log
import subprocess
# Initialize audio player with error handling
#try:
#    from pinoywok.audio_player import AudioPlayer
#    audio_player = AudioPlayer()
#    _AUDIO_AVAILABLE = True
#except Exception as e:
#    print(f"Warning: Audio player initialization failed: {e}")
#    # Create a dummy audio player that does nothing
#    class DummyAudioPlayer:
#        def __getattr__(self, name):
#            return lambda *args, **kwargs: None
#    audio_player = DummyAudioPlayer()
#    _AUDIO_AVAILABLE = False



from pinoywok.config import config

'''

{
    "notifiable": null,
    "modelInstance": 7,
    "notificationPayload": {
        "class": "TenantChannelMessageNotification",
        "title": "Canal Tenant",
        "message": "Tenant Message",
        "notificationPayload": {
            "tab_id": 7,
            "file_path": "tabs/sale_notes/tab_7_1744936263.pdf",
            "tenant_id": 1
        }
    },
    "model": "Domain\\App\\Models\\Tab\\Tab",
    "targetType": "user",
    "mailSubject": "Canal Tenant",
    "data": {
        "tab_id": 7,
        "file_path": "tabs/sale_notes/tab_7_1744936263.pdf",
        "tenant_id": 1
    },
    "type": "print",
    "timestamp": "2025-04-17T20:31:05-04:00",
    "targetRoles": null,
    "notify": "none"
}

'''

def print_order(j,token,output,log_file,config_file):
    
    config.load_config(config_file)
    API = f"{config.get_config('API_SCHEME')}://{config.get_config('API_HOST')}{':' + str(config.get_config('API_PORT')) if config.get_config('WS_PORT') else ''}/api/"

    tab_id = j['data']['tab_id']
    download_url = f"{API}tab/tab/{tab_id}/download"
    output_file = os.path.join(output, f"tab_{tab_id}.pdf")
    
    response = requests.get(download_url, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, stream=True)    
    log(f"Download URL: {download_url}")
    log(f"Bearer Token: {token}")
    log(f"Output File: {output_file}")
    log(f"Tab ID: {tab_id}")
    
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)    
 
    if WINDOWS_OS:
        try:
      
            images = convert_from_path(output_file, dpi=203,poppler_path=config.get("POPPLER_PATH"))
            
            # Connect to printer
            #if printer_type == "usb":
            printer = Usb(config.get("PRINTER_VENDOR"), config.get("PRINTER_PRODUCT"))
            #elif printer_type == "network":
            #    printer = Network(printer_params.get("ip"), printer_params.get("port", 9100))
            #elif printer_type == "file":
            #    printer = File(printer_params.get("path"))
            
            # Print each page
            for img in images:
                # Resize to fit receipt width
                width, height = img.size
                max_width = config.get("PRINTER_MAX_WIDTH", 512)
                if width > max_width:
                    ratio = max_width / width
                    img = img.resize((max_width, int(height * ratio)))
                log(f"Printing page {images.index(img) + 1} of {len(images)}")
                # Print and cut
                printer.image(img)
                printer.cut()
                
            return True
        except Exception as e:
            log(f"ESC/POS printing failed: {e}")

    else:
        if sys.platform == 'darwin':  # for Mac OS
            subprocess.call(['open', output_file])
        elif sys.platform == 'linux':  # for Linux
            subprocess.call(['xdg-open', output_file])
        elif sys.platform == 'win32':  # for Windows
            subprocess.call(['start', output_file])
        else:
            print("Unsupported platform")
            
            
def print_order_test(j,token,output,log_file,config_file):
    
    config.load_config(config_file)
    API = f"{config.get_config('API_SCHEME')}://{config.get_config('API_HOST')}{':' + str(config.get_config('API_PORT')) if config.get_config('WS_PORT') else ''}/api/"

    tab_id = j['data']['tab_id']
    download_url = f"{API}tab/tab/{tab_id}/download"
    output_file = os.path.join(output, f"tab_{tab_id}.pdf")
    
    response = requests.get(download_url, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, stream=True)    
    log(f"Download URL: {download_url}")
    log(f"Bearer Token: {token}")
    log(f"Output File: {output_file}")
    log(f"Tab ID: {tab_id}")
    
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)    
 
    
    try:
    
        images = convert_from_path(output_file, dpi=203,poppler_path=config.get("POPPLER_PATH"))
        
        # Connect to printer
        #if printer_type == "usb":
        printer = Usb(config.get("PRINTER_VENDOR"), config.get("PRINTER_PRODUCT"))
        #elif printer_type == "network":
        #    printer = Network(printer_params.get("ip"), printer_params.get("port", 9100))
        #elif printer_type == "file":
        #    printer = File(printer_params.get("path"))
        
        # Print each page
        for img in images:
            # Resize to fit receipt width
            width, height = img.size
            max_width = config.get("PRINTER_MAX_WIDTH", 512)
            if width > max_width:
                ratio = max_width / width
                img = img.resize((max_width, int(height * ratio)))
            log(f"Printing page {images.index(img) + 1} of {len(images)}")
            # Print and cut
            printer.image(img)
            printer.cut()
            
        return True
    except Exception as e:
        log(f"ESC/POS printing failed: {e}")

    
    
def printer(image):
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

    return

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