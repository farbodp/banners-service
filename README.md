## FastAPI App - Top Marketing Banners

This is a FastAPI app that returns the top marketing banners based on the rules mentioned [here](https://i.datachef.co/tha-de).

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

### Stress test

Stress test script is written using the `locust` package and can be found in the locustfile.py file.

To run the web UI, enter the following command:

```sh
locust --users 50 --spawn-rate 5 --host=http://localhost:8000
```

#### Result

The stress test result (running locally) is shown in below:

![Stress test result](stress_test/stress_result.png "Stress test result")

Since I used caching, the response time gradually decreases as the results are being cached. Eventually, the app handles 160 rps, which is 9600 requests per minute.

#### Other soultions

I used caching to improve the performance, but other solutions can be:

* Use `async` endpoint (it is supported in FastAPI).
* merge CSV file before the server starts
* Use combination of caching and `async` endponits.

All of these soultions can be explored to find the best option.

### Logic for banner selection

The second requirement mentioned in the assignment is to never show one banner twice in a row for a unique visitor. This requirement and the business rules are somehow contradictory, but I tried to solve it this way:

First when a visitor visits the url, I go by the business rules (`top_banners_by_campaign_id` function). The second time, I pick the top 10 banners sort by the revenue and the clicks count, but excluding the previously shown banners (`top_banners_by_campaign_id_second_visit` function). I cache the visitors' IPs in `seen_banners_cache` variable, which is a TTL cached dictionary.