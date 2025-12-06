import os

class Config:
    SLEEPER_API_BASE = "https://api.sleeper.app/v1"
    SLEEPER_AVATAR_BASE = "https://sleepercdn.com/avatars/thumbs"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
