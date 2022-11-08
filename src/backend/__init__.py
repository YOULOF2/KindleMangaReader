from src.backend.GetMangaByID import get_manga_by_id
from src.backend.SendByEmail import send_attachment_by_email, send_notification_email
from src.backend.SendToUSB import send_by_usb
from src.backend.MangaClasses import Manga

__all__ = ["get_manga_by_id", "send_by_usb", "load_manga", "send_attachment_by_email", "send_notification_email"]


def load_manga(msID: str):
    return Manga.load(msID)