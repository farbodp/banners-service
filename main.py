import numpy as np
import pandas as pd
from random import shuffle
from cachetools import TTLCache
from functools import lru_cache
from fastapi import FastAPI, Query, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from utils.utils import read_csv_remove_duplicates, get_hour_quarter
# from async_lru import alru_cache



STATIC_DIR_NAME = "static"
app = FastAPI()
app.mount("/static", StaticFiles(directory="images"), name=STATIC_DIR_NAME)

csv_sets = {}
seen_banners_cache = TTLCache(maxsize=100, ttl=60)

@app.on_event("startup")
def startup_event():
    csv_files = {
        'impressions': ['1', '2', '3', '4'],
        'clicks': ['1', '2', '3', '4'],
        'conversions': ['1', '2', '3', '4']
    }

    for file_type, file_nums in csv_files.items():
        for num in file_nums:
            file_path = f"csv/{num}/{file_type}_{num}.csv"
            log_file_path = f"logs/{file_type}_{num}_duplicates.log"

            csv_sets[f"{file_type}_{num}"] = read_csv_remove_duplicates(file_path, log_file_path)

@lru_cache(maxsize=128)
def top_banners_by_campaign_id_second_visit(campaign_id, hour_quarter, visitor_ip):
    impressions, clicks, conversions = csv_sets[f"impressions_{hour_quarter}"], csv_sets[f"clicks_{hour_quarter}"], csv_sets[f"conversions_{hour_quarter}"]

    if campaign_id not in impressions['campaign_id'].unique():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Join the dataframes together
    impressions_clicks = pd.merge(impressions, clicks, on=["banner_id", "campaign_id"], how="outer")


    impressions_clicks_conversions = pd.merge(impressions_clicks, conversions, on="click_id", how="left")

    # Filter by the campaign_id
    campaign_data = impressions_clicks_conversions[impressions_clicks_conversions["campaign_id"] == campaign_id]

    # Group by banner_id and sum the revenue
    banner_revenue_clicks = campaign_data.groupby("banner_id").agg(
        revenue = pd.NamedAgg(column="revenue", aggfunc="sum"),
        clicks_count = pd.NamedAgg(column="click_id", aggfunc=lambda x: x.notnull().sum()),
    )

    banner_revenue_clicks_sorted = banner_revenue_clicks.sort_values(by=['revenue', 'clicks_count'], ascending=[False, False])
    excluded_ids = seen_banners_cache[visitor_ip]
    top_banners_second_visit = banner_revenue_clicks_sorted[~banner_revenue_clicks_sorted.index.isin(excluded_ids)].head(10)

    return list(top_banners_second_visit.index)


@lru_cache(maxsize=128)
def top_banners_by_campaign_id(campaign_id, hour_quarter):

    
    impressions, clicks, conversions = csv_sets[f"impressions_{hour_quarter}"], csv_sets[f"clicks_{hour_quarter}"], csv_sets[f"conversions_{hour_quarter}"]

    if campaign_id not in impressions['campaign_id'].unique():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # clicks = read_csv_remove_duplicates(f"csv/{hour_quarter}/clicks_{hour_quarter}.csv", log_file_path=f'logs/clicks_{hour_quarter}_duplicates.log')
    # conversions = read_csv_remove_duplicates(f"csv/{hour_quarter}/conversions_{hour_quarter}.csv", log_file_path=f'logs/conversions_{hour_quarter}_duplicates.log')

    # Join the dataframes together
    impressions_clicks = pd.merge(impressions, clicks, on=["banner_id", "campaign_id"], how="outer")


    impressions_clicks_conversions = pd.merge(impressions_clicks, conversions, on="click_id", how="left")

    # Filter by the campaign_id
    campaign_data = impressions_clicks_conversions[impressions_clicks_conversions["campaign_id"] == campaign_id]

    # Group by banner_id and sum the revenue
    banner_revenue_clicks = campaign_data.groupby("banner_id").agg(
        revenue = pd.NamedAgg(column="revenue", aggfunc="sum"),
        clicks_count = pd.NamedAgg(column="click_id", aggfunc=lambda x: x.notnull().sum()),
    )

    banners_with_conversions_count = (banner_revenue_clicks["revenue"] > 0).sum()
    

    if banners_with_conversions_count >= 10:
        top_banners = banner_revenue_clicks.sort_values('revenue', ascending=False).head(10)

    elif 5 <= banners_with_conversions_count < 10:
        top_banners = banner_revenue_clicks.sort_values('revenue' ,ascending=False).head(banners_with_conversions_count)

    elif 1 <= banners_with_conversions_count < 5:
        most_conversion_banners = banner_revenue_clicks.sort_values('revenue' ,ascending=False).head(banners_with_conversions_count)
        most_clicked_banners = banner_revenue_clicks[banner_revenue_clicks['revenue'] == 0].sort_values('clicks_count', ascending=False).head(5-banner_revenue_clicks)
        top_banners = pd.concat([most_conversion_banners, most_clicked_banners], axis=0)

    else:
        most_clicked_banners = banner_revenue_clicks[banner_revenue_clicks['clicks_count'] > 0].sort_values('clicks_count', ascending=False)

        # check count of banners with clicks
        clicked_banners_count = most_clicked_banners.shape[0]

        if clicked_banners_count < 5:
            random_rows_count = 5-clicked_banners_count
            # randomly select 2 rows from the dataframe
            random_banners = banner_revenue_clicks[banner_revenue_clicks['clicks_count'] == 0].sample(n=random_rows_count)
            top_banners = pd.concat([most_clicked_banners, random_banners], axis=0)
        else:
            top_banners = most_clicked_banners

    return list(top_banners.index)


@app.get("/campaigns/{campaign_id}", response_class=HTMLResponse)
def get_images(campaign_id: int, request: Request):
    hour_quarter = get_hour_quarter()
    # We check the cache (seen_banners_cache), if the value for an IP is None,
    # then we follow the business rules, but if value is a list of seen ids,
    # we return the top 10 row, excluding the seen ids.
    visitor_ip = request.client.host

    if visitor_ip in seen_banners_cache and seen_banners_cache[visitor_ip] is not None:
        top_banner_ids = top_banners_by_campaign_id_second_visit(campaign_id, hour_quarter, visitor_ip)
        seen_banners_cache[visitor_ip] = None
    else:
        top_banner_ids = top_banners_by_campaign_id(campaign_id = campaign_id, hour_quarter=hour_quarter)
        seen_banners_cache[visitor_ip] = top_banner_ids
    

    shuffled_banner_ids = shuffle(top_banner_ids)

    html_content = """
        <html>
            <head>
                <title>Top Banners</title>
            </head>
            <body>
                <h1>Top Banners</h1>
                <div>
        """
    
    for banner_id in top_banner_ids:
        html_content += f'<img src="/{STATIC_DIR_NAME}/image_{banner_id}.png" width="200" height="200"/>\n'
    
    html_content += """
                </div>
            </body>
        </html>
    """

    return html_content
