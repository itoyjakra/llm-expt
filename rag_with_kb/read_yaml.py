"""Simply reads the yaml file, required by terraform"""

import json

import yaml


def read_yaml_file(file_path):
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    return data.get("master_collection_dynamodb", "default_table_name")


if __name__ == "__main__":
    table_name = read_yaml_file("infra.yaml")
    print(json.dumps({"table_name": table_name}))
