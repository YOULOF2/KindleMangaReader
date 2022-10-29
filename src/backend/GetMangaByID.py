from backend.MangaClasses import Manga, MangaVolume, MangaChapter
from backend.Utils import clear_temp, get_request_for

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

    # all manga volumes as a list of class MangaVolume
    all_volumes = []
    for volume_title, vol_ch_data in manga_volumes.items():

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
        if volume_title == "none":
            volume_title = "UnGrpd"
            
        all_volumes.append(
            MangaVolume(
                manga_id=manga_id,
                volume_title=volume_title,
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
