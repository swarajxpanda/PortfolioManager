import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
REDIRECT_URL = os.getenv("REDIRECT_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")