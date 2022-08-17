import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

SECRET_KEY = os.environ.get("SECRET_KEY")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")

# Enable debug mode.
DEBUG = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Connect to the database


# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI ='postgresql://postgres:Postgresql1@localhost:5432/todovenu'