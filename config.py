import os

class Config:
    SLEEPER_API_BASE = "https://api.sleeper.app/v1"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SLEEPER_AVATAR_BASE = "https://sleepercdn.com/avatars/thumbs"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
