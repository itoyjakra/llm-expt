"""Class definition if ArxivDownloader
-- search for a topic in arxiv 
-- download and papers
"""

import os
from datetime import datetime, timedelta

import arxiv
import pandas as pd
from loguru import logger
from pytz import timezone


class ArxivDownloader:
    def __init__(self, topic: str, start_date: str, end_date: str):
        self.client = arxiv.Client()
        self.topic = topic
        self.start_date = pd.to_datetime(start_date).replace(tzinfo=timezone("UTC"))
        self.end_date = pd.to_datetime(end_date).replace(tzinfo=timezone("UTC"))

    def set_start_date(self, start_date: str):
        """Set the start date for the download."""
        self.start_date = pd.to_datetime(start_date).replace(tzinfo=timezone("UTC"))

    def set_end_date(self, end_date: str):
        """Set the end date for the download."""
        self.end_date = pd.to_datetime(end_date).replace(tzinfo=timezone("UTC"))

    def search_arxiv(self, max_results: int = 25) -> arxiv.Search:
        """Search arxiv for a topic"""
        return arxiv.Search(
            query=self.topic,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

    def download_papers_by_date(self, max_results: int = 25) -> pd.DataFrame:
        """Download papers from arxiv by date range"""
        search_results = self.search_arxiv(max_results=max_results)

        all_data = []
        for result in self.client.results(search_results):
            if result.updated < self.start_date:
                continue
            if result.updated > self.end_date:
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

    def test_download(self):
        """Download papers from the last 10 days"""
        df_papers = self.download_papers_by_date()

        logger.info(df_papers.info())
        logger.info(df_papers.head())
        logger.info(df_papers.Date.min())
        logger.info(df_papers.Date.max())

        topic = self.topic.lower().replace(" ", "_")
        start_date = self.start_date.strftime("%Y-%m-%d")
        end_date = self.end_date.strftime("%Y-%m-%d")
        target_location = f"data/{topic}_papers_{start_date}_{end_date}.csv"
        df_papers.to_csv(f"{target_location}", index=False)
        logger.info(f"Saved papers to {target_location}")

    def bulk_download(self, max_results: int = 1_000) -> None:
        """Initial download of all 2024 papers."""
        topic = self.topic.lower().replace(" ", "_")
        start_date = self.start_date.strftime("%Y-%m-%d")
        end_date = self.end_date.strftime("%Y-%m-%d")
        target_location = f"data/{topic}_papers_{start_date}_{end_date}.csv"

        # Check if the file already exists
        if os.path.exists(target_location):
            logger.info(f"File {target_location} already exists. Skipping download.")
            return

        logger.info(f"Downloading papers from {self.start_date} to {self.end_date}")
        df_papers = self.download_papers_by_date(max_results=max_results)

        logger.info(df_papers.info())
        logger.info(df_papers.head())
        logger.info(df_papers.Date.min())
        logger.info(df_papers.Date.max())

        df_papers.to_csv(target_location, index=False)
        logger.info(f"Saved papers to {target_location}")

        def daily_download(self):
            """Download papers published in the last day and save the results in a CSV file."""
            # Calculate the start and end dates for the last day
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            start_date = start_date.replace(tzinfo=timezone("UTC"))
            end_date = end_date.replace(tzinfo=timezone("UTC"))

            # Update the downloader's start and end dates to the last day
            self.set_start_date(start_date.strftime("%Y-%m-%d"))
            self.set_end_date(end_date.strftime("%Y-%m-%d"))

            # Download papers for the last day
            df_papers = self.download_papers_by_date()

            # Prepare the filename with the current date
            filename = f"data/{self.topic}_papers_{start_date.strftime('%Y-%m-%d')}.csv"

            # Save the results to a CSV file
            df_papers.to_csv(filename, index=False)
            logger.info(f"Saved papers to {filename}")
