"""Send data users"""

import smtplib
import pathlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List
from decouple import config
from loguru import logger

MAIL_SERVER: str = config("mailer_server")
MAIL_PORT: int = config("mailer_port", cast=int)
MAIL_USER: str = config("mailer_user")
MAIL_PASSWORD: str = config("mailer_password")
MAIL_SENDER: str = config("mailer_sender")
MAIL_RECEIVER: str = config("mailer_receiver")
MAIL_SUBJECT: str = config("mailer_subject", default="Dtrack Toolkit Service Report")

LOG_DIR = config("log_dir", default="./log")
OUTPUT_DIR = config("output_dir", default="./output")


def setup_mailer(server: str, port: int, user: str, password: str) -> smtplib.SMTP:
    mailer = smtplib.SMTP(server, port)
    mailer.starttls()
    mailer.login(user, password)
    return mailer


def build_mail(
    sender_email: str, receiver_mail: str, subject: str, message_payload: str
):
    message = MIMEMultipart("alternative")

    message["From"] = sender_email
    message["To"] = receiver_mail
    message["Subject"] = subject

    message.attach(MIMEText(message_payload, "plain"))

    return message


def add_attachment(msg: MIMEMultipart, paths: List[str]) -> MIMEMultipart:
    for file in paths:
        with open(file, "rb") as fh:
            # Attach the file with filename to the email
            name = file.split("/")[-1]
            msg.attach(MIMEApplication(fh.read(), Name=name))
    return msg


def collect_attachments(path: str, suffix: str) -> List[str]:
    attachment_objects = []
    directory = pathlib.Path(path)
    for item in directory.iterdir():
        if item.is_file() and item.name.endswith(suffix):
            attachment_objects.append(item.as_posix())
            # print(item.as_posix())
    return attachment_objects


def main():
    if not (MAIL_SERVER and MAIL_PORT and MAIL_USER and MAIL_PASSWORD and MAIL_SENDER and MAIL_RECEIVER):
        logger.info("No mail server configuration found. Aborting mail sending.")
        return

    mailer = setup_mailer(MAIL_SERVER, MAIL_PORT, MAIL_USER, MAIL_PASSWORD)
    receiver = MAIL_RECEIVER
    subject = MAIL_SUBJECT
    sender_address = MAIL_SENDER
    msg = build_mail(
        "dttaas@mail.example",
        receiver,
        subject,
        "Report data attached",
    )
    attachments_paths_json = collect_attachments(path=OUTPUT_DIR, suffix=".json")
    attachments_paths_logs = collect_attachments(path=LOG_DIR, suffix=".log")
    msg = add_attachment(msg, attachments_paths_logs)
    msg = add_attachment(msg, attachments_paths_json)
    mailer.sendmail(sender_address, receiver, msg.as_string())


if __name__ == "__main__":
    main()
