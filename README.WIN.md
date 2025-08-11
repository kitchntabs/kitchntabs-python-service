# Windows Setup Guide for dash-python-service

> **Important:**  
> This project requires **Python 3.11.x** from [python.org](https://www.python.org/downloads/windows/).  
> **Python 3.12+ is NOT compatible** with PyInstaller and some dependencies.

---

## 1. Uninstall Microsoft Store Python

- Open **Settings > Apps > Installed apps**.
- Search for "Python".
- Uninstall any "Python" entries from the Microsoft Store.

---

## 2. Install Python 3.11.x from python.org

- Download Python 3.11.x installer:  
  [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
- Run the installer:
  - **Check "Add Python to PATH"** before installing.
  - Click **Install Now**.

---

## 3. Install Visual Studio Build Tools (for C++ compilation)

- Open PowerShell as Administrator.
- Install Chocolatey (if not installed):
  ```powershell
  Set-ExecutionPolicy Bypass -Scope Process -Force; `
    [System.Net.ServicePointManager]::SecurityProtocol = `
    [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
  ```
- Install Visual Studio C++ Build Tools:
  ```powershell
  choco install visualstudio2022-workload-vctools -y
  ```

---

## 4. Enable Long Paths (recommended)

```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

---

## 5. Create and Activate Virtual Environment

```powershell
python -m venv pw_env
.\pw_env\Scripts\activate.ps1
```

---

## 6. Install Project Requirements

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pywin32
```

---

## 7. Install PyInstaller Globally

> **Note:** PyInstaller must be installed globally, not inside the virtual environment.

```powershell
pip install pyinstaller
```

---

## 8. Build the Project

```powershell
python -m PyInstaller ./src/kt_service.py --onefile --distpath ./service `
  --add-data ./config.kitchntabs.prod.yaml:. `
  --add-data pw_env/Lib/site-packages/escpos/*.json:escpos `
  --collect-data escpos --noconfirm
```

---

## 9. Troubleshooting

- If you see DLL errors (e.g., `ImportError: DLL load failed while importing _win32sysloader`):
  - Reinstall pywin32:
    ```powershell
    python -m pip uninstall pywin32
    python -m pip install pywin32
    ```
  - Check for DLL files:
    ```powershell
    Test-Path "pw_env\Lib\site-packages\pywin32_system32\pythoncom39.dll"
    Test-Path "pw_env\Lib\site-packages\pywin32_system32\pywintypes39.dll"
    ```

- If you see errors about missing `python39.dll`:
  - Copy the DLL from your Python installation to your deployment folder if needed.

---

## 10. Running the Service

```powershell
.\pw_env\Scripts\activate.ps1
python ./src/print_service.py 39 "your_token" .\config.kitchntabs.prod.yaml log.txt
```
Or run the built executable:
```powershell
& "C:\Program Files\kitchntabs\resources\python-service\kt_service.exe" "your_token" "your_channel" "config.kitchntabs.prod.yaml" "log.txt"
```

---

## Notes

- **Do NOT use Python 3.12 or newer.**
- Always use a virtual environment for isolation.
- Some dependencies require Visual Studio C++ Build Tools.
- **PyInstaller must be installed globally with pip, not in the virtual environment.**
- If you encounter issues, check the troubleshooting section above.

---

## References

- [Python 3.9.x for Windows](https://www.python.org/downloads/windows/)
- [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)


# necessary to reinstalll pywin32
python -m pip uninstall pywin32
python -m pip install pywin32

#
Remove-Item Alias:python
# Remove the old virtualenv
Remove-Item -Recurse -Force .\pw_env

# Create a new virtualenv
python -m venv .\pw_env

# Activate it
.\pw_env\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install your requirements
python -m pip install -r requirements.txt

# Print service
python -m pip install pywin32

# Install pyinstaller
pip install PyInstaller 

# Test pyinstaller
pyinstaller --version

# Build
pnpm build-win