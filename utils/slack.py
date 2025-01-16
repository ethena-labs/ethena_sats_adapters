import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()


def slack_message(message: str):
    if os.getenv("SLACK_WEBHOOK", "") == "":
        logging.info("Slack webhook not set, skipping message")
        return
    response = requests.post(
        os.getenv("SLACK_WEBHOOK", ""),
        json={
            "text": message,
        },
        timeout=60,
    )
    logging.info(f"Slack response: {response}")
