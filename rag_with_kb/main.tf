
provider "aws" {
  region = "us-east-1"
}

data "external" "dynamodb_table_name" {
  program = ["python", "${path.module}/read_yaml.py"]
}

resource "aws_dynamodb_table" "arxiv_papers_master_collection" {
  name         = data.external.dynamodb_table_name.result["table_name"]
  billing_mode = "PAY_PER_REQUEST" # Use on-demand capacity mode
  hash_key     = "EntryId"

  attribute {
    name = "EntryId"
    type = "S" # String
  }

  tags = {
    Name        = "ArxivPapersMasterCollection"
    Environment = "Production"
  }
}
