import os
from subprocess import check_call, STDOUT
from pathlib import Path
from loguru import logger
from time import time
from backend.Utils import loop

_REALESRGAN_VULKAN_PATH = str(Path(Path(__file__).parent, "realesrgan-ncnn-vulkan.exe"))


def vulkan_upscale_images(input_images: list[str]):
    start_time = time()

    for file in loop(input_images, desc="Upscalling Images", colour="RED"):
        loop_start_time = time()
        file_extension = file.split("\\")[-1].split(".")[-1]

        command = (
            _REALESRGAN_VULKAN_PATH
            + f' -i "{file}" -o "{file}" -n realesrgan-x4plus-anime -f {file_extension}'
        )

        DEVNULL = open(os.devnull, "wb")
        try:
            check_call(command, stdout=DEVNULL, stderr=STDOUT)
        finally:
            DEVNULL.close()
            
            
        loop_end_time = time()
        loop_processing_time = round((loop_end_time - loop_start_time)/60, 2)
        file_name = file.split('\\')[-1]
        
        logger.info(f"Upscaled {file_name} in {loop_processing_time} minutes")
   

    end_time = time()
    processing_time = end_time - start_time
    logger.info(f"Upscaled {len(input_images)} images in {processing_time} seconds.")
