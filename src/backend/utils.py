import glob
import os
from pathlib import Path

from PIL import Image
from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

from loguru import logger

import gevent.monkey

gevent.monkey.patch_all()

import requests


PATH_TO_TEMP = Path(Path(__file__).resolve().parent.parent, "temp")


def get_request_for(url: str) -> dict:
    request = requests.get(url)
    request.raise_for_status()
    return request.json()


def clear_temp():
    execlude = [f"{PATH_TO_TEMP}\\.gitignore"]
    all_files = glob.glob(f"{PATH_TO_TEMP}\\*")

    if len(all_files) == 0:
        return

    for file in all_files:
        if file not in execlude:
            print(file)
            os.remove(file)


def get_file_size_for(path_to_file: str) -> float:
    size_in_bytes = os.path.getsize(path_to_file)
    size_in_mb = round(size_in_bytes / 1048576, 1)
    return size_in_mb


def reformate_image(ImageFilePath):
    image = Image.open(ImageFilePath, "r").convert("RGB")
    image_width, image_height = image.size

    background = Image.new("RGB", (2480, 3508), (0, 0, 0, 1))
    background_width, background_height = background.size

    wpercent = 2480 / float(image_width)
    hsize = int((float(image_height) * float(wpercent)))
    image = image.resize((2480, hsize), Image.Resampling.LANCZOS)

    offset = ((background_width - image_width) // 2, (background_height - image_height) // 2)

    background.paste(image, offset)

    image.save(ImageFilePath)

    logger.info("Image has been resized")
    
    
