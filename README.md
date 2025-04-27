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
python3.9 -m venv pw_python_env
source ./pw_python_env/bin/activate
pip install numpy==1.24.3 cython wheel setuptools
pip install --only-binary=scipy scipy==1.11.4
pip install -r ./requirements.txt
```

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
py -m venv ./pw_python_env
.\pw_python_env\Scripts\activate.ps1
py -m pip install -r ./requirements.txt
py -m pip install pywin32    

- Notes: 
- - TODO: pipinstaller is included in the requirements, though it should not, and should be globally scoped installed, not required in the venv.

## Build project

https://github.com/pyinstaller/pyinstaller/issues/8659
pipinstaller not copying assets requires by escpos. 

pyinstaller ./pw_ws_service/ws_service.py --distpath ./pinoywok-service --add-data "config.yaml:."  --add-data "pw_python_env/Lib/site-packages/escpos/*.json:escpos" --collect-data escpos --noconfirm 

mkdir -p logs