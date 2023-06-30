import pandas as pd
import logging
from functools import lru_cache
import datetime
from fastapi import HTTPException


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
    logger.debug(
        f"Found {len(duplicates)} duplicate rows in {file_path}:\n{duplicates.to_string()}"
    )


def remove_duplicates(df):
    df.drop_duplicates(inplace=True)


def get_hour_quarter():
    now = datetime.datetime.utcnow()
    minute = now.minute
    quarter = minute // 15 + 1
    return quarter


def validate_campaign_id(impressions, campaign_id):
    if campaign_id not in impressions['campaign_id'].unique():
        raise HTTPException(status_code=404, detail="Campaign not found")


def join_dataframes(impressions, clicks, conversions):
    impressions_clicks = pd.merge(
        impressions, clicks, on=["banner_id", "campaign_id"], how="outer"
    )
    return pd.merge(impressions_clicks, conversions, on="click_id", how="left")


def filter_campaign_data(data, campaign_id):
    return data[data["campaign_id"] == campaign_id]


def calculate_banner_revenue_clicks(data):
    return data.groupby("banner_id").agg(
        revenue=pd.NamedAgg(column="revenue", aggfunc="sum"),
        clicks_count=pd.NamedAgg(
            column="click_id", aggfunc=lambda x: x.notnull().sum()
        ),
    )


def count_banners_with_conversions(data):
    return (data["revenue"] > 0).sum()


def select_top_revenue_banners(data, count):
    return data.sort_values('revenue', ascending=False).head(count)


def select_most_clicked_banners(data):
    return data[data['clicks_count'] > 0].sort_values(
        'clicks_count', ascending=False
    )


def select_random_banners(data, count):
    return data[data['clicks_count'] == 0].sample(n=count)


def combine_top_banners(banners1, banners2):
    return pd.concat([banners1, banners2], axis=0)

def sort_banner_revenue_clicks(banner_revenue_clicks):
    return banner_revenue_clicks.sort_values(by=['revenue', 'clicks_count'], ascending=[False, False])

def exclude_ids(df, excluded_ids):
    df = df[~df.index.isin(excluded_ids)]
    return df

def select_top_rows(df, count):
    return df.head(count)