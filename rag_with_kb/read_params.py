"""Reading parameters from the yaml file for terraform to consume."""

import json

import boto3
import yaml

client = boto3.client("bedrock-agent")


def get_kb_id_from_name(kb_name: str) -> str | None:
    """Returns the ID of the Knowledge Base from its name"""
    response = client.list_knowledge_bases(
        maxResults=123,
    )
    for item in response["knowledgeBaseSummaries"]:
        if item["name"] == kb_name:
            return item["knowledgeBaseId"]

    return None


def get_ds_id_from_kb_id(kb_id: str) -> str | None:
    """Returns the ID of the Dataset from Knowledge Base name"""
    response = client.list_data_sources(knowledgeBaseId=kb_id)

    # TODO need to handle multiple data sources if present
    for item in response["dataSourceSummaries"]:
        return item["dataSourceId"]

    return None


def main():
    """prints all the parameters required by Terraform"""
    with open("infra.yaml", "r") as f:
        infra_config = yaml.safe_load(f)

    kb_bucket = infra_config["kb_bucket"]
    kb_id = get_kb_id_from_name(kb_name=infra_config["kb_name"])
    if kb_id is None:
        raise Exception(f"No Knowledge Base with name: {infra_config['kb_name']} found")
    ds_id = get_ds_id_from_kb_id(kb_id=kb_id)
    ddb_id = infra_config["master_collection_dynamodb"]

    print(
        json.dumps(
            {
                "kb_bucket": f"{kb_bucket}",
                "kb_id": f"{kb_id}",
                "ddb_id": f"{ddb_id}",
                "ds_id": f"{ds_id}",
            }
        )
    )


if __name__ == "__main__":
    main()
