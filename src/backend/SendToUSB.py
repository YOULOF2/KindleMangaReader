import win32api
from pathlib import Path
import shutil
from src.backend.Utils import loop

def send_by_usb(drive_title: str, files: list[str]):
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split("\000")[:-1]
    for drive in drives:
        drive_name = win32api.GetVolumeInformation(drive)[0]
        if drive_name == drive_title or drive_name == drive_title.upper():            
            for file in loop(files, desc="Transfering file to kindle"):
                filename = file.split("\\")[-1]
                path_to_document = f"{drive}documents\\{filename}"
                shutil.copy2(file, path_to_document)
                
            
        