"""Create necessary infrastructure for the RAG solution."""

import json
import time

import boto3
import botocore
import yaml
from loguru import logger
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection

from utility import (
    create_bedrock_execution_role,
    create_oss_policy_attach_bedrock_execution_role,
    create_policies_in_oss,
)

region = "us-east-1"
s3_client = boto3.client("s3")
bedrock_client = boto3.client("bedrock-agent")
boto3_session = boto3.session.Session()
aoss_client = boto3_session.client("opensearchserverless")


def create_knowledge_base(**kwargs):
    """Create a Bedrock knowledge base."""
    logger.info("Creating knowledge base...")

    create_kb_response = bedrock_client.create_knowledge_base(
        name=kwargs["kb_name"],
        description=kwargs["kb_desc"],
        roleArn=kwargs["role_arn"],
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": kwargs["embed_model_arn"],
            },
        },
        storageConfiguration={
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": kwargs["oss_config"],
        },
    )

    return create_kb_response["knowledgeBase"]


def create_kb_bucket(bucket_name: str) -> None:
    """Create a bucket for the knowledge base if it does not already exist."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"Bucket {bucket_name} already exists, skipping...")
    except botocore.exceptions.ClientError:
        response = s3_client.create_bucket(Bucket=bucket_name)
        logger.debug(response)


def get_json_body():
    return {
        "settings": {
            "index.knn": "true",
            "number_of_shards": 1,
            "knn.algo_param.ef_search": 512,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "engine": "nmslib",
                        "space_type": "cosinesimil",
                        "parameters": {"ef_construction": 512, "m": 16},
                    },
                },
                "text": {"type": "text"},
                "text-metadata": {"type": "text"},
            }
        },
    }


def get_opensearch_client():
    service = "aoss"
    credentials = boto3.Session().get_credentials()
    awsauth = auth = AWSV4SignerAuth(credentials, region, service)
    return OpenSearch(
        hosts=[{"host": host, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300,
    )


def create_opensearch_index(oss_client, body_json, index_name):
    # Create index
    logger.info("Creating index...")
    response = oss_client.indices.create(index=index_name, body=json.dumps(body_json))
    logger.info(response)
    time.sleep(60)  # index creation can take up to a minute


def get_oss_config(vector_index: str, collection) -> dict:
    logger.debug(f"Creating OpenSearch config for index {vector_index}")
    return {
        "collectionArn": collection["createCollectionDetail"]["arn"],
        "vectorIndexName": vector_index,
        "fieldMapping": {
            "vectorField": "vector",
            "textField": "text",
            "metadataField": "text-metadata",
        },
    }


def get_chunking_config(**kwargs) -> dict:
    return {
        "chunkingStrategy": kwargs["strategy"],
        "fixedSizeChunkingConfiguration": {
            "maxTokens": kwargs["max_tokens"],
            "overlapPercentage": kwargs["overlap_percentage"],
        },
    }


if __name__ == "__main__":
    with open("infra.yaml", "r") as f:
        infra_config = yaml.safe_load(f)

    logger.debug(infra_config)

    # create the bucket to store the pdf of the papers
    create_kb_bucket(infra_config["kb_bucket"])

    # create the collection
    vector_store_name = infra_config["vector_store"]["name"]

    bedrock_kb_execution_role = create_bedrock_execution_role(
        bucket_name=infra_config["kb_bucket"]
    )
    bedrock_kb_execution_role_arn = bedrock_kb_execution_role["Role"]["Arn"]

    encryption_policy, network_policy, access_policy = create_policies_in_oss(
        vector_store_name=vector_store_name,
        aoss_client=aoss_client,
        bedrock_kb_execution_role_arn=bedrock_kb_execution_role_arn,
    )
    collection = aoss_client.create_collection(
        name=vector_store_name, type="VECTORSEARCH"
    )
    logger.debug(type(collection))
    collection_id = collection["createCollectionDetail"]["id"]
    host = collection_id + "." + region + ".aoss.amazonaws.com"
    logger.debug(f"{host=}")

    # wait for collection creation
    response = aoss_client.batch_get_collection(names=[vector_store_name])
    # Periodically check collection status
    while (response["collectionDetails"][0]["status"]) == "CREATING":
        logger.debug("Creating collection...")
        time.sleep(30)
        response = aoss_client.batch_get_collection(names=[vector_store_name])
    logger.debug("\nCollection successfully created:")
    logger.debug(response["collectionDetails"])

    # create oss policy and attach it to Bedrock execution role
    response = create_oss_policy_attach_bedrock_execution_role(
        collection_id=collection_id, bedrock_kb_execution_role=bedrock_kb_execution_role
    )
    logger.debug(response)

    # create opensearch configuration
    oss_config = get_oss_config(
        vector_index=infra_config["vector_index"]["name"], collection=collection
    )

    # create chunking configuration
    chunk_config = get_chunking_config(
        strategy=infra_config["chunking_strategy"]["type"],
        max_tokens=infra_config["chunking_strategy"]["max_tokens"],
        overlap_percentage=infra_config["chunking_strategy"]["overlap_percentage"],
    )

    # create the knowledge base
    embed_model = infra_config["embed_model"]["name"]
    embed_model_categoty = infra_config["embed_model"]["category"]
    embed_model_arn = f"arn:aws:bedrock:{region}::{embed_model_categoty}/{embed_model}"

    response = create_knowledge_base(
        kb_name=infra_config["kb_name"],
        kb_desc=infra_config["kb_description"],
        role_arn=bedrock_kb_execution_role_arn,
        embed_model_arn=embed_model_arn,
        oss_config=oss_config,
    )

    logger.debug(response)
