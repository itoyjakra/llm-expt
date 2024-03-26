import os
import time

import boto3
from botocore.exceptions import ClientError

region = "us-east-1"
bedrock_client = boto3.client("bedrock-agent")
boto3_session = boto3.session.Session()
bedrock_agent_client = boto3_session.client("bedrock-agent", region_name=region)


def lambda_handler(event, context):
    """Start an ingestion job for a given knowledge base and data source."""
    # Retrieve environment variables
    kb_id = os.environ["KB_ID"]
    ds_id = os.environ["DS_ID"]

    # Start the ingestion job
    try:
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=kb_id, dataSourceId=ds_id
        )
        job = response["ingestionJob"]
        print(f"Started ingestion job with ID: {job['ingestionJobId']}")

        # Optionally, wait for the job to complete
        while job["status"] != "COMPLETE":
            time.sleep(60)  # Wait for 60 seconds before checking the job status again
            get_job_response = bedrock_agent_client.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job["ingestionJobId"],
            )
            job = get_job_response["ingestionJob"]
            print(f"Ingestion job status: {job['status']}")

    except ClientError as e:
        print(f"Error starting ingestion job: {e}")
        raise

    return {
        "statusCode": 200,
        "body": f"Ingestion job started successfully with ID: {job['ingestionJobId']}",
    }
