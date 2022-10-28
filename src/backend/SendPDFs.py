from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib
from dotenv import load_dotenv


load_dotenv()


def send_pdfs(pdf_files: list):
    def setup_server():
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(from_addr, password)

        return server

    def send_email(pdf_file_path, server):
        # Craft message (obj)
        msg = MIMEMultipart()

        msg["Subject"] = ""
        msg["From"] = from_addr
        msg["To"] = to_addr

        # Attach the pdf to the msg going by e-mail
        with open(pdf_file_path, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")

        pdf_filename = pdf_file_path.split("\\")[-1]
        attach.add_header("Content-Disposition", "attachment", filename=pdf_filename)
        msg.attach(attach)

        # send msg
        server.send_message(msg)
        server.quit()

    def process(pdf_file):
        server = setup_server()
        try:
            send_email(pdf_file, server)
        except smtplib.SMTPDataError:
            server = setup_server()
            process(pdf_file)

    ## credits: http://linuxcursor.com/python-programming/06-how-to-send-pdf-ppt-attachment-with-html-body-in-python-script
    from_addr = os.getenv("SENDER_EMAIL")
    to_addr = os.getenv("KINDLE_EMAIL")
    password = os.getenv("SENDER_EMAIL_PASSWORD")

    with ThreadPoolExecutor() as executor:
        _ = [executor.submit(process, pdf_file) for pdf_file in pdf_files]
