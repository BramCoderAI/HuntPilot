You need miniconda or anaconda and create your environment with Python=3.11.
After creating and activate your conda environments you need to install all the packages in "requirements.txt" or if you want you can install manually with the command "pip install PyQt6 PyInstaller" PyInstaller is optional but recommanded if you want to create your executable.
If you want to use PyInstaller make this command in your console open into the "HuntPilot" folder "PyInstaller --noconfirm --clean --windowed --name HuntPilot --collect-all PyQt6 --hidden-import PyQt6.sip main.py"
