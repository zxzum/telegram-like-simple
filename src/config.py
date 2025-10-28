"""
Configuration for Simple Userbot
Get credentials from https://my.telegram.org/apps
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')

# Target chat and topic
CHAT_ID = int(os.getenv('CHAT_ID', -1002749060046))

# Parse TOPIC_ID - can be None, 0, or a number
topic_id_str = os.getenv('TOPIC_ID', '0').strip()
if topic_id_str.lower() in ('none', 'null', ''):
    TOPIC_ID = None
else:
    try:
        TOPIC_ID = int(topic_id_str)
    except ValueError:
        TOPIC_ID = None

# Session name
SESSION_NAME = os.getenv('SESSION_NAME', 'userbot')

# Bot settings
IGNORE_OWN_MESSAGES = os.getenv('IGNORE_OWN_MESSAGES', 'false').lower() == 'true'
IGNORE_BOT_MESSAGES = os.getenv('IGNORE_BOT_MESSAGES', 'false').lower() == 'true'

# Validation
if not API_ID or not API_HASH:
    raise ValueError("❌ API_ID and API_HASH must be set in .env file!")

print(f"✅ Config loaded:")
print(f"   CHAT_ID: {CHAT_ID}")
print(f"   TOPIC_ID: {TOPIC_ID}")
print(f"   IGNORE_OWN_MESSAGES: {IGNORE_OWN_MESSAGES}")
print(f"   IGNORE_BOT_MESSAGES: {IGNORE_BOT_MESSAGES}")