from email.mime.application import MIMEApplication
from fileinput import filename
from backend.MangaClasses import *
from backend.utils import *
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
from dotenv import load_dotenv
import os

load_dotenv()


def get_manga_by_id(manga_id: str) -> Manga:
    # Get Manga Data
    manga_details_data = get_request_for(f"https://api.mangadex.org/manga/{manga_id}")

    manga_details = manga_details_data["data"]
    manga_attributes = manga_details["attributes"]

    manga_title = manga_attributes["title"]["en"]
    manga_description = manga_attributes["description"]["en"]
    manga_status = manga_attributes["status"]

    manga_cover_id = [
        relationship["id"]
        for relationship in manga_details["relationships"]
        if relationship["type"] == "cover_art"
    ][0]
    manga_cover_data = get_request_for(
        f"https://api.mangadex.org/cover/{manga_cover_id}"
    )
    manga_cover = f"https://uploads.mangadex.org/covers/{manga_cover_data['data']['id']}/{manga_cover_data['data']['attributes']['fileName']}"

    # Get Manga Volumes and chapters
    aggregated_manga_data = get_request_for(
        f"https://api.mangadex.org/manga/{manga_id}/aggregate?translatedLanguage%5B%5D=en"
    )

    # All volumes
    manga_volumes = aggregated_manga_data["volumes"]

    # all manga volumes as a list of class MangaVolume
    all_volumes = []
    for vol_number, vol_ch_data in manga_volumes.items():

        # Get chapters for each volume
        all_chapters = []
        vol_chs = vol_ch_data["chapters"]
        for _, chapter_data in vol_chs.items():
            all_chapters.append(
                MangaChapter(
                    chapter_num=chapter_data["chapter"],
                    chapter_id=chapter_data["id"],
                )
            )

        all_volumes.append(
            MangaVolume(
                manga_id=manga_id,
                volume_title=vol_number,
                chapters=all_chapters,
            )
        )

    return Manga(
        id=manga_id,
        title=manga_title,
        description=manga_description,
        status=manga_status,
        manga_cover=manga_cover,
        volumes=all_volumes,
    )


def send_pdfs(pdf_files: list, subject = "", message = "", send_to = "", password = ""):
    def send_email_pdf(pdf_file: str):
        # Attach the pdf to the msg going by e-mail
        with open(pdf_file, "rb") as file:
            attach = MIMEApplication(file.read(),_subtype="pdf")
        
        pdf_filename = str(pdf_file).split("\\")[-1]
        attach.add_header("Content-Disposition","attachment",filename=pdf_filename)
        msg.attach(attach)
    
        # send msg
        server.send_message(msg)
        
    ## credits: http://linuxcursor.com/python-programming/06-how-to-send-pdf-ppt-attachment-with-html-body-in-python-script
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.set_debuglevel(True)
    server.starttls()
    server.login(os.getenv("SENDER_EMAIL"), os.getenv("SENDER_EMAIL_PASSWORD"))
    # Craft message (obj)
    msg = MIMEMultipart()

    msg["Subject"] = subject
    msg["From"] = os.getenv("SENDER_EMAIL")
    msg["To"] = os.getenv("KINDLE_EMAIL")
    # Insert the text to the msg going by e-mail
    msg.attach(MIMEText(message, "plain"))
    
    all_threads = []
    for pdf_file in pdf_files:
        thread = threading.Thread(target=send_email_pdf, args=(pdf_file))
        all_threads.append(thread)
        thread.start()
    
    # Join all threads after finishing
    [th.join() for th in all_threads]