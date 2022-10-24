from PIL import Image
from fpdf import FPDF
from PyPDF2 import PdfMerger
from pathlib import Path
import pickle
from backend.utils import *


class MangaChapter:
    def __init__(self, chapter_num: float, chapter_id: str) -> None:
        self.number = chapter_num
        self.id = chapter_id

    def download_imgs(self) -> list[str]:
        request_json = get_request_for(
            f"https://api.mangadex.org/at-home/server/{self.id}"
        )

        base_url = request_json["baseUrl"]

        chapter_data = request_json["chapter"]
        chapter_hash = chapter_data["hash"]
        chapter_img_filenames = chapter_data["dataSaver"]

        files = []
        for chapter_img_filename in loop(
            chapter_img_filenames, description="Dowloading Chapter Images"
        ):
            image_url = f"{base_url}/data-saver/{chapter_hash}/{chapter_img_filename}"

            response = requests.get(image_url)
            filename = f"{Path(Path(__file__).resolve().parent.parent, 'temp', chapter_img_filename)}"
            with open(filename, "wb") as file:
                file.write(response.content)

            files.append(filename)

        return files

    def to_pdf(self, volume_title=None, standalone=False) -> str:
        files_list = self.download_imgs()

        pdf = FPDF()
        for file in loop(files_list, description="Adding Chapter Images to PDF"):
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

        if volume_title is not None:
            pdf_filename = (
                f"{str(PATH_TO_TEMP)}\\Volume {volume_title} Chapter {self.number}.pdf"
            )
        else:
            pdf_filename = f"{str(PATH_TO_TEMP)}\\Chapter {self.number}.pdf"
            
        pdf.output(pdf_filename, "F")
        

        return pdf_filename

    def __str__(self):
        return f"{self.number = }\n{self.id = }"


class MangaVolume:
    def __init__(
        self,
        manga_id: str,
        volume_title: str,
        chapters: list[MangaChapter],
    ) -> None:
        self.manga_id = manga_id
        self.title = volume_title
        self.chapters = chapters

    def to_pdf(self) -> list:
        all_pdfs = []

        # Gets Cover for particular volume
        all_covers = get_request_for(
            f"https://api.mangadex.org/cover?"
            f"limit=100&manga%5B%5D={self.manga_id}&order%5BcreatedAt%5D=asc&order%5BupdatedAt%5D=asc&order%5Bvolume%5D=asc"
        )

        for cover in all_covers["data"]:
            if cover["attributes"]["volume"] == self.title:
                hash_cover_filename = cover["attributes"]["fileName"]

                manga_cover_url = (
                    f"https://mangadex.org/covers/{self.manga_id}/{hash_cover_filename}"
                )

                response = requests.get(manga_cover_url)
                cover_filename = f"{Path(PATH_TO_TEMP, hash_cover_filename)}"
                # Dowloads cover as image
                with open(cover_filename, "wb") as file:
                    file.write(response.content)

                # Converts Cover image to pdf
                cover_pdf = FPDF()

                cover_image = Image.open(cover_filename)
                cover_width, cover_height = cover_image.size

                # convert pixel in mm with 1px=0.264583 mm
                cover_width, cover_height = float(cover_width * 0.264583), float(
                    cover_height * 0.264583
                )

                # given we are working with A4 format size
                pdf_size = {"P": {"w": 210, "h": 297}, "L": {"w": 297, "h": 210}}

                # get page orientation from image size
                orientation = "P" if cover_width < cover_height else "L"

                #  make sure image size is not greater than the pdf format size
                cover_width = (
                    cover_width
                    if cover_width < pdf_size[orientation]["w"]
                    else pdf_size[orientation]["w"]
                )
                cover_height = (
                    cover_height
                    if cover_height < pdf_size[orientation]["h"]
                    else pdf_size[orientation]["h"]
                )

                cover_pdf.add_page()

                cover_pdf.image(cover_filename, 0, 0, cover_width, cover_height)

                cover_pdf_filename = (
                    f"{str(PATH_TO_TEMP)}\\volume {self.title} cover.pdf"
                )
                cover_pdf.output(cover_pdf_filename, "F")

        for chapter in loop(
            self.chapters, description="Converting Chapters to PDFs", colour="RED"
        ):
            all_pdfs.insert(0, chapter.to_pdf())

        # Add cover image pdf to all_pdfs
        all_pdfs.insert(0, cover_pdf_filename)

        all_volume_parts = set([])
        total_file_size = 0
        volume_part = 1
        merger = PdfMerger()
        for pdf in loop(all_pdfs, description="Creating Volume"):
            if total_file_size <= 18:
                total_file_size += get_file_size_for(pdf)

                merger.append(pdf)
            else:
                filename = f"{PATH_TO_TEMP}\\Volume {self.title} Part {volume_part}.pdf"
                merger.write(filename)
                all_volume_parts.add(filename)

                merger.close()
                merger = PdfMerger()

                volume_part += 1
                total_file_size = 0

                merger.append(pdf)
                total_file_size += get_file_size_for(pdf)

        filename = f"{PATH_TO_TEMP}\\Volume {self.title} Part {volume_part}.pdf"
        merger.write(filename)
        all_volume_parts.add(filename)

        merger.close()

        return list(all_volume_parts)

    def __str__(self):
        return f"{self.title = }"


class Manga:
    MANGA_DATA_STORAGE_PATH = Path(PATH_TO_TEMP, "data.manga")

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        status: str,
        manga_cover: str,
        volumes: list[MangaVolume],
    ) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.cover = manga_cover
        self.volumes = volumes

    def __str__(self):
        return f"{self.title = }\n{self.description = }\n{self.status = }\n{self.year = }\n{self.cover = }\nNumber of volumes = {len(self.volumes)}"

    def save(self):
        with open(self.MANGA_DATA_STORAGE_PATH, "wb") as pickle_file:
            pickle.dump(self, pickle_file)

    @classmethod
    def load(cls):
        with open(cls.MANGA_DATA_STORAGE_PATH, "rb") as pickle_file:
            instance = pickle.load(pickle_file)
        return instance
