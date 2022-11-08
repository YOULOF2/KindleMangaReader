from src.backend.MangaClasses import Manga, MangaVolume, MangaChapter
from src.backend.Utils import clear_temp, get_request_for
from pathlib import Path

__all__ = ["get_manga_by_id"]


def get_manga_by_id(manga_id: str) -> Manga:
    # # Clear temp folder
    # clear_temp()

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

    manga = Manga()
    # all manga volumes as a list of class MangaVolume
    all_volumes = []

    # Gets Cover for particular volume
    all_covers = get_request_for(
        f"https://api.mangadex.org/cover?"
        f"limit=100&manga%5B%5D={manga_id}&order%5BcreatedAt%5D=asc&order%5BupdatedAt%5D=asc&order%5Bvolume%5D=asc"
    )
    for volume_title, chapter_data in manga_volumes.items():
        volume = MangaVolume()

        # Get chapters for each volume
        all_chapters = []
        vol_chs = chapter_data["chapters"]
        for _, chapter_data in vol_chs.items():
            all_chapters.append(
                MangaChapter(
                    number=chapter_data["chapter"],
                    id=chapter_data["id"],
                    manga_obj=manga,
                    volume_obj=volume,
                )
            )

        # If volume is `none` set volume title to `UnGrpd`
        if volume_title == "none":
            volume_title = "UnGrpd"

        for cover in all_covers["data"]:
            if cover["attributes"]["volume"] == volume_title:
                hash_cover_filename = cover["attributes"]["fileName"]

                manga_cover_url = (
                    f"https://mangadex.org/covers/{manga_id}/{hash_cover_filename}"
                )
                break

        else:
            manga_cover_url = str(
                Path(Path(__file__).parent, "assets\\cnf.jpg")
                
            )
        volume.title = volume_title
        volume.chapters = all_chapters
        volume.cover = manga_cover_url
        volume.manga = manga

        all_volumes.append(volume)

    manga.id = manga_id
    manga.title = manga_title
    manga.description = manga_description
    manga.status = manga_status
    manga.cover = manga_cover
    manga.volumes = all_volumes

    return manga
