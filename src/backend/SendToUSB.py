import os
import shutil
from time import sleep

import win32api
from tqdm import tqdm
from loguru import logger


def send_by_usb(drive_title: str, files: list[str], eject=True):
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split("\000")[:-1]
    for drive in drives:
        drive_name = win32api.GetVolumeInformation(drive)[0]
        if drive_name == drive_title or drive_name == drive_title.upper():
            for file in tqdm(files, desc="Transfering file to kindle"):
                filename = file.split("\\")[-1]
                path_to_document = f"{drive}documents\\{filename}"
                while True:
                    try:
                        shutil.copy2(file, path_to_document)
                    except FileNotFoundError:
                        logger.info(f"Can't Find {file}, retrying")
                    else:
                        break
                    sleep(1)


            if eject:
                drive_letter = drive.removesuffix("\\")
                os.system(
                    f'powershell $driveEject = New-Object -comObject Shell.Application; $driveEject.Namespace(17).ParseName("""{drive_letter}""").InvokeVerb("""Eject""")')
