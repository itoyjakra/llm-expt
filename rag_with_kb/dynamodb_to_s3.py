import boto3
import requests
import yaml
from botocore.exceptions import ClientError
from loguru import logger

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")


def download_pdfs_to_s3() -> None:
    """For each entry of the DynamoDB table, download the PDF and save in S3."""
    # Read the S3 bucket name from infra.yaml
    with open("infra.yaml", "r") as f:
        infra_config = yaml.safe_load(f)

    logger.debug(infra_config)

    kb_bucket = infra_config["kb_bucket"]
    db_name = infra_config["master_collection_dynamodb"]

    table = dynamodb.Table(db_name)

    # Scan the DynamoDB table
    # response = table.scan()
    response = table.scan(Limit=5)

    logger.info(f"Found {len(response['Items'])} items in the DynamoDB table.")
    logger.info(f"Downloading PDFs to S3 bucket: {kb_bucket}")

    # Process each item in the table
    for item in response["Items"]:
        # Download the PDF
        pdf_url = item["URL"]
        paper_key = f"{pdf_url.split('/')[-1]}.pdf"

        # Check if the paper exists in the S3 bucket
        # paper_key = f"{item['EntryId']}.pdf"
        try:
            s3.head_object(Bucket=kb_bucket, Key=paper_key)
            logger.debug(f"Paper {paper_key} already exists in the S3 bucket.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # The paper does not exist in the S3 bucket, so save it
                pdf_response = requests.get(pdf_url)
                pdf_content = pdf_response.content
                s3.put_object(Bucket=kb_bucket, Key=paper_key, Body=pdf_content)
                logger.info(f"Saved paper {paper_key} to the S3 bucket.")
            else:
                # Something else went wrong
                raise


if __name__ == "__main__":
    download_pdfs_to_s3()
