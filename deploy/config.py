import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')

host = "localhost"
DATABASE_URL = f'postgresql://stan:stan@localhost:5432/bot_teach'

ADMIN_IDS = [589380091, 436985071, 336609833]
