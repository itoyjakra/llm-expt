
provider "aws" {
  region = "us-east-1"
}

data "external" "read_params" {
  program = ["python", "${path.module}/read_params.py"]
}

resource "aws_dynamodb_table" "arxiv_papers_master_collection" {
  name         = data.external.read_params.result["ddb_id"]
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

data "archive_file" "ddb_to_s3_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/dynamodb_to_s3.py"
  output_path = "${path.module}/lambda_functions/ddb_to_s3_lambda_function_payload.zip"
}

data "archive_file" "refresh_kb_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_functions/refresh_knowledge_base.py"
  output_path = "${path.module}/lambda_functions/refresh_kb_lambda_function_payload.zip"
}

resource "aws_lambda_function" "download_pdfs_to_s3_lambda" {
  filename      = data.archive_file.ddb_to_s3_lambda_zip.output_path
  function_name = "download_pdf_to_s3"
  handler       = "dynamodb_to_s3.lambda_handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn

  source_code_hash = filebase64sha256(data.archive_file.ddb_to_s3_lambda_zip.output_path)

  environment {
    variables = {
      KB_BUCKET = data.external.read_params.result["kb_bucket"]
      DB_NAME   = data.external.read_params.result["ddb_id"]
    }
  }
  timeout = 900 # Timeout in seconds
}

#TODO need to attach the correct set of policies
resource "aws_lambda_function" "refresh_knowledge_base_lambda" {
  filename      = data.archive_file.refresh_kb_zip.output_path
  function_name = "refresh_knowledge_base"
  handler       = "refresh_knowledge_base.lambda_handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_exec.arn

  source_code_hash = filebase64sha256(data.archive_file.refresh_kb_zip.output_path)

  environment {
    variables = {
      KB_ID = data.external.read_params.result["kb_id"]
      DS_ID = data.external.read_params.result["ds_id"]
    }
  }
  timeout = 900 # Timeout in seconds
}

resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_exec_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_s3_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}
