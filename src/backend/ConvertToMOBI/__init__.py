from src.backend.ConvertToMOBI.EpubMaker import EPubMaker
from src.backend.Utils import PATH_TO_TEMP, get_file_size_for
from pathlib import Path
import os
import shutil
from uuid import uuid4
import re
from loguru import logger
import subprocess

PATH_TO_KINDLEGEN = str(Path(Path(__file__).parent, "kindlegen.exe"))
FILES_TO_COPY = ["cnf.jpg", "tec.jpg", "tev.jpg"]


def list_to_mobi(
    input_list: list,
    mobi_name: str,
):    
    cleaned_input_list = list(dict.fromkeys(input_list))
    if len(cleaned_input_list) != len(input_list):
        logger.info("Duplicate items removed.")
    
    mobi_name = re.sub(r'[\\/*?:"<>|]', "", mobi_name)

    uuid_code = uuid4().hex
    input_dir = str(Path(PATH_TO_TEMP, f"{mobi_name}-{uuid_code}\\"))
    os.makedirs(input_dir)

    for index, file in enumerate(cleaned_input_list):
        file_name = file.split("\\")[-1]
        indexed_file_name = f"{index} " + file_name

        dst_filepath = str(Path(input_dir, indexed_file_name))
        
        if file_name in FILES_TO_COPY:
            shutil.copy(src=file, dst=dst_filepath)
        else:
            shutil.move(src=file, dst=dst_filepath)

    epub_output_file = str(Path(PATH_TO_TEMP, f"{mobi_name}-as-epub.epub"))
    EPubMaker(
        input_dir=input_dir,
        output_file=epub_output_file,
        epub_name=mobi_name,
        author_name="KindleMangaReader",
        publisher_name="YOULOF2",
    ).make_epub()
    logger.info(f"Created {mobi_name}.epub")

    command = f'{PATH_TO_KINDLEGEN} "{epub_output_file}" -c0 -o "{mobi_name}.mobi"'
    subprocess.Popen(command, shell=True).wait()
    
    mobi_file_path = str(Path(PATH_TO_TEMP, f"{mobi_name}.mobi"))
    logger.info(mobi_file_path)
    
    return mobi_file_path
