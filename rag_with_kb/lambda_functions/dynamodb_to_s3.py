import os
from urllib.request import urlopen

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")


def lambda_handler(event, context):
    """For each entry of the DynamoDB table, download the PDF and save in S3."""
    # Use environment variables for configuration
    kb_bucket = os.environ["KB_BUCKET"]
    db_name = os.environ["DB_NAME"]

    table = dynamodb.Table(db_name)

    # Scan the DynamoDB table
    response = table.scan(Limit=100)

    print(f"Found {len(response['Items'])} items in the DynamoDB table.")
    print(f"Downloading PDFs to S3 bucket: {kb_bucket}")

    # Process each item in the table
    for item in response["Items"]:
        # Download the PDF
        pdf_url = item["URL"]
        paper_key = f"{pdf_url.split('/')[-1]}.pdf"

        # Check if the paper exists in the S3 bucket
        try:
            s3.head_object(Bucket=kb_bucket, Key=paper_key)
            print(f"Paper {paper_key} already exists in the S3 bucket.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # The paper does not exist in the S3 bucket, so save it
                with urlopen(pdf_url) as response, open(
                    f"/tmp/{paper_key}", "wb"
                ) as out_file:
                    data = response.read()
                    out_file.write(data)
                # Upload the PDF to S3
                with open(f"/tmp/{paper_key}", "rb") as data:
                    s3.put_object(Bucket=kb_bucket, Key=paper_key, Body=data)
                print(f"Saved paper {paper_key} to the S3 bucket.")
            else:
                # Something else went wrong
                raise
