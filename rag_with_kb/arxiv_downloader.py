"""Class definition if ArxivDownloader
-- search for a topic in arxiv 
-- download and papers
"""

import imp
import os
from datetime import datetime, timedelta

import arxiv
import boto3
import pandas as pd
from loguru import logger
from pytz import timezone

from read_yaml import read_yaml_file

dynamodb = boto3.resource("dynamodb")


class ArxivDownloader:
    def __init__(
        self,
        topic: str,
        start_date: str,
        end_date: str,
        db_name: str,
        max_results: int = 10_000,
    ):
        self.client = arxiv.Client()
        self.topic = topic
        self.db_name = db_name
        self.max_results = max_results
        self.start_date = pd.to_datetime(start_date).replace(tzinfo=timezone("UTC"))
        self.end_date = pd.to_datetime(end_date).replace(tzinfo=timezone("UTC"))

    def set_start_date(self, start_date: str):
        """Set the start date for the download."""
        self.start_date = pd.to_datetime(start_date).replace(tzinfo=timezone("UTC"))

    def set_end_date(self, end_date: str):
        """Set the end date for the download."""
        self.end_date = pd.to_datetime(end_date).replace(tzinfo=timezone("UTC"))

    def search_arxiv(self) -> arxiv.Search:
        """Search arxiv for a topic"""
        return arxiv.Search(
            query=self.topic,
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

    def download_papers_by_date(self) -> pd.DataFrame:
        """Download papers from arxiv by date range"""
        search_results = self.search_arxiv()

        all_data = []
        for result in self.client.results(search_results):
            if result.updated < self.start_date:
                continue
            if result.updated > self.end_date:
                continue
            assert result.updated.tzinfo is not None
            assert result.updated >= self.start_date
            assert result.updated <= self.end_date
            temp = [
                result.title,
                result.published,
                result.entry_id,
                result.summary,
                result.pdf_url,
                [auth.name for auth in result.authors],
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

    def bulk_download(self) -> pd.DataFrame:
        """Initial download of all 2024 papers."""
        topic = self.topic.lower().replace(" ", "_")
        start_date = self.start_date.strftime("%Y-%m-%d")
        end_date = self.end_date.strftime("%Y-%m-%d")
        target_location = f"data/{topic}_papers_{start_date}_{end_date}.csv"

        logger.info(f"Downloading papers from {self.start_date} to {self.end_date}")
        df_papers = self.download_papers_by_date()
        df_papers.to_csv(target_location, index=False)
        logger.info(f"Saved papers to {target_location}")

        logger.info(df_papers.info())
        logger.info(df_papers.head())
        logger.info(df_papers.Date.min())
        logger.info(df_papers.Date.max())

        return df_papers

    def bulk_download_to_db(self) -> None:
        """Download papers from arxiv and add them to a DynamoDB table."""
        # Download papers
        df_papers = self.bulk_download()
        logger.debug(df_papers.info())

        logger.info("inserting items into DynamoDB")
        # Get the table
        table = dynamodb.Table(self.db_name)
        # Insert papers into the DynamoDB table
        for index, row in df_papers.iterrows():
            # Prepare the item to be inserted
            item = {
                "EntryId": row["Id"],
                "Title": row["Title"],
                "Published": row["Date"].strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),  # Convert timestamp to ISO 8601 format
                "Summary": row["Summary"],
                "URL": row["URL"],
                "Authors": row["Authors"],
            }

            # Insert the item into the table
            table.put_item(Item=item)

    def daily_download(self) -> pd.DataFrame:
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

        logger.info(df_papers.info())
        logger.info(df_papers.head())

        # Prepare the filename with the current date
        filename = f"data/{self.topic}_papers_{start_date.strftime('%Y-%m-%d')}.csv"

        # Save the results to a CSV file
        df_papers.to_csv(filename, index=False)
        logger.info(f"Saved papers to {filename}")

        return df_papers

    def daily_download_to_db(self) -> None:
        """Download papers published in the last 24 hours
        and add them to a DynamoDB table."""
        # Initialize the DynamoDB client
        table = dynamodb.Table(self.db_name)

        # Download papers for the last day
        df_papers = self.daily_download()

        # Check for duplicates and add new papers to the DynamoDB table
        for index, row in df_papers.iterrows():
            # Prepare the item to be inserted
            item = {
                "Title": row["Title"],
                "Published": row["Date"],
                "EntryId": row["Id"],
                "Summary": row["Summary"],
                "URL": row["URL"],
                "Authors": row["Authors"],
            }

            # Check if the paper already exists in the table
            response = table.get_item(Key={"EntryId": item["EntryId"]})
            if "Item" not in response:
                # The paper is new, so add it to the table
                table.put_item(Item=item)
                print(f"Added new paper: {item['Title']}")
            else:
                print(f"Paper already exists: {item['Title']}")


if __name__ == "__main__":
    # Perform a bulk download of all 2024 papers on LLM
    topic = "LLM"
    start_date = "2024-01-01"
    end_date = "2024-03-23"
    dynamodb_table = read_yaml_file("infra.yaml")
    downloader = ArxivDownloader(
        topic=topic,
        start_date=start_date,
        end_date=end_date,
        db_name=dynamodb_table,
        max_results=5000,
    )
    downloader.bulk_download_to_db()
    logger.info("Bulk download completed.")
