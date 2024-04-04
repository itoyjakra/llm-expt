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

    documents_scanned = 0
    documents_saved = 0
    last_evaluated_key = None

    while True:
        # Scan the DynamoDB table with pagination
        if last_evaluated_key:
            response = table.scan(ExclusiveStartKey=last_evaluated_key)
        else:
            response = table.scan()

        print(f"Found {len(response['Items'])} items in the DynamoDB table.")
        print(f"Downloading PDFs to S3 bucket: {kb_bucket}")

        for item in response["Items"]:
            documents_scanned += 1
            # Download the PDF
            pdf_url = item["URL"]
            paper_key = f"{pdf_url.split('/')[-1]}.pdf"

            try:
                s3.head_object(Bucket=kb_bucket, Key=paper_key)
                print(f"Paper {paper_key} already exists in the S3 bucket.")
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    with urlopen(pdf_url) as response:
                        s3.put_object(
                            Bucket=kb_bucket, Key=paper_key, Body=response.read()
                        )
                    print(f"Saved paper {paper_key} to the S3 bucket.")
                    documents_saved += 1
                else:
                    # Something else went wrong
                    raise

        # Check if there are more items to scan
        if "LastEvaluatedKey" in response:
            last_evaluated_key = response["LastEvaluatedKey"]
        else:
            break

    print(f"Total documents saved to S3: {documents_saved}")
    print(f"Total documents scanned from DynamoDB : {documents_scanned}")
