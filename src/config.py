"""
Configuration for Userbot
"""

import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')

CHAT_ID = int(os.getenv('CHAT_ID', -1002749060046))

topic_id_str = os.getenv('TOPIC_ID', '0').strip()
if topic_id_str.lower() in ('none', 'null', ''):
    TOPIC_ID = None
else:
    try:
        TOPIC_ID = int(topic_id_str)
    except ValueError:
        TOPIC_ID = None

SESSION_NAME = os.getenv('SESSION_NAME', 'userbot')

IGNORE_OWN_MESSAGES = os.getenv('IGNORE_OWN_MESSAGES', 'false').lower() == 'true'
IGNORE_BOT_MESSAGES = os.getenv('IGNORE_BOT_MESSAGES', 'false').lower() == 'true'

if not API_ID or not API_HASH:
    raise ValueError("❌ API_ID and API_HASH must be set!")

print(f"✅ Config: Chat={CHAT_ID}, Topic={TOPIC_ID}")