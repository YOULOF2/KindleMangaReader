from concurrent.futures import ThreadPoolExecutor
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv


load_dotenv()


def send_attachment_by_email(files: list):
    def setup_server():
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_addr, password)

        return server

    def send_email(file_path, server):
        # Craft message (obj)
        msg = MIMEMultipart()

        msg["Subject"] = ""
        msg["From"] = from_addr
        msg["To"] = to_addr

        file_extension = file_path.split(".")[-1]
        with open(file_path, "rb") as f:
            if file_extension == "pdf":
                attach = MIMEApplication(f.read(), _subtype="pdf")
            else:
                attach = MIMEApplication(f.read(), _subtype="pdf")

        file_name = file_path.split("\\")[-1]
        attach.add_header("Content-Disposition", "attachment", filename=file_name)
        msg.attach(attach)

        # send msg
        server.send_message(msg)
        server.quit()

    def process(file):
        server = setup_server()
        try:
            send_email(file, server)
        except smtplib.SMTPDataError:
            server = setup_server()
            process(file)

    ## credits: http://linuxcursor.com/python-programming/06-how-to-send-pdf-ppt-attachment-with-html-body-in-python-script
    from_addr = os.getenv("SENDER_EMAIL")
    to_addr = os.getenv("KINDLE_EMAIL")
    password = os.getenv("SENDER_EMAIL_PASSWORD")

    with ThreadPoolExecutor() as executor:
        _ = [executor.submit(process, file) for file in files]


def send_notification_email(files_sent: list[str]):
    def ulify(elements):
        html_string = "<ul>\n"
        html_string += "\n".join(["<li>" + str(s) + "</li>" for s in elements])
        html_string += "\n</ul>"
        return html_string
    
    sender = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_EMAIL_PASSWORD")
    reciever = os.getenv("PERSONAL_EMAIL")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Ebooks Have Been Sent To Kindle"
    msg["From"] = sender
    msg["To"] = reciever

    file_titles = [file.split("\\")[-1].split(".")[0] for file in files_sent]
    text = "Ebooks requested have been delivered"
    html = f"""
    <html>
    <head></head>
    <body>
        <p>The Ebooks:</p>
        {ulify(file_titles)}
        <br>
        <p>Have been sent successfully to Kindle</p>
        from KindleMangaReader
    </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    msg.attach(part1)
    msg.attach(part2)

    mail = smtplib.SMTP("smtp.gmail.com", 587)

    mail.ehlo()

    mail.starttls()

    mail.login(sender, sender_password)
    mail.sendmail(sender, reciever, msg.as_string())
    mail.quit()