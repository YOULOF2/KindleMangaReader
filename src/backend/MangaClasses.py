from select import kevent
from PIL import Image
from fpdf import FPDF
from PyPDF2 import PdfMerger
from pathlib import Path
import pickle
from backend.Utils import get_file_size_for, get_request_for, PATH_TO_TEMP, loop
import requests


class MangaChapter:
    def __init__(self, chapter_num: float, chapter_id: str) -> None:
        """Contains ID and Number of Chapter

        Args:
            chapter_num (float): The number of the chapter
            chapter_id (str): The ID of the chapter from MangaDex
        """
        self.number = chapter_num
        self.id = chapter_id

    def download_imgs(self) -> list[str]:
        """Dowloads The Images of the chapter using the MangaDex `at-home` endpoint

        Returns:
            list[str]: List of all images
        """

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

    # TODO: Add cover for each chapter using PILLOW and manga cover
    # TODO: Chapter can be separated to multiple pdfs according to the size, if the `inparts` argument is True
    # TODO: Change return type to be either `list` or `str`
    def to_pdf(self, **kwargs) -> str:
        """Converts Chapter images to PDF.
        If `volume_title` and `manga_name` variables are found in the kwargs,
        the chapter is processed as standalone with a cover image and the volume title and manga name in the filename.

        Args:
            **kwargs (dict): 
                    volume_title (str): Volume Title
                    manga_name (str): Manga Name
                    
        Returns:
            str: PDF filename
        """
        volume_title = kwargs.get("volume_title")
        manga_name = kwargs.get("manga_name")

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

        if volume_title:
            pdf_filename = (
                f"{str(PATH_TO_TEMP)}\\{manga_name} v{volume_title} ch{self.number}.pdf"
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
        """Conatins the manga id, volume title, and the list of chapters for a manga volume.

        Args:
            manga_id (str): Manga ID from MangaDex
            volume_title (str): The title of the volume
            chapters (list[MangaChapter]): List of `MangaChapter` objects.
        """
        self.manga_id = manga_id
        self.title = volume_title
        self.chapters = chapters

    # TODO: for each volume part add a cover page with volume cover and PILOOW text
    # TODO: Change return type to support `str` or `list` 
    def to_pdf(self, in_parts=True) -> list[str]:
        """Converts the volume object to PDFs

        Args:
            in_parts (bool): `True` by default. Set to `False` to make volume into one PDF only.
        
        Returns:
            list (str): List of PDF parts
        """
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

                #  make sure image size is not greater than the pdf format size
                cover_width = cover_width if cover_width < 210 else 210
                cover_height = cover_height if cover_height < 297 else 297

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
        merger = PdfMerger()
        for volume_part, pdf in loop(
            enumerate(all_pdfs, start=1), description="Creating Volume"
        ):
            if total_file_size <= 11 and in_parts:
                total_file_size += get_file_size_for(pdf)

                merger.append(pdf)
            else:
                filename = f"{PATH_TO_TEMP}\\Volume {self.title} Part {volume_part}.pdf"
                merger.write(filename)
                all_volume_parts.add(filename)

                merger.close()
                merger = PdfMerger()

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


# TODO: Add doc strings to Manga class and its methods
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
