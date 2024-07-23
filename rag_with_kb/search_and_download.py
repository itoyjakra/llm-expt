"""Functions to search for a topic in arxiv and download papers."""

from datetime import datetime, timedelta
from tracemalloc import start

import arxiv
import pandas as pd
from loguru import logger
from pytz import timezone

client = arxiv.Client()


def search_arxiv(topic: str, max_results: int = 25) -> arxiv.Search:
    """Search arxiv for a topic"""
    return arxiv.Search(
        query=topic, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate
    )


def download_papers_by_date(
    topic: str, dates: tuple, max_results: int = 25
) -> pd.DataFrame:
    """Download papers from arxiv by date range"""
    start_date = pd.to_datetime(dates[0])
    end_date = pd.to_datetime(dates[1])

    search_results = search_arxiv(topic=topic, max_results=max_results)

    all_data = []
    for result in client.results(search_results):
        if result.updated < start_date:
            continue
        if result.updated > end_date:
            continue
        temp = [
            result.title,
            result.published,
            result.entry_id,
            result.summary,
            result.pdf_url,
            result.authors,
        ]
        all_data.append(temp)

    column_names = ["Title", "Date", "Id", "Summary", "URL", "Authors"]

    return pd.DataFrame(all_data, columns=column_names)


def test_download(topic="LLM"):
    """Download papers from the last 10 days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)
    start_date = start_date.replace(tzinfo=timezone("UTC"))
    end_date = end_date.replace(tzinfo=timezone("UTC"))
    dates = (start_date, end_date)

    df_papers = download_papers_by_date(topic, dates)

    logger.info(df_papers.info())
    logger.info(df_papers.head())
    logger.info(df_papers.Date.min())
    logger.info(df_papers.Date.max())

    topic = topic.lower().replace(" ", "_")
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")
    target_location = f"data/{topic}_papers_{start_date}_{end_date}.csv"
    df_papers.to_csv(f"{target_location}", index=False)
    logger.info(f"Saved papers to {target_location}")


def bulk_download(topic: str, max_results: int = 1_000) -> None:
    """Initial download of all 2024 papers."""
    start_date = datetime(2024, 1, 1).replace(tzinfo=timezone("UTC"))
    end_date = datetime.now().replace(tzinfo=timezone("UTC"))
    dates = (start_date, end_date)
    logger.info(f"Downloading papers from {start_date} to {end_date}")
    df_papers = download_papers_by_date(
        topic=topic, dates=dates, max_results=max_results
    )

    logger.info(df_papers.info())
    logger.info(df_papers.head())
    logger.info(df_papers.Date.min())
    logger.info(df_papers.Date.max())

    topic = topic.lower().replace(" ", "_")
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")
    target_location = f"data/{topic}_papers_{start_date}_{end_date}.csv"
    df_papers.to_csv(f"{target_location}", index=False)
    logger.info(f"Saved papers to {target_location}")


if __name__ == "__main__":
    # test_download(topic="Generative AI")
    bulk_download(topic="LLM")
