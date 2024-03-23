"""Bunch of utility functions required to create Bedrokc Knowledge Base"""

"""https://github.com/aws-samples/amazon-bedrock-workshop/blob/main/02_KnowledgeBases_and_RAG/utility.py"""

import json
import random

import boto3
from loguru import logger

suffix = random.randrange(200, 900)
boto3_session = boto3.session.Session()
region_name = boto3_session.region_name
iam_client = boto3_session.client("iam")
account_number = boto3.client("sts").get_caller_identity().get("Account")
identity = boto3.client("sts").get_caller_identity()["Arn"]

# encryption_policy_name = f"bedrock-sample-rag-sp-{suffix}"
# network_policy_name = f"bedrock-sample-rag-np-{suffix}"
# access_policy_name = f"bedrock-sample-rag-ap-{suffix}"
# bedrock_execution_role_name = f"AmazonBedrockExecutionRoleForKnowledgeBase_{suffix}"
# fm_policy_name = f"AmazonBedrockFoundationModelPolicyForKnowledgeBase_{suffix}"
# s3_policy_name = f"AmazonBedrockS3PolicyForKnowledgeBase_{suffix}"
# oss_policy_name = f"AmazonBedrockOSSPolicyForKnowledgeBase_{suffix}"


def create_bedrock_execution_role(
    bucket_name, fm_policy_name, s3_policy_name, bedrock_execution_role_name
):
    foundation_model_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                ],
                "Resource": [
                    f"arn:aws:bedrock:{region_name}::foundation-model/amazon.titan-embed-text-v1",
                    f"arn:aws:bedrock:{region_name}::foundation-model/cohere.embed-english-v3",
                    f"arn:aws:bedrock:{region_name}::foundation-model/cohere.embed-multilingual-v3",
                ],
            }
        ],
    }

    s3_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*",
                ],
                "Condition": {
                    "StringEquals": {"aws:ResourceAccount": f"{account_number}"}
                },
            }
        ],
    }

    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    # create policies based on the policy documents
    try:
        fm_policy = iam_client.create_policy(
            PolicyName=fm_policy_name,
            PolicyDocument=json.dumps(foundation_model_policy_document),
            Description="Policy for accessing foundation model",
        )
    except iam_client.exceptions.EntityAlreadyExistsException as e:
        logger.error(f"Foundation model policy already exists: {e}")
        fm_policy = iam_client.get_policy(
            PolicyArn=f"arn:aws:iam::{account_number}:policy/{fm_policy_name}"
        )
        logger.debug(f"Foundation model policy: {fm_policy}")

    try:
        s3_policy = iam_client.create_policy(
            PolicyName=s3_policy_name,
            PolicyDocument=json.dumps(s3_policy_document),
            Description="Policy for reading documents from s3",
        )
    except iam_client.exceptions.EntityAlreadyExistsException as e:
        logger.error(f"S3 policy already exists: {e}")
        s3_policy = iam_client.get_policy(
            PolicyArn=f"arn:aws:iam::{account_number}:policy/{s3_policy_name}"
        )
        logger.debug(f"S3 policy: {s3_policy}")

    # create bedrock execution role
    try:
        bedrock_kb_execution_role = iam_client.create_role(
            RoleName=bedrock_execution_role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
            Description="Amazon Bedrock Knowledge Base Execution Role for accessing OSS and S3",
            MaxSessionDuration=3600,
        )
    except iam_client.exceptions.EntityAlreadyExistsException as e:
        logger.error(f"Bedrock execution role already exists: {e}")
        bedrock_kb_execution_role = iam_client.get_role(
            RoleName=bedrock_execution_role_name
        )
        logger.debug(f"Bedrock execution role: {bedrock_kb_execution_role}")

    # fetch arn of the policies and role created above
    bedrock_kb_execution_role_arn = bedrock_kb_execution_role["Role"]["Arn"]
    s3_policy_arn = s3_policy["Policy"]["Arn"]
    fm_policy_arn = fm_policy["Policy"]["Arn"]

    # attach policies to Amazon Bedrock execution role
    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"], PolicyArn=fm_policy_arn
    )
    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"], PolicyArn=s3_policy_arn
    )
    return bedrock_kb_execution_role


def create_oss_policy_attach_bedrock_execution_role(
    collection_id, bedrock_kb_execution_role, oss_policy_name
):
    # define oss policy document
    oss_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["aoss:APIAccessAll"],
                "Resource": [
                    f"arn:aws:aoss:{region_name}:{account_number}:collection/{collection_id}"
                ],
            }
        ],
    }

    try:
        oss_policy = iam_client.create_policy(
            PolicyName=oss_policy_name,
            PolicyDocument=json.dumps(oss_policy_document),
            Description="Policy for accessing opensearch serverless",
        )
    except iam_client.exceptions.EntityAlreadyExistsException as e:
        logger.error(f"OSS policy already exists: {e}")
        oss_policy = iam_client.get_policy(
            PolicyArn=f"arn:aws:iam::{account_number}:policy/{oss_policy_name}"
        )
        logger.debug(f"OSS policy: {oss_policy}")

    oss_policy_arn = oss_policy["Policy"]["Arn"]
    logger.debug("Opensearch serverless arn: ", oss_policy_arn)

    iam_client.attach_role_policy(
        RoleName=bedrock_kb_execution_role["Role"]["RoleName"], PolicyArn=oss_policy_arn
    )
    return None


def create_policies_in_oss(
    vector_store_name,
    aoss_client,
    bedrock_kb_execution_role_arn,
    encryption_policy_name,
    network_policy_name,
    access_policy_name,
):
    try:
        encryption_policy = aoss_client.create_security_policy(
            name=encryption_policy_name,
            policy=json.dumps(
                {
                    "Rules": [
                        {
                            "Resource": ["collection/" + vector_store_name],
                            "ResourceType": "collection",
                        }
                    ],
                    "AWSOwnedKey": True,
                }
            ),
            type="encryption",
        )
    except aoss_client.exceptions.ConflictException as e:
        logger.error(f"Encryption policy already exists: {e}")
        encryption_policy = aoss_client.get_security_policy(
            name=encryption_policy_name, type="encryption"
        )
        logger.debug(f"Encryption policy: {encryption_policy}")

    try:
        network_policy = aoss_client.create_security_policy(
            name=network_policy_name,
            policy=json.dumps(
                [
                    {
                        "Rules": [
                            {
                                "Resource": ["collection/" + vector_store_name],
                                "ResourceType": "collection",
                            }
                        ],
                        "AllowFromPublic": True,
                    }
                ]
            ),
            type="network",
        )
    except aoss_client.exceptions.ConflictException as e:
        logger.error(f"Network policy already exists: {e}")
        network_policy = aoss_client.get_security_policy(
            name=network_policy_name, type="network"
        )
        logger.debug(f"Network policy: {network_policy}")

    try:
        access_policy = aoss_client.create_access_policy(
            name=access_policy_name,
            policy=json.dumps(
                [
                    {
                        "Rules": [
                            {
                                "Resource": ["collection/" + vector_store_name],
                                "Permission": [
                                    "aoss:CreateCollectionItems",
                                    "aoss:DeleteCollectionItems",
                                    "aoss:UpdateCollectionItems",
                                    "aoss:DescribeCollectionItems",
                                ],
                                "ResourceType": "collection",
                            },
                            {
                                "Resource": ["index/" + vector_store_name + "/*"],
                                "Permission": [
                                    "aoss:CreateIndex",
                                    "aoss:DeleteIndex",
                                    "aoss:UpdateIndex",
                                    "aoss:DescribeIndex",
                                    "aoss:ReadDocument",
                                    "aoss:WriteDocument",
                                ],
                                "ResourceType": "index",
                            },
                        ],
                        "Principal": [identity, bedrock_kb_execution_role_arn],
                        "Description": "Easy data policy",
                    }
                ]
            ),
            type="data",
        )
    except aoss_client.exceptions.ConflictException as e:
        logger.error(f"Access policy already exists: {e}")
        access_policy = aoss_client.get_access_policy(
            name=access_policy_name, type="data"
        )
        logger.debug(f"Access policy: {access_policy}")

    return encryption_policy, network_policy, access_policy


def delete_iam_role_and_policies():
    fm_policy_arn = f"arn:aws:iam::{account_number}:policy/{fm_policy_name}"
    s3_policy_arn = f"arn:aws:iam::{account_number}:policy/{s3_policy_name}"
    oss_policy_arn = f"arn:aws:iam::{account_number}:policy/{oss_policy_name}"
    iam_client.detach_role_policy(
        RoleName=bedrock_execution_role_name, PolicyArn=s3_policy_arn
    )
    iam_client.detach_role_policy(
        RoleName=bedrock_execution_role_name, PolicyArn=fm_policy_arn
    )
    iam_client.detach_role_policy(
        RoleName=bedrock_execution_role_name, PolicyArn=oss_policy_arn
    )
    iam_client.delete_role(RoleName=bedrock_execution_role_name)
    iam_client.delete_policy(PolicyArn=s3_policy_arn)
    iam_client.delete_policy(PolicyArn=fm_policy_arn)
    iam_client.delete_policy(PolicyArn=oss_policy_arn)
    return 0
