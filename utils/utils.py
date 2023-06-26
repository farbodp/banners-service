import pandas as pd
import logging
from functools import lru_cache
import datetime


def read_csv_remove_duplicates(file_path, log_file_path=None):
    df = pd.read_csv(file_path)

    if log_file_path:
        log_duplicates(file_path, df, log_file_path)

    remove_duplicates(df)

    return df

def log_duplicates(file_path, df, log_file_path):
    duplicates = df[df.duplicated()]
    if duplicates.empty:
        return

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.debug(f"Found {len(duplicates)} duplicate rows in {file_path}:\n{duplicates.to_string()}")

def remove_duplicates(df):
    df.drop_duplicates(inplace=True)

def get_hour_quarter():
    now = datetime.datetime.utcnow()
    minute = now.minute
    quarter = minute // 15 + 1
    return quarter