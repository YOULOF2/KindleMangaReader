from src.backend.ConvertToMOBI.EpubMaker import EPubMaker
from src.backend.Utils import PATH_TO_TEMP, get_file_size_for
from pathlib import Path
import os
import shutil
from uuid import uuid4

PATH_TO_KINDLEGEN = str(Path(Path(__file__).parent, "kindlegen.exe"))


def list_to_mobi(
    input_list: list,
    mobi_name: str,
):    
    uuid_code = uuid4().hex
    input_dir = str(Path(PATH_TO_TEMP, f"{mobi_name}-{uuid_code}\\"))
    os.makedirs(input_dir)
    
    for index, file in enumerate(input_list):
        file_name = f"{index} " + file.split('\\')[-1]
                
        dst_filepath = str(Path(Path(input_dir, file_name)))
        shutil.copy(src=file, dst=dst_filepath)
    
    epub_output_file = str(Path(PATH_TO_TEMP, f"{mobi_name}-as-epub.epub"))
    EPubMaker(
        input_dir=input_dir,
        output_file=epub_output_file,
        epub_name=mobi_name,
        author_name="KindleMangaReader",
        publisher_name="YOULOF2",
    ).make_epub()
    
    command = f'{PATH_TO_KINDLEGEN} "{epub_output_file}" -c0 -o "{mobi_name}.mobi"'
    os.system(command)
    return str(Path(PATH_TO_TEMP, f"{mobi_name}.mobi"))
