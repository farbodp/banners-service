# Top Banner Ads

This is a single web page application that serves banner ads on a website. Banners are selected based on their revenue performance. While the web app itself is relatively straightforward (picture shown in below), its purpose is to showcase the banners selection logic of the backend.

![banners web app](images/banners.png)

Dataset consists of 3 csv files:

1. impressions.csv
    - columns: `banner_id`, `campaign_id`
2. clicks.csv
    - columns: `click_id`, `banner_id`, `campaign_id`
3. conversions.csv
    - columns: `conversion_id`, `click_id`, `revenue`

By querying the above data sets, performance of the banners based on their revenue can be found (available in the conversions.csv).

##  Business Rules :briefcase:

If you assume `X is the number of banners with conversions within a campaign`, then there are a few possible scenarios:

| Scenario      | Requirement |
| ------------- |-------------|
| X>=10         | Show the Top 10 banners based on revenue within that campaign |
| X in range(5, 10)      | Show the Top X banners based on revenue within that campaign      |
| X in range(1,5) | Collection of banners should consist of 5 banners, containing: The top x banners based on revenue within that campaign and Banners with the most clicks within that campaign to make up a collection of 5 unique banners.      |
| X == 0 | Show the top ­5 banners based on clicks. If the number of banners with clicks is less than 5 within that campaign, then you should add random banners to make up a collection of 5 unique banners. |

## Technical Requirements

1. To avoid saturation for visitors, we believe that the top banners being served should not follow a fixed order based on their performance; but they should appear in a random sequence.

2. You should also avoid having a banner served twice in a row for a unique visitor.

3. The 4 sets of CSV's represent the 4 quarters of an hour. So when I visit the website during 00m­-15m (excluding 15), I want to see banners being served based on the statistics of the first dataset, and if I visit your site during 15m-­30m, I want to see the banners being served based on the second dataset, so on so forth.

4. The application should serve at least 5000 requests per minute ­ The script and results of the stress­ test should be provided.

### Installation

1. Clone the repository.
2. Install the dependencies
```sh
pip install -r requirements.txt
```

### Running the App

You can run the app using either uvicorn or gunicorn.

#### Using uvicorn

Open a terminal and navigate to the root directory of the app. Run the following command: 

```sh
uvicorn main:app --reload
```

#### Using gunicorn (for production)

Open a terminal and navigate to the root directory of the app.

Run the following command:
```sh
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Stress test

Stress test script is written using the `locust` package and can be found in the locustfile.py file.

To run the web UI, enter the following command:

```sh
locust --users 50 --spawn-rate 5 --host=http://localhost:8000
```

### Result

The stress test result (running locally) is shown in below:

![Stress test result](stress_test/stress_result.png "Stress test result")

Since I used caching, the response time gradually decreases as the results are being cached. Eventually, the app handles 160 rps, which is 9600 requests per minute. It should be mentioned that we have 50 concurrent users in this stress test, as stated in the command above.

## Other soultions

I used caching to improve the performance, but other solutions can be:

* Use `async` endpoint (it is supported in FastAPI).
* merge CSV file before the server starts
* Use combination of caching and `async` endponits.

All of these soultions can be explored to find the best option.

## Logic for banner selection

The second requirement mentioned in the assignment is to never show one banner twice in a row for a unique visitor. This requirement and the business rules are somehow contradictory, but I tried to solve it this way:

First when a visitor visits the url, I go by the business rules (`top_banners_by_campaign_id` function). The second time, I pick the top 10 banners sort by the revenue and the clicks count, but excluding the previously shown banners (`top_banners_by_campaign_id_second_visit` function). I cache the visitors' IPs in `seen_banners_cache` variable, which is a TTL cached dictionary.