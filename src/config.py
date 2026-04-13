import logging
import os

import yaml
from dotenv import load_dotenv

load_dotenv()


def get_database_url():
    return os.getenv('DATABASE_URL', 'postgresql+asyncpg://user:password@localhost/mydatabase')


def config_logs():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(pathname)s - %(levelname)s - %(message)s')


def custom_openapi():
    with open('definition\\api-hospital.yaml', 'r') as file:
        return yaml.safe_load(file.read())
