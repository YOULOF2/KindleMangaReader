from time import time
from urllib import response
from backend import get_manga_by_id, Manga, send_pdfs
from flask import Flask, render_template, request, redirect, url_for, make_response
import json

app = Flask(__name__)
app.jinja_env.filters["zip"] = zip


@app.route("/", methods=["GET"])
def index():    
    response = make_response(render_template("index.html"))

    if request.cookies.get("que") is not None:
        response.set_cookie("que", "", expires=0)

    response.set_cookie("que", json.dumps([]))
    return response


@app.route("/manga", methods=["GET", "POST"])
def display_manga():
    if request.method == "POST":
        text = request.form["text"]
        # text = "737a846b-2e67-4d63-9f7e-f54b3beebac4"
        manga = get_manga_by_id(text)
        manga.save()

        return render_template(
            "display_manga.html",
            id=manga.id,
            title=manga.title,
            description=manga.description,
            status=manga.status,
            volumes=manga.volumes,
        )

    manga = Manga.load()
    return render_template(
        "display_manga.html",
        id=manga.id,
        title=manga.title,
        description=manga.description,
        status=manga.status,
        volumes=manga.volumes,
    )


@app.route("/volume", methods=["GET"])
def display_volume():
    title = request.args.get("title")
    manga: Manga = Manga.load()
    for volume in manga.volumes:
        if volume.title == title:
            return render_template(
                "display_volume.html",
                id=manga.id,
                title=manga.title,
                description=manga.description,
                status=manga.status,
                volumes=manga.volumes,
                volume=volume,
            )


@app.route("/que")
def display_que():
    unfiltered_que: list[str] = json.loads(request.cookies.get("que"))
    que = list(set(unfiltered_que))

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
    )


@app.route("/que/add", methods=["POST"])
def que_add():
    title = request.args.get("title")

    selected_chapters = list(request.form)
    selected_chapters.remove("action")

    if request.form.get("action") == "Back":
        response = make_response(redirect(url_for("display_manga")))
    else:
        response = make_response(redirect(url_for("display_que")))

    try:
        que = json.loads(request.cookies.get("que"))
    except TypeError:
        response = make_response(redirect(url_for("display_volume", title=title)))
        response.set_cookie("que", json.dumps([]))
        return response
    else:
        que += selected_chapters
        que = list(set(que))
        response.set_cookie("que", json.dumps(que))

    return response


@app.route("/que/remove", methods=["GET"])
def que_remove():
    item_id = request.args.get("item_id")

    response = make_response(redirect(url_for("display_que")))

    que: list[str] = json.loads(request.cookies.get("que"))
    que.remove(item_id)

    response.set_cookie("que", json.dumps(que))

    return response


@app.route("/que/checkout", methods=["POST"])
def que_checkout():
    class InternalVolumeChapter:
        def __init__(self, volume_title: str, chapter_number: str) -> None:
            self.volume_title = volume_title
            self.chapter_number = chapter_number

    processing_start = time()

    unfiltered_que: list[str] = json.loads(request.cookies.get("que"))
    que = set(unfiltered_que)
    print(f"{que = }")

    # Redirect back to que if que is empty
    if len(que) == 0:
        return redirect(url_for("display_que"))

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
    manga: Manga = Manga.load()

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

    for volume_obj in manga.volumes:
        for complete_volume_title in complete_volumes_titles:
            if complete_volume_title == volume_obj.title:
                volume_files = volume_obj.to_pdf()
                files_to_send += volume_files

    for chapter, volume_title in zip(chapter_objects, volume_objects_titles):
        filename = chapter.to_pdf(volume_title=volume_title)
        files_to_send.append(filename)

        
    print(f"{files_to_send = }")

    send_pdfs(
        pdf_files=files_to_send,
    )

    processing_end = time()

    processing_time = round((processing_end - processing_start)/60, 1)

    return redirect(url_for("display_success", processing_time=processing_time))


@app.route("/success")
def display_success():
    processing_time = request.args.get("processing_time")
    
    response = make_response(f"<h1>Success!</h1><br /><h2>{processing_time} minutes</h2>")
    response.set_cookie("que", json.dumps([]))
    return response


if __name__ == "__main__":
    app.run(debug=False, host="192.168.1.18", port=5000)

    # 89393959-9749-4b7d-b199-cf25f1a52d86
    