import tqdm
import random
from pathlib import Path
import glob
import os
from PIL import Image
from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

from loguru import logger

import gevent.monkey

gevent.monkey.patch_all()

import requests


PATH_TO_TEMP = Path(Path(__file__).resolve().parent.parent, "temp")


def loop(*args, **kwargs):
    progressbar = tqdm.tqdm(*args, **kwargs, disable=False)
    return progressbar


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
    image = Image.open(ImageFilePath, "r")
    image_size = image.size
    width = image_size[0]
    height = image_size[1]

    wpercent = 2480 / float(width)
    hsize = int((float(height) * float(wpercent)))
    image = image.resize((2480, hsize), Image.Resampling.LANCZOS)
    image.save(ImageFilePath)

    logger.info("Image has been resized")
    
    
