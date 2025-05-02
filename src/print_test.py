import os
import platform
import subprocess
from pinoywok import config
import sys
from pinoywok.args import args
from pinoywok.config import config
from pinoywok.print import printPil

WINDOWS_OS = False
if platform.system() == 'Windows' or os.name == 'nt':
    WINDOWS_OS = True

args.set_key("config", sys.argv[1] if len(sys.argv) > 1 else 'config.dev.yaml')

#Load config
_args = args.get_args()
config.load_config(_args.config)

def print_order():
    # Download a sample PDF

    sample_file = "./output/tab_39.pdf"

    # Try converting it
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(sample_file, 300, poppler_path=config.get('POPPLER_PATH'))
        print(f"Successfully converted sample PDF to {len(images)} images")

        if WINDOWS_OS == True:
                for i, image in enumerate(images):
                    printPil(image)
        else:
            if sys.platform == 'darwin':  # for Mac OS
                subprocess.call(['open', sample_file])
            elif sys.platform == 'linux':  # for Linux
                subprocess.call(['xdg-open', sample_file])
            elif sys.platform == 'win32':  # for Windows
                subprocess.call(['start', sample_file])
            else:
                print("Unsupported platform")
    except Exception as e:
        print(f"Error converting sample PDF: {e}")

def main() -> None:
     print_order()

if __name__ == "__main__":
    main()