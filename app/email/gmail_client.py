
import os
import imaplib
import email
import re

from html import unescape
from html.parser import HTMLParser
from email.header import decode_header
from email.message import Message
from dotenv import load_dotenv


# Load environment variables
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


class HTMLTextExtractor(HTMLParser):

    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        if data.strip():
            self.text_parts.append(data.strip())

    def get_text(self):
        return " ".join(self.text_parts)


class GmailClient:

    def __init__(self):

        self.email_address = os.getenv("GMAIL_ADDRESS")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")

        self.imap_host = os.getenv(
            "IMAP_HOST", "imap.gmail.com"
        )

        self.imap_port = int(
            os.getenv("IMAP_PORT", "993")
        )

        self.connection = None

    # ---------------------------------------------
    # CONNECT TO GMAIL
    # ---------------------------------------------

    def connect(self):

        if not self.email_address or not self.app_password:
            raise ValueError(
                "GMAIL_ADDRESS or GMAIL_APP_PASSWORD is missing in .env"
            )

        try:

            self.connection = imaplib.IMAP4_SSL(
                self.imap_host,
                self.imap_port
            )

            self.connection.login(
                self.email_address,
                self.app_password
            )

            status, _ = self.connection.select("INBOX")

            if status != "OK":
                raise ConnectionError(
                    "Could not open Gmail inbox."
                )

            print("Gmail inbox connected successfully!")

            return True

        except Exception as error:

            self.disconnect()

            raise ConnectionError(
                f"Gmail connection failed: {error}"
            ) from error

    # ---------------------------------------------
    # DECODE EMAIL HEADERS
    # ---------------------------------------------

    @staticmethod
    def decode_header_value(value):

        if not value:
            return ""

        decoded_parts = decode_header(value)
        result = []

        for content, encoding in decoded_parts:

            if isinstance(content, bytes):

                try:
                    result.append(
                        content.decode(
                            encoding or "utf-8",
                            errors="replace"
                        )
                    )

                except LookupError:

                    result.append(
                        content.decode(
                            "utf-8",
                            errors="replace"
                        )
                    )

            else:
                result.append(str(content))

        return "".join(result)

    # ---------------------------------------------
    # DECODE EMAIL BODY
    # ---------------------------------------------

    @staticmethod
    def decode_payload(part):

        payload = part.get_payload(decode=True)

        if not payload:
            return ""

        charset = part.get_content_charset() or "utf-8"

        try:

            return payload.decode(
                charset,
                errors="replace"
            )

        except LookupError:

            return payload.decode(
                "utf-8",
                errors="replace"
            )

    # ---------------------------------------------
    # REMOVE HTML TAGS
    # ---------------------------------------------

    @staticmethod
    def html_to_text(html_content):

        parser = HTMLTextExtractor()

        try:
            parser.feed(html_content)
            text = parser.get_text()

        except Exception:
            text = re.sub(
                r"<[^>]+>",
                " ",
                html_content
            )

        return unescape(text).strip()

    # ---------------------------------------------
    # EXTRACT EMAIL BODY
    # ---------------------------------------------

    @classmethod
    def extract_body(cls, message: Message):

        plain_parts = []
        html_parts = []

        if message.is_multipart():

            for part in message.walk():

                if part.is_multipart():
                    continue

                disposition = (
                    part.get("Content-Disposition", "") or ""
                ).lower()

                if "attachment" in disposition:
                    continue

                content_type = part.get_content_type()

                if content_type == "text/plain":

                    content = cls.decode_payload(part)

                    if content:
                        plain_parts.append(content)

                elif content_type == "text/html":

                    content = cls.decode_payload(part)

                    if content:
                        html_parts.append(content)

        else:

            content_type = message.get_content_type()

            content = cls.decode_payload(message)

            if content_type == "text/plain":
                plain_parts.append(content)

            elif content_type == "text/html":
                html_parts.append(content)

        # Prefer plain text
        if plain_parts:

            body = "\n".join(plain_parts)

        # Use HTML only when plain text is unavailable
        elif html_parts:

            body = cls.html_to_text(
                "\n".join(html_parts)
            )

        else:

            body = "Email body is unavailable or unsupported."

        return body.strip()

    # ---------------------------------------------
    # FETCH UNREAD EMAILS
    # ---------------------------------------------

    def fetch_unread_emails(self, limit=5):

        if self.connection is None:
            raise ConnectionError(
                "Connect to Gmail before fetching emails."
            )

        limit = max(1, min(int(limit), 10))

        status, messages = self.connection.search(
            None,
            "UNSEEN"
        )

        if status != "OK":
            raise RuntimeError(
                "Could not search Gmail inbox."
            )

        email_ids = messages[0].split()

        # Get the latest unread emails
        email_ids = email_ids[-limit:]

        results = []

        for email_id in reversed(email_ids):

            try:

                status, data = self.connection.fetch(
                    email_id,
                    "(BODY.PEEK[])"
                )

                if status != "OK":
                    continue

                raw_email = None

                for item in data:

                    if isinstance(item, tuple):
                        raw_email = item[1]
                        break

                if not raw_email:
                    continue

                message = email.message_from_bytes(
                    raw_email
                )

                email_data = {
                    "from": self.decode_header_value(
                        message.get("From")
                    ),
                    "subject": self.decode_header_value(
                        message.get("Subject")
                    ),
                    "date": message.get("Date", ""),
                    "body": self.extract_body(message),
                    "message_id": message.get("Message-ID", "")
                }

                results.append(email_data)

            except Exception as error:

                print(
                    f"Could not process email {email_id}: {error}"
                )

        print(f"Retrieved {len(results)} unread emails.")

        return results

    # ---------------------------------------------
    # DISCONNECT FROM GMAIL
    # ---------------------------------------------

    def disconnect(self):

        if self.connection is not None:

            try:
                self.connection.close()
            except Exception:
                pass

            try:
                self.connection.logout()
            except Exception:
                pass

            self.connection = None


# ---------------------------------------------
# DIRECT TESTING
# ---------------------------------------------

if __name__ == "__main__":

    gmail = GmailClient()

    try:

        gmail.connect()

        inbox_emails = gmail.fetch_unread_emails(
            limit=5
        )

        print("\nUnread Emails Found:", len(inbox_emails))

        for index, item in enumerate(inbox_emails, 1):

            print("\n" + "=" * 60)
            print("EMAIL:", index)
            print("FROM:", item["from"])
            print("SUBJECT:", item["subject"])
            print("DATE:", item["date"])
            print("BODY:", item["body"][:500])

    except Exception as error:

        print("\nGMAIL ERROR:", error)

    finally:

        gmail.disconnect()
