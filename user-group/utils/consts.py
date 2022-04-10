import os
import logging

SUBSCRIBERS_TABLE = "subscribers"
SCHEDULED_MESSAGES_TABLE = "scheduled_messages"
SCHEDULED_MESSAGES_BUCKET = os.environ.get("SCHEDULED_MESSAGES_BUCKET_NAME")
SOURCE_EMAIL = os.environ.get("SOURCE_EMAIL")

logger = logging.getLogger()
logger.setLevel(logging.INFO)