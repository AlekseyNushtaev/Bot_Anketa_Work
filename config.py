from dotenv import load_dotenv
import os

load_dotenv()

TG_TOKEN = os.environ.get("TG_TOKEN")
CHANEL_ID = int(os.environ.get("CHANEL_ID"))
