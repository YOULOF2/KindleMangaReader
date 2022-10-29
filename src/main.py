from time import time
from urllib import response
from backend import get_manga_by_id, Manga, send_pdfs
from flask import Flask, render_template, request, redirect, url_for, make_response
import json
import itertools

app = Flask(__name__)
app.jinja_env.filters["zip"] = zip


@app.route("/", methods=["GET"])
def index():
    response = make_response(render_template("index.html"))

    if request.cookies.get("que") is not None:
        response.set_cookie("que", "", expires=0)

    response.set_cookie("que", json.dumps({}))
    return response


@app.route("/manga", methods=["GET", "POST"])
def display_manga():
    if request.method == "POST":
        # text = request.form["text"]
        text = "737a846b-2e67-4d63-9f7e-f54b3beebac4"
        manga = get_manga_by_id(text)
        msID = manga.save()

        return render_template(
            "display_manga.html",
            id=manga.id,
            title=manga.title,
            description=manga.description,
            status=manga.status,
            volumes=manga.volumes,
            msID=msID,
        )

    msID = request.args.get("msID")
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


@app.route("/volume", methods=["GET"])
def display_volume():
    title = request.args.get("title")

    msID = request.args.get("msID")
    manga: Manga = Manga.load(msID)

    que_dict: dict = json.loads(request.cookies.get("que"))
    print(f"{que_dict = }")
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


@app.route("/que", methods=["GET"])
def display_que():
    msID = request.args.get("msID")

    que_dict: list[str] = json.loads(request.cookies.get("que"))
    que = list(itertools.chain.from_iterable(que_dict.values()))
    
    print(f"{que_dict = }")

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


@app.route("/que/add", methods=["POST"])
def que_add():
    title = request.args.get("title")
    msID = request.args.get("msID")

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


@app.route("/que/remove", methods=["GET"])
def que_remove():
    item_que_id = request.args.get("item_id")

    response = make_response(redirect(url_for("display_que")))

    que_dict: dict = json.loads(request.cookies.get("que"))
    
    for volume_title, volume_que in que_dict.items():
        for item_id in volume_que:
            if item_id == item_que_id:
                que = que_dict[volume_title]
                que.remove(item_id)
                que = list(set(que))
                que_dict[volume_title] = que
                
    print(f"{que_dict = }")
    
    response.set_cookie("que", json.dumps(que_dict))

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
    msID = request.args.get("msID")
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

    processing_time = round((processing_end - processing_start) / 60, 1)

    return redirect(url_for("display_success", processing_time=processing_time))


@app.route("/success", methods=["POST"])
def display_success():
    processing_time = request.args.get("processing_time")

    response = make_response(
        f"<h1>Success!</h1><br /><h2>{processing_time} minutes</h2>"
    )
    response.set_cookie("que", json.dumps({}))
    return response

@app.route("/redirect", methods=["POST"])
def redirect_to():
    msID = request.args.get("msID")
    
    action = request.form.get("action")
    match action:
        case "Home":
            return redirect(url_for("index"))
        case "Que":
            return redirect(url_for("display_que", msID=msID))
        case "Volumes":
            return redirect(url_for("display_manga", msID=msID))

if __name__ == "__main__":
    app.run(debug=True, host="192.168.1.18", port=5000)

    # 89393959-9749-4b7d-b199-cf25f1a52d86
