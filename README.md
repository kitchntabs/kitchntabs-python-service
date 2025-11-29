### Important Notes:
- config.yml 
- contains the variables requires by the service, config.example.yml as reference. 

### Requirements
- Python 3+ (3.12 suggested)
- pip install pyinstaller (after env is activated)

### Python Env Linux/Mac instructions

```sh
pyenv install 3.9.16
pyenv local 3.9.16
```

```sh
# Create a python virtual env and install requirements / dependencies
python3.9 -m venv pw_env
source ./pw_env/bin/activate
pip install numpy==1.24.3 cython wheel setuptools
pip install --only-binary=scipy scipy==1.11.4
pip install -r ./requirements.txt
```

# notes:

- test:
- ./service/ws_service test_token test_channel config.prod.mac.yaml log.txt
- C:\Users\USER\DASH\dash-frontend\release\win-unpacked\resources\python-service\ws_service.exe test_token test_channel C:\Users\USER\DASH\dash-frontend\release\win-unpacked\resources\python-service\config.prod.yaml log.txt

### Windows PowerShell & Python 3.12+

# Note: Open a powershell wiundow with administrator privileges.
# Some commands do not run properly on VSCode terminal

Enable long paths:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

Set-ExecutionPolicy Bypass -Scope Process

To isntall choco
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

To install visual studio
choco install visualstudio2022-workload-vctools -y

& "C:\Program Files\kitchntabs\resources\python-service\kt_service.exe" "24|eJHkese14E9Mjv1cBs1W1XFKYGnIyndKvFPYKvWm51de9eec" "private-tenant.1.system" "config.kitchntabs.prod.yaml" "log.txt"
## Requirement Windoiws Development

VStudio C Compiler tools to compile the node zmq library

│ gyp ERR! find VS You need to install the latest version of Visual Studio
│ gyp ERR! find VS including the "Desktop development with C++" workload.
│ gyp ERR! find VS For more information consult the documentation at:
│ gyp ERR! find VS https://github.com/nodejs/node-gyp#on-windows


#### Authorize env activation:


- some packages might required to be compiled, download visual studio build tool  https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install python 3.9 from windows store
py --version
py -3.9.13 --version 

set-executionpolicy RemoteSigned -Scope CurrentUser
New-Alias -Name python -Value python3

#### Create the environment
python -m venv ./pw_env
#### Or just use it if its created
.\pw_env\Scripts\activate.ps1
#### Make sure python resolves to the env
python -m pip install -r ./requirements.txt
python -m pip install pywin32   
python -m pip install pyinstaller

- Notes: 
- - TODO: pipinstaller is included in the requirements, though it should not, and should be globally scoped installed, not required in the venv.

## Build project

https://github.com/pyinstaller/pyinstaller/issues/8659
pipinstaller not copying assets requires by escpos. 

pyinstaller ./pw_ws_service/ws_service.py --distpath ./pinoywok-service --add-data "config.yaml:."  --add-data "pw_python_env/Lib/site-packages/escpos/*.json:escpos" --collect-data escpos --noconfirm 

mac: 
pyinstaller ./src/kt_service.py  --distpath ./service --add-data "config.yaml:."  --add-data "pw_env/lib/python3.9/site-packages/escpos/*.json:escpos" --collect-data escpos --noconfirm 


pyinstaller ./src/kt_service.py --distpath ./ --add-data "config.kitchntabs.prod.yaml:./config.yaml"  --add-data "pw_python_env/Lib/site-packages/escpos/*.json:escpos" --collect-data escpos --noconfirm

mkdir -p logs

# TEST PRINT
{
    "token": ,
    "channel": "private-tenant.1.system"
}

.\pw_env\Scripts\activate.ps1
py ./src/print_service.py 39  "107|TbJOsinJS3X3kZ6sO9s7tNc0wKbdYh67lY2FRRmZ7bf8b610" .\config.prod.yaml log.txt


Here’s a step-by-step guide to install Python from python.org:

1. Uninstall Windows Store Python (optional but recommended)
Open Settings > Apps > Installed apps.
Search for "Python".
Uninstall any "Python" entries from the Microsoft Store.
2. Download Python Installer
Go to: https://www.python.org/downloads/windows/
Click Download Python 3.11.x (or your preferred version).
3. Run the Installer
Double-click the downloaded .exe file.
Important:
Check "Add Python to PATH" at the bottom of the installer window.
Click "Customize installation" if you want to change the install location or features.
Click "Install Now".
4. Verify Installation
Open a new PowerShell or Command Prompt and run:

You should see the python.org version (e.g., Python 3.11.x).

5. (Optional) Create a Virtual Environment
6. Install Your Requirements
Now you can use PyInstaller and other tools without Windows Store limitations!


# WINDOWS BUILD:

& C:/Users/USER/DASH/dash-python-service/pw_env/Scripts/Activate.ps1
python -m PyInstaller ./src/kt_service.py --onefile --distpath ./service --add-data ./config.kitchntabs.prod.yaml:. --add-data pw_env/Lib/site-packages/escpos/*.json:escpos --collect-data escpos --noconfirm


# WINDOWS THROUBLESHOOTING
ImportError: DLL load failed while importing _win32sysloader: No se puede encontrar el módulo especificado.
...
AttributeError: Failed to retrieve attribute __file__ from module pythoncom

Test-Path "pw_env\Lib\site-packages\pywin32_system32\pythoncom39.dll"
Test-Path "pw_env\Lib\site-packages\pywin32_system32\pywintypes39.dll"

New-Item -ItemType Directory -Path "C:\Program Files\kitchntabs\resources\python-service\_internal" -Force

If the files do not exists, reinstall:

# Sometimes is necessary to reinstalll pywin32
py -m pip uninstall pywin32
python -m pip install pywin32

# TEST
& "C:\Program Files\kitchntabs\resources\python-service\kt_service.exe" "24|eJHkese14E9Mjv1cBs1W1XFKYGnIyndKvFPYKvWm51de9eec" "private-tenant.1.system" "config.kitchntabs.prod.yaml" "log.txt"


& "C:\Users\USER\DASH\dash-python-service\\kt_service\\kt_service.exe" "24|eJHkese14E9Mjv1cBs1W1XFKYGnIyndKvFPYKvWm51de9eec" "private-tenant.1.system" "config.kitchntabs.prod.yaml" "log.txt"

Test-Path "C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.11_3.11.2544.0_x64__qbz5n2kfra8p0\python311.dll"
Test-Path "C:\Program Files\kitchntabs\resources\python-service\_internal\python311.dll"


PyInstaller cannot embed the Python DLL (python311.dll) inside the .exe when building with the Windows Store version of Python. This is a known limitation due to Windows Store Python's packaging and permissions.
With python.org Python, PyInstaller can usually bundle the DLL automatically in onefile mode.
With Windows Store Python, you must manually copy the DLL next to your executable.




