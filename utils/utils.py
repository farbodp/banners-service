import pandas as pd
import logging
from functools import lru_cache
import datetime


# @lru_cache(maxsize=32)
def read_csv_remove_duplicates(file_path, log_file_path=None):
    # Read CSV file into a pandas DataFrame
    df = pd.read_csv(file_path)

    # Identify duplicate rows in the DataFrame
    duplicates = df[df.duplicated()]

    # Log duplicate rows to a file using the Python logging module if log_file_path is provided
    if log_file_path is not None:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if not duplicates.empty:
            logger.debug(f"Found {len(duplicates)} duplicate rows in {file_path}:\n{duplicates.to_string()}")

    # Remove duplicate rows from the DataFrame
    df.drop_duplicates(inplace=True)

    return df


def get_hour_quarter():
    now = datetime.datetime.utcnow()
    minute = now.minute
    quarter = minute // 15 + 1
    return quarter