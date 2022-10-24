import tqdm
import random
import requests
from pathlib import Path
import glob
import os


PATH_TO_TEMP = Path(Path(__file__).resolve().parent.parent, "temp")


def loop(*args, **kwargs):
    desciption = kwargs["description"]
    del kwargs["description"]

    progressbar = tqdm.tqdm(*args, **kwargs, disable=False)
    progressbar.set_description(desciption)

    return progressbar


def get_request_for(url: str) -> dict:
    request = requests.get(url)
    request.raise_for_status()
    return request.json()

def clear_temp():
    all_files = glob.glob(f"{PATH_TO_TEMP}/*")
    for file in all_files:
        print(file)
        os.remove(file)
        
def get_file_size_for(path_to_file: str) -> float:
    size_in_bytes = os.path.getsize(path_to_file)
    size_in_mb = round(size_in_bytes/1048576, 1)
    return size_in_mb