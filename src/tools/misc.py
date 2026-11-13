# ---- Libraries -------------------------------------------------------
from fastmcp import FastMCP

from datetime import datetime, timezone, date
import urllib.request
import socket
import time
import imaplib
import smtplib
import email
from email.policy import default
from email.message import EmailMessage
import os

# ---- MCP -------------------------------------------------------------
misc_mcp = FastMCP("AI Task Agent")

# ---- Screen & Input --------------------------------------------------
@misc_mcp.tool
def delay(milliseconds: int) -> str:
    """Pauses execution for a specified duration.
    Use to allow applications, menus, pages, or other operations time to finish before continuing.

    Args:
        milliseconds: The duration to wait, in milliseconds.

    Returns:
        A message confirming the requested delay.
    """
    time.sleep(milliseconds / 1000)
    return f"Waited {milliseconds} milliseconds."


# ---- Environment -----------------------------------------------------
@misc_mcp.tool
def get_environment_info() -> str:
    """Reports information about the current execution environment.
    Use to check the current date and time, timezone, hostname, local IP, and internet connectivity. An external service is queried to determine the public IP.

    Args:
        None.

    Returns:
        A text report containing the available environment information.
    """
    has_internet = False
    try:
        public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8')
        has_internet = True
    except:
        public_ip = "N/A"


    return f"""
    The current time in UTC is {datetime.now(timezone.utc)}.
    The current time for the User is {datetime.now().astimezone()}.
    The User's timezone is {datetime.now().astimezone().tzname()}.
    Today is {date.today()} (YYYY-MM-DD).
    The current day of the week is {datetime.now().strftime('%A')}.
    The machine's hostname is {socket.gethostname()}.
    The local IP address is {socket.gethostbyname(socket.gethostname())}.
    Does the machine have Internet (T/F)? {has_internet}.
    If the machine has Internet it's public IP address is {public_ip}
    """

# email system
# Read email
@misc_mcp.tool
def read_email(n: int) -> dict:
    """Reads the latest n emails in the inbox.
    Use to get recent emails from the user-specified email.

    Args:
        n: The latest n emails in the inbox.

    Returns:
        A dictionary of the most recent emails, starting from the least recent.
    """
    emaildict = dict()
    emailstr = ""
    emailhost = os.environ.get("EMAIL_HOST", "").strip()
    useremail = os.environ.get("USER_EMAIL", "").strip()
    userpassword = os.environ.get("USER_PASSWORD", "").strip()

    # if missing any of these environment variables, email will not be possible, so return error
    if (not emailhost) or (not useremail) or (not userpassword):
        raise SystemExit("EMAIL_HOST or USER_EMAIL or USER_PASSWORD is not set. Configure these in the .env file.")
    # connect to email host server
    mail = imaplib.IMAP4_SSL(emailhost)
    mail.login(useremail, userpassword)


    # read from inbox
    mail.select('inbox')


    # search
    status, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()


    if not email_ids:
        raise SystemExit("Inbox is empty.")

    
    # get latest n email ids
    latestn = email_ids[-n:]

    for e in range(len(latestn)):
        curr = latestn[e]

        status, data = mail.fetch(curr, '(RFC822)')

        # raw email in bytes
        raw = data[0][1]
        # message
        msg = email.message_from_bytes(raw, policy=default)

        # get who it is from and the subject
        emailstr += f"From: {msg['From']}\n"
        emailstr += f"Subject: {msg['Subject']}\n"
        # get body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    emailstr += 'Body:\n' + part.get_content()
                    break
        else:
            emailstr += 'Body:\n' + msg.get_content()

        emailstr += '\n'
        emaildict[f"{len(latestn)-e}th latest email"] = emailstr
        emailstr = ""
    # all done
    mail.logout()

    return {
        "emaildictionary":emaildict
    }


# Send email
@misc_mcp.tool
def send_email(recipient: str, subject: str, body:str) -> str:
    """ Sends an email.
    Use to send emails to recipients.

    Args:
        recipient: The email address you are sending the email to.
        subject: The subject of the email you are sending.
        body: The body of the email you are sending.
    
    Returns:
        A string confirmation that the email was sent.
    """
    emailhost = os.environ.get("EMAIL_HOST", "").strip()
    useremail = os.environ.get("USER_EMAIL", "").strip()
    userpassword = os.environ.get("USER_PASSWORD", "").strip()

    # if missing any of these environment variables, email will not be possible, so return error
    if (not emailhost) or (not useremail) or (not userpassword):
        raise SystemExit("EMAIL_HOST or USER_EMAIL or USER_PASSWORD is not set. Configure these in the .env file.")

    # set up the email
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = useremail
    msg['To'] = recipient

    # send the email with stmp ssl
    with smtplib.SMTP_SSL(emailhost, 465) as smtp:
        smtp.login(useremail, userpassword)
        smtp.send_message(msg)
    
    return "Email has been sent."