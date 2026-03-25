import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
    VTPASS_API_KEY = os.getenv("VTPASS_API_KEY")
    VTPASS_PUBLIC_KEY = os.getenv("VTPASS_PUBLIC_KEY")
