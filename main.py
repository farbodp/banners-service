import numpy as np
import pandas as pd
from random import shuffle
from cachetools import TTLCache
from functools import lru_cache
from fastapi import FastAPI, Query, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from utils.utils import (
    read_csv_remove_duplicates,
    get_hour_quarter,
    validate_campaign_id,
    join_dataframes,
    filter_campaign_data,
    calculate_banner_revenue_clicks,
    count_banners_with_conversions,
    select_top_revenue_banners,
    select_most_clicked_banners,
    select_random_banners,
    combine_top_banners,
    sort_banner_revenue_clicks,
    exclude_ids,
    select_top_rows,
)


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
        'conversions': ['1', '2', '3', '4'],
    }

    for file_type, file_nums in csv_files.items():
        for num in file_nums:
            file_path = f"csv/{num}/{file_type}_{num}.csv"
            log_file_path = f"logs/{file_type}_{num}_duplicates.log"

            csv_sets[f"{file_type}_{num}"] = read_csv_remove_duplicates(
                file_path, log_file_path
            )


@lru_cache(maxsize=128)
def top_banners_by_campaign_id(campaign_id, hour_quarter):
    impressions = csv_sets[f"impressions_{hour_quarter}"]
    clicks = csv_sets[f"clicks_{hour_quarter}"]
    conversions = csv_sets[f"conversions_{hour_quarter}"]

    validate_campaign_id(impressions, campaign_id)

    joined_data = join_dataframes(impressions, clicks, conversions)
    campaign_data = filter_campaign_data(joined_data, campaign_id)
    banner_revenue_clicks = calculate_banner_revenue_clicks(campaign_data)

    banners_with_conversions_count = count_banners_with_conversions(
        banner_revenue_clicks
    )

    top_banners = None

    if banners_with_conversions_count >= 10:
        top_banners = select_top_revenue_banners(banner_revenue_clicks, 10)
    elif 5 <= banners_with_conversions_count < 10:
        top_banners = select_top_revenue_banners(
            banner_revenue_clicks, banners_with_conversions_count
        )
    elif 1 <= banners_with_conversions_count < 5:
        most_conversion_banners = select_top_revenue_banners(
            banner_revenue_clicks, banners_with_conversions_count
        )
        most_clicked_banners = select_most_clicked_banners(
            banner_revenue_clicks
        )
        top_banners = combine_top_banners(
            most_conversion_banners, most_clicked_banners
        )
    else:
        most_clicked_banners = select_most_clicked_banners(
            banner_revenue_clicks
        )
        clicked_banners_count = most_clicked_banners.shape[0]

        if clicked_banners_count < 5:
            random_rows_count = 5 - clicked_banners_count
            random_banners = select_random_banners(
                banner_revenue_clicks, random_rows_count
            )
            top_banners = combine_top_banners(
                most_clicked_banners, random_banners
            )
        else:
            top_banners = most_clicked_banners

    return list(top_banners.index)


@lru_cache(maxsize=128)
def top_banners_by_campaign_id_second_visit(
    campaign_id, hour_quarter, visitor_ip
):
    impressions, clicks, conversions = (
        csv_sets[f"impressions_{hour_quarter}"],
        csv_sets[f"clicks_{hour_quarter}"],
        csv_sets[f"conversions_{hour_quarter}"],
    )

    validate_campaign_id(impressions, campaign_id)

    joined_data = join_dataframes(impressions, clicks, conversions)
    campaign_data = filter_campaign_data(joined_data, campaign_id)
    banner_revenue_clicks = calculate_banner_revenue_clicks(campaign_data)

    banner_revenue_clicks_sorted = sort_banner_revenue_clicks(banner_revenue_clicks)

    excluded_ids = seen_banners_cache[visitor_ip]
    top_banners_excluded_ids = exclude_ids(banner_revenue_clicks_sorted, excluded_ids)
    top_banners_second_visit = select_top_rows(banner_revenue_clicks_sorted, 10)

    return list(top_banners_second_visit.index)


@app.get("/campaigns/{campaign_id}", response_class=HTMLResponse)
def get_images(campaign_id: int, request: Request):
    hour_quarter = get_hour_quarter()
    # We check the cache (seen_banners_cache), if the value for an IP is None,
    # then we follow the business rules, but if value is a list of seen ids,
    # we return the top 10 row, excluding the seen ids.
    visitor_ip = request.client.host

    if (
        visitor_ip in seen_banners_cache
        and seen_banners_cache[visitor_ip] is not None
    ):
        top_banner_ids = top_banners_by_campaign_id_second_visit(
            campaign_id, hour_quarter, visitor_ip
        )
        seen_banners_cache[visitor_ip] = None
    else:
        top_banner_ids = top_banners_by_campaign_id(
            campaign_id=campaign_id, hour_quarter=hour_quarter
        )
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
