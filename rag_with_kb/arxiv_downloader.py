"""Class definition of ArxivDownloader
-- search for a topic in arxiv 
-- download and papers
"""

from dataclasses import dataclass
from typing import Optional

import arxiv
import boto3
import pandas as pd
from loguru import logger
from pytz import timezone

dynamodb = boto3.resource("dynamodb")


@dataclass
class TestPaperDownloadArgs:
    """Holds constructor arguments for ArxivDownloader class"""

    topic: str
    start_date: str
    end_date: str
    dynamodb_table: str
    max_results: int


class ArxivDownloader:
    """Downloads arxiv papers on a topic
    for a given date range
    and stores them in a dynamodb table
    """

    def __init__(
        self,
        topic: str,
        start_date: str,
        end_date: str,
        db_name: str,
        max_results: int = 10_000,
    ):
        self.client = arxiv.Client()
        self.topic = topic.lower().replace(" ", "_")
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

    def query_arxiv_for_topic(self) -> arxiv.Search:
        """Searches arxiv for a topic"""
        return arxiv.Search(
            query=self.topic,
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

    def download_paper_metadata_by_date(self) -> pd.DataFrame:
        """Download paper metadata and save to a dataframe"""
        search_results = self.query_arxiv_for_topic()

        logger.info(f"start date for download: {self.start_date}")
        logger.info(f"end date for download: {self.end_date}")

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
        df_papers = self.download_paper_metadata_by_date()

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

    # def download_paper_metadata(self) -> pd.DataFrame:
    #     """Download paper metadata and save to a dataframe"""
    #     start_date = self.start_date.strftime("%Y-%m-%d")
    #     end_date = self.end_date.strftime("%Y-%m-%d")
    #     target_location = f"data/{topic}_papers_{start_date}_{end_date}.csv"

    #     logger.info(f"Downloading papers from {self.start_date} to {self.end_date}")
    #     df_papers = self.download_paper_metadata_by_date()
    #     df_papers.to_csv(target_location, index=False)
    #     logger.info(f"Saved papers to {target_location}")

    #     logger.info(df_papers.info())
    #     logger.info(df_papers.head())
    #     logger.info(df_papers.Date.min())
    #     logger.info(df_papers.Date.max())

    #     return df_papers

    def save_metadata_to_ddb(self) -> None:
        """Download papers from arxiv and add them to a DynamoDB table."""
        # Download papers
        df_papers = self.download_paper_metadata_by_date()
        logger.debug(df_papers.info())

        logger.info("inserting items into DynamoDB")
        table = dynamodb.Table(self.db_name)
        # Insert papers into the DynamoDB table
        for _, row in df_papers.iterrows():
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
            # Check if the paper already exists in the table
            response = table.get_item(Key={"EntryId": item["EntryId"]})
            if "Item" not in response:
                # The paper is new, so add it to the table
                table.put_item(Item=item)
                logger.info(f"Added new paper: {item['Title']}")
            else:
                logger.info(f"Paper already exists: {item['Title']}")


def test_paper_download(args: TestPaperDownloadArgs) -> None:
    """Test paper download"""

    downloader = ArxivDownloader(
        topic=args.topic,
        start_date=args.start_date,
        end_date=args.end_date,
        db_name=args.dynamodb_table,
        max_results=args.max_results,
    )

    # test scraping of metadata from Arxiv
    # df_papers = downloader.download_paper_metadata_by_date()
    # logger.info(df_papers.info())
    # logger.info(df_papers.head())

    # test insertion of metadata to dynamodb table
    downloader.save_metadata_to_ddb()


if __name__ == "__main__":
    test_paper_download(
        TestPaperDownloadArgs(
            topic="LLM",
            start_date="2024-03-23",
            end_date="2024-03-26",
            dynamodb_table="arxiv_papers_master_collection",
            max_results=1_000,
        )
    )
