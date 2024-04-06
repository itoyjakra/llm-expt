"""Lambda function to scrape new papers available in the last day."""

from datetime import datetime, timedelta


from arxiv_downloader import ArxivDownloader


def lambda_handler(event, context):
    """Lambda function to scrape new papers available in the last day."""

    print("event payload...")
    print(event)

    # Calculate yesterday's date and today's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_date = yesterday.strftime("%Y-%m-%d")

    today = datetime.now()
    today_date = today.strftime("%Y-%m-%d")

    start_date = event.get(
        "start_date", yesterday_date
    )  # Default to yesterday's date if not provided
    end_date = event.get(
        "end_date", today_date
    )  # Default to today's date if not provided

    topic = event.get("topic")
    dynamodb_table = event.get("db_name")
    max_results = event.get("max_results", 100))

    # Initialize the ArxivDownloader with the specified parameters
    downloader = ArxivDownloader(
        topic=topic,
        start_date=start_date,
        end_date=end_date,
        db_name=dynamodb_table,
        max_results=max_results
    )

    # Call the daily_download_to_db method to download and add papers to the DynamoDB table
    downloader.daily_download_to_db()

    print("Daily download completed.")
