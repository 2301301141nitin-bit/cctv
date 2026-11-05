import os
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("=== Building Antigravity CCTV Windows Executable ===")
    
    # Path to custom PyInstaller command
    pyinstaller_bin = os.path.join(BASE_DIR, "venv", "Scripts", "pyinstaller.exe")
    if not os.path.exists(pyinstaller_bin):
        pyinstaller_bin = "pyinstaller"
        
    cmd = [
        pyinstaller_bin,
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=AntigravityCCTV",
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=cv2",
        "--hidden-import=faiss",
        "--hidden-import=transformers",
        "--hidden-import=torch",
        "--hidden-import=sqlalchemy",
        "desktop_app.py"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=BASE_DIR)
    
    if res.returncode == 0:
        dist_dir = os.path.join(BASE_DIR, "dist", "AntigravityCCTV")
        print(f"\n=======================================================")
        print(f" SUCCESS! Build completed.")
        print(f" Standalone Windows App location:")
        print(f" {dist_dir}")
        print(f" Executable: {os.path.join(dist_dir, 'AntigravityCCTV.exe')}")
        print(f"=======================================================\n")
    else:
        print("\n[ERROR] Build failed. Check logs above.\n")

if __name__ == "__main__":
    build()
