from time import time
from backend import get_manga_by_id, Manga, send_pdfs, send_by_usb
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
    flash,
)
import json
import itertools

app = Flask(__name__)
app.secret_key = "123secret"
app.jinja_env.filters["zip"] = zip


@app.after_request
def after_request(response):
    response.headers[
        "Cache-Control"
    ] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET"])
def index():
    response = make_response(render_template("index.html"))
    response.set_cookie("que", json.dumps({}))

    return response


@app.route("/get_manga", methods=["POST"])
def get_manga():
    text = request.form["text"]
    if "http" in text:
        text = text.removeprefix("https://mangadex.org/title/")
        text = text.split("/")[0]
    # text = "737a846b-2e67-4d63-9f7e-f54b3beebac4"
    manga = get_manga_by_id(text)
    msID = manga.save()

    return redirect(url_for("display_manga", msID=msID))


@app.route("/<string:msID>/manga", methods=["GET"])
def display_manga(msID: str):
    manga = Manga.load(msID)
    return render_template(
        "display_manga.html",
        id=manga.id,
        title=manga.title,
        description=manga.description,
        status=manga.status,
        volumes=manga.volumes,
        msID=msID,
    )


@app.route("/<string:msID>/volume/<string:title>", methods=["GET"])
def display_volume(msID: str, title: str):
    manga: Manga = Manga.load(msID)

    que_dict: dict = json.loads(request.cookies.get("que"))
    if title not in que_dict:
        que_dict.update({title: []})
    que = que_dict[title]

    is_checked_list = []
    for volume in manga.volumes:
        if volume.title == title:
            if f"volume_{volume.title}" in que:
                is_checked_list.append(True)
            else:
                is_checked_list.append(False)

            for chapter in volume.chapters:
                if f"{volume.title}-{chapter.number}" in que:
                    is_checked_list.append(True)
                else:
                    is_checked_list.append(False)

            return render_template(
                "display_volume.html",
                id=manga.id,
                title=manga.title,
                description=manga.description,
                status=manga.status,
                volumes=manga.volumes,
                volume=volume,
                msID=msID,
                is_checked_list=is_checked_list,
            )


@app.route("/<string:msID>/que", methods=["GET"])
def display_que(msID: str):
    que_dict: list[str] = json.loads(request.cookies.get("que"))
    que = list(itertools.chain.from_iterable(que_dict.values()))

    volumes = []
    chapters = []
    complete_volumes = []
    for data in que:
        split_data = data.split("-")
        if len(split_data) == 1:
            volume_title = data.removeprefix("volume_")
            complete_volumes.append(volume_title)
            continue

        volumes.append(split_data[0])
        chapters.append(split_data[1])

    return render_template(
        "display_que.html",
        volumes=volumes,
        chapters=chapters,
        complete_volumes=complete_volumes,
        msID=msID,
    )


@app.route("/<string:msID>/que/add/<string:title>", methods=["POST"])
def que_add(msID: str, title: str):
    selected_chapters = list(request.form)
    selected_chapters.remove("action")

    if request.form.get("action") == "Back":
        response = make_response(redirect(url_for("display_manga", msID=msID)))
    else:
        response = make_response(redirect(url_for("display_que", msID=msID)))

    try:
        que_dict = json.loads(request.cookies.get("que"))
    except TypeError:
        response = make_response(redirect(url_for("display_volume", title=title)))
        response.set_cookie("que", json.dumps({}))
        return response
    else:
        if title not in que_dict:
            que_dict.update({title: []})
        que = que_dict[title]
        que += selected_chapters
        for item in que:
            if item not in selected_chapters:
                que.remove(item)
        que = list(set(que))
        que_dict[title] = que
        response.set_cookie("que", json.dumps(que_dict))

    return response


@app.route("/<string:msID>/que/remove/<string:item_que_id>", methods=["GET"])
def que_remove(msID: str, item_que_id: str):
    response = make_response(redirect(url_for("display_que", msID=msID)))

    que_dict: dict = json.loads(request.cookies.get("que"))

    for volume_title, volume_que in list(que_dict.items()):
        for item_id in volume_que:
            if item_id == item_que_id:
                que = que_dict[volume_title]
                que.remove(item_id)
                que = list(set(que))

                if len(que) == 0:
                    que_dict[volume_title] = que
                    del que_dict[volume_title]
                    break

    response.set_cookie("que", json.dumps(que_dict))

    return response


@app.route("/<string:msID>/que/checkout", methods=["POST"])
def que_checkout(msID: str):
    class InternalVolumeChapter:
        def __init__(self, volume_title: str, chapter_number: str) -> None:
            self.volume_title = volume_title
            self.chapter_number = chapter_number

    processing_start = time()

    que_dict: dict = json.loads(request.cookies.get("que"))
    que = list(itertools.chain.from_iterable(que_dict.values()))

    # Redirect back to que if que is empty
    if len(que) == 0:
        flash("Que is empty")
        return redirect(url_for("display_manga", msID=msID))

    all_volume_chapters = []
    complete_volumes_titles = []
    for data in que:
        split_data = data.split("-")
        if len(split_data) == 1:
            volume_title = data.removeprefix("volume_")
            complete_volumes_titles.append(volume_title)
            continue

        all_volume_chapters.append(
            InternalVolumeChapter(
                volume_title=split_data[0], chapter_number=split_data[1]
            )
        )

    # Load manga object
    manga: Manga = Manga.load(msID)

    chapter_objects = []
    volume_objects_titles = []

    files_to_send = []

    for volume_obj in manga.volumes:
        for volume_chapter in all_volume_chapters:
            if volume_chapter.volume_title == volume_obj.title:
                for _ in range(len(all_volume_chapters)):
                    for chapter_obj in volume_obj.chapters:
                        if volume_chapter.chapter_number == chapter_obj.number:
                            volume_objects_titles.append(volume_obj.title)

                            chapter_objects.append(chapter_obj)
    
    submit_type = request.form.get("action")
    as_mobi = request.form.get("mobi")
        
    send_by_email = False if submit_type == "Send By USB" else True
        
    for volume_obj in manga.volumes:
        for complete_volume_title in complete_volumes_titles:
            if complete_volume_title == volume_obj.title:
                print(f"Creating volume {volume_obj.title}")
                if not as_mobi:
                    volume_files = volume_obj.to_pdf(data_saver=send_by_email)
                    files_to_send += volume_files
                else:
                    volume_files = [volume_obj.to_mobi(data_saver=send_by_email)]
                    files_to_send.insert(0, volume_files)
                

    for chapter, volume_title in zip(chapter_objects, volume_objects_titles):
        if not as_mobi:
            filename = chapter.to_pdf()
        else:
            filename = chapter.to_mobi()
        files_to_send.append(filename)

    if send_by_email:
        send_pdfs(
            pdf_files=files_to_send,
        )
    else:
        send_by_usb(
            drive_title="Kindle",
            files=files_to_send,
        )

    processing_end = time()

    processing_time = round((processing_end - processing_start) / 60, 1)

    return redirect(url_for("display_success", processing_time=processing_time))


@app.route("/success", methods=["GET"])
def display_success():
    processing_time = request.args.get("processing_time")

    response = make_response(
        f"<h1>Success!</h1><br /><h2>{processing_time} minutes</h2>"
    )
    response.set_cookie("que", json.dumps({}))
    return response


@app.route("/<string:msID>/redirect", methods=["POST"])
def process_redirect(msID: str):
    action = request.form.get("action")
    match action:
        case "Home":
            return redirect(url_for("index"))
        case "Que":
            return redirect(url_for("display_que", msID=msID))
        case "Volumes":
            return redirect(url_for("display_manga", msID=msID))
        case "Back":
            return redirect(url_for("display_que", msID=msID))


if __name__ == "__main__":
    app.run(debug=True, host="192.168.1.18", port=5000)

    # 89393959-9749-4b7d-b199-cf25f1a52d86
