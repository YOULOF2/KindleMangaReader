from PIL import Image
from fpdf import FPDF
from PyPDF2 import PdfMerger
from pathlib import Path
import pickle
from src.backend.Utils import get_file_size_for, get_request_for, PATH_TO_TEMP, loop, reformate_image
from uuid import uuid4
from humanize import number
import validators
from src.backend.ConvertToMOBI import list_to_mobi
from uuid import uuid4
from loguru import logger
from src.backend.RealESRGAN import vulkan_upscale_images


import grequests
import requests


class Manga:
    def __init__(
        self,
        id: str = None,
        title: str = None,
        description: str = None,
        status: str = None,
        cover: str = None,
        volumes: list = None,
    ) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.cover = cover
        self.volumes = volumes

    def __str__(self):
        return f"{self.title = }\n{self.description = }\n{self.status = }\n{self.cover = }\nNumber of volumes = {len(self.volumes)}"

    def save(self) -> str:
        object_id = str(uuid4()).split("-")[0]
        with open(f"{PATH_TO_TEMP}\\{object_id}.manga", "wb") as pickle_file:
            pickle.dump(self, pickle_file)

        return object_id

    @classmethod
    def load(cls, object_id: str):
        with open(f"{PATH_TO_TEMP}\\{object_id}.manga", "rb") as pickle_file:
            instance = pickle.load(pickle_file)
        return instance


class MangaVolume:
    def __init__(
        self,
        title: str = None,
        chapters: list = None,
        cover: str = None,
        manga: Manga = None,
    ) -> None:
        self.title = title
        self.chapters = chapters
        self.cover = cover
        self.manga = manga

    def to_pdf(self, in_parts=True, data_saver=True, upscale=False) -> list[str]:
        all_pdfs = []

        if "https://" in self.cover:
            response = requests.get(self.cover)
            hash_cover_filename = self.cover.split("/")[-1]
            cover_filename = str(Path(PATH_TO_TEMP, hash_cover_filename))

            # Dowloads cover as image
            with open(cover_filename, "wb") as file:
                file.write(response.content)

        else:
            cover_filename = self.cover

        # Converts Cover image to pdf
        cover_pdf = FPDF()

        cover_image = Image.open(cover_filename)
        cover_width, cover_height = cover_image.size

        # convert pixel in mm with 1px=0.264583 mm
        cover_width, cover_height = float(cover_width * 0.264583), float(
            cover_height * 0.264583
        )

        #  make sure image size is not greater than the pdf format size
        cover_width = cover_width if cover_width < 210 else 210
        cover_height = cover_height if cover_height < 297 else 297

        cover_pdf.add_page()

        cover_pdf.image(cover_filename, 0, 0, cover_width, cover_height)

        cover_pdf_filename = f"{str(PATH_TO_TEMP)}\\volume {self.title} cover.pdf"
        cover_pdf.output(cover_pdf_filename, "F")

        for chapter in loop(
            self.chapters, desc="Converting Chapters to PDFs", colour="RED"
        ):
            all_pdfs.insert(0, chapter.to_pdf(data_saver=data_saver, upscale=upscale))

        # Add cover image pdf to all_pdfs
        all_pdfs.insert(0, cover_pdf_filename)

        all_volume_parts = set([])
        total_file_size = 0
        merger = PdfMerger()
        if in_parts:
            for volume_part, pdf in loop(
                enumerate(all_pdfs, start=1), desc="Creating Volume"
            ):
                if total_file_size <= 11:
                    total_file_size += get_file_size_for(pdf)

                    merger.append(pdf)
                else:
                    filename = (
                        f"{PATH_TO_TEMP}\\Volume {self.title} Part {volume_part}.pdf"
                    )
                    merger.write(filename)
                    all_volume_parts.add(filename)

                    merger.close()
                    merger = PdfMerger()

                    total_file_size = 0

                    merger.append(pdf)
                    total_file_size += get_file_size_for(pdf)

                if self.title == "UnGrpd":
                    filename = f"{PATH_TO_TEMP}\\{self.manga.title} {self.title} Volume Part {volume_part}.pdf"
                else:
                    filename = f"{PATH_TO_TEMP}\\{self.manga.title} {number.ordinal(self.title)} Volume Part {volume_part}.pdf"

        else:
            for pdf in loop(all_pdfs, desc="Creating Volume"):
                merger.append(pdf)

            if self.title == "UnGrpd":
                filename = f"{PATH_TO_TEMP}\\{self.manga.title} {self.title} Volume.pdf"
            else:
                filename = f"{PATH_TO_TEMP}\\{self.manga.title} {number.ordinal(self.title)} Volume.pdf"

        pdf_title = filename.split("\\")[-1].removesuffix(".pdf")

        merger.add_metadata(
            {
                "/Author": "KinldeMangaReader",
                "/Title": pdf_title,
            }
        )
        merger.write(filename)

        all_volume_parts.add(filename)

        merger.close()

        return list(all_volume_parts)

    def to_mobi(self, data_saver=True, upscale=False) -> str:
        all_images = []

        for chapter in self.chapters:
            logger.info(f"Downloading Images for {self.title} volume")
            chapter_images = chapter.download_imgs(data_saver=data_saver, upscale=upscale)
            all_images = chapter_images + all_images

        if validators.url(self.cover):
            response = requests.get(self.cover)
            hash_cover_filename = self.cover.split("/")[-1]
            cover_filename = str(Path(PATH_TO_TEMP, hash_cover_filename))

            # Dowloads cover as image
            with open(cover_filename, "wb") as file:
                file.write(response.content)
        else:
            cover_filename = self.cover

        all_images.insert(0, cover_filename)
        
        end_of_volume_page = str(Path(Path(__file__).parent, "assets\\tev.jpg"))
        
        all_images.append(end_of_volume_page)

        if self.title == "UnGrpd":
            filename = f"{self.manga.title} {self.title} Volume"
        else:
            filename = f"{self.manga.title} {number.ordinal(self.title)} Volume"

        mobi_path = list_to_mobi(
            input_list=all_images,
            mobi_name=filename,
        )

        return mobi_path

    def __str__(self):
        return f"{self.title = }"


class MangaChapter:
    def __init__(
        self,
        number: float,
        id: str,
        manga_obj: Manga,
        volume_obj: MangaVolume,
    ) -> None:
        self.number = number
        self.id = id
        self.manga = manga_obj
        self.volume = volume_obj

    def download_imgs(self, data_saver=True, upscale=False) -> list[str]:
        request_json = get_request_for(
            f"https://api.mangadex.org/at-home/server/{self.id}"
        )

        base_url = request_json["baseUrl"]

        chapter_data = request_json["chapter"]
        chapter_hash = chapter_data["hash"]
        if data_saver:
            chapter_image_filenames = chapter_data["dataSaver"]
        else:
            chapter_image_filenames = chapter_data["data"]

        files = []
        request_urls = []
        for chapter_image_filename in chapter_image_filenames:
            if data_saver:
                image_url = (
                    f"{base_url}/data-saver/{chapter_hash}/{chapter_image_filename}"
                )
            else:
                image_url = f"{base_url}/data/{chapter_hash}/{chapter_image_filename}"
                
            request_urls.append(image_url)

        requests = [grequests.get(url) for url in request_urls]
        responses = grequests.map(requests)
        
        for response, chapter_image_filename in zip(responses, chapter_image_filenames):
            filename = str(Path(PATH_TO_TEMP, chapter_image_filename))
            
            if filename in files:
                filename = str(Path(PATH_TO_TEMP, f"{uuid4().hex}-{chapter_image_filename}"))
                
            with open(filename, "wb") as file:
                file.write(response.content)
                file.close()
                
            reformate_image(filename)
            
            files.append(filename)
            
        if upscale:
            vulkan_upscale_images(files)
            
        return files

    def to_pdf(self, data_saver=True, standalone=False, upscale=False) -> str:
        files_list = self.download_imgs(data_saver=data_saver, upscale=upscale)

        pdf = FPDF()
        for file in loop(files_list, desc="Adding Chapter Images to PDF"):
            image = Image.open(file)

            width, height = image.size

            # convert pixel in mm with 1px=0.264583 mm
            width, height = float(width * 0.264583), float(height * 0.264583)

            # given we are working with A4 format size
            pdf_size = {"P": {"w": 210, "h": 297}, "L": {"w": 297, "h": 210}}

            # get page orientation from image size
            orientation = "P" if width < height else "L"

            if orientation == "L":
                image = image.rotate(90)

                width, height = image.size

                # convert pixel in mm with 1px=0.264583 mm
                width, height = float(width * 0.264583), float(height * 0.264583)

                # given we are working with A4 format size
                pdf_size = {"P": {"w": 210, "h": 297}, "L": {"w": 297, "h": 210}}

                # get page orientation from image size
                orientation = "P" if width < height else "L"

            #  make sure image size is not greater than the pdf format size
            width = (
                width
                if width < pdf_size[orientation]["w"]
                else pdf_size[orientation]["w"]
            )
            height = (
                height
                if height < pdf_size[orientation]["h"]
                else pdf_size[orientation]["h"]
            )

            pdf.add_page(orientation=orientation)

            pdf.image(file, 0, 0, width, height)

        if standalone:
            pdf_filename = f"{str(PATH_TO_TEMP)}\\{self.manga.title} v{self.volume.title} ch{self.number}.pdf"
        else:
            pdf_filename = f"{str(PATH_TO_TEMP)}\\Chapter {self.number}.pdf"

        pdf.output(pdf_filename, "F")

        return pdf_filename

    def to_mobi(self, data_saver=True, upscale=False) -> str:
        files_list = self.download_imgs(data_saver=data_saver, upscale=upscale)
        
        end_of_chapter_page = str(Path(Path(__file__).parent, "assets\\tec.jpg"))
        
        files_list.append(end_of_chapter_page)

        mobi_path = list_to_mobi(
            input_list=files_list,
            mobi_name=f"{self.manga.title} v{self.volume.title} ch{self.number}",
        )

        return mobi_path

    def __str__(self):
        return f"{self.number = }\n{self.id = }"
