
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
  runtime       = var.runtime
  role          = aws_iam_role.lambda_exec.arn

  source_code_hash = filebase64sha256(data.archive_file.ddb_to_s3_lambda_zip.output_path)

  environment {
    variables = {
      KB_BUCKET = data.external.read_params.result["kb_bucket"]
      DB_NAME   = data.external.read_params.result["ddb_id"]
    }
  }
  timeout = var.lambda_timeout
}

resource "null_resource" "install_python_dependencies" {
  provisioner "local-exec" {
    command = "bash ${path.module}/scripts/create_lambda_archive.sh"

    environment = {
      source_code_path = var.path_source_code
      function_name    = var.lambda_scraper_function_name
      path_module      = path.module
      runtime          = var.runtime
      path_cwd         = path.cwd
    }
  }
}

data "archive_file" "create_dist_pkg" {
  depends_on  = [null_resource.install_python_dependencies]
  source_dir  = "${path.cwd}/lambda_dist_pkg/"
  output_path = "${path.module}/scraper_lambda_function_payload.zip"
  type        = "zip"
}

# resource "aws_lambda_function" "paper_scraper_lambda" {
#   function_name = var.lambda_scraper_function_name
#   description   = "Scrapes arxiv papers between two dates"
#   handler       = "lambda_handler"
#   runtime       = var.runtime
#   role          = aws_iam_role.lambda_exec.arn
#   timeout       = var.lambda_timeout

#   depends_on       = [null_resource.install_python_dependencies]
#   source_code_hash = data.archive_file.create_dist_pkg.output_base64sha256
#   filename         = data.archive_file.create_dist_pkg.output_path
# }

# data "aws_lambda_layer_version" "aws_pandas_layer" {
#   layer_name = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:10"
#   version    = 10
# }

resource "aws_lambda_function" "paper_scraper_lambda" {
  function_name = var.lambda_scraper_function_name
  description   = "Scrapes arxiv papers between two dates"
  handler       = "daily_scraper.lambda_handler"
  runtime       = var.runtime
  role          = aws_iam_role.lambda_exec.arn
  timeout       = var.lambda_timeout

  filename         = "my_custom_lambda/function.zip"
  source_code_hash = filebase64sha256("my_custom_lambda/function.zip")

  layers = [
    "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:10"
  ]
  # aws_lambda_layer_version.aws_pandas_layer.arn
}
#TODO need to attach the correct set of policies
resource "aws_lambda_function" "refresh_knowledge_base_lambda" {
  filename      = data.archive_file.refresh_kb_zip.output_path
  function_name = "refresh_knowledge_base"
  handler       = "refresh_knowledge_base.lambda_handler"
  runtime       = var.runtime
  role          = aws_iam_role.lambda_exec.arn

  source_code_hash = filebase64sha256(data.archive_file.refresh_kb_zip.output_path)

  environment {
    variables = {
      KB_ID = data.external.read_params.result["kb_id"]
      DS_ID = data.external.read_params.result["ds_id"]
    }
  }
  timeout = var.lambda_timeout
}



resource "aws_sfn_state_machine" "arxiv_paper_workflow" {
  name     = "ArxivPaperWorkflow"
  role_arn = aws_iam_role.step_function_execution_role.arn

  definition = jsonencode({
    Comment = "A state machine that runs the paper scraping, PDF downloading, and knowledge base refreshing workflow."
    StartAt = "PaperScraper"
    States = {
      PaperScraper = {
        Type     = "Task"
        Resource = aws_lambda_function.paper_scraper_lambda.arn
        Next     = "DownloadPDFsToS3"
        Parameters = {
          "topic"       = var.topic
          "db_name"     = var.db_name
          "max_results" = var.max_results
        }
      }
      DownloadPDFsToS3 = {
        Type     = "Task"
        Resource = aws_lambda_function.download_pdfs_to_s3_lambda.arn
        Next     = "RefreshKnowledgeBase"
      }
      RefreshKnowledgeBase = {
        Type     = "Task"
        Resource = aws_lambda_function.refresh_knowledge_base_lambda.arn
        End      = true
      }
    }
  })
}


resource "aws_cloudwatch_event_rule" "daily_execution_rule" {
  name                = "DailyArxivPaperScraper"
  schedule_expression = "cron(0 2 * * ? *)"
}

resource "aws_cloudwatch_event_target" "step_function_target" {
  rule      = aws_cloudwatch_event_rule.daily_execution_rule.name
  target_id = "StepFunctionTarget"
  arn       = aws_sfn_state_machine.arxiv_paper_workflow.arn
  role_arn  = aws_iam_role.step_function_execution_role.arn
}

resource "aws_iam_policy" "invoke_step_function_policy" {
  name        = "InvokeStepFunctionPolicy"
  description = "Policy to allow invoking a Step Functions state machine"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "states:StartExecution"
        Effect   = "Allow"
        Resource = aws_sfn_state_machine.arxiv_paper_workflow.arn
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_invoke_step_function_policy" {
  role       = aws_iam_role.step_function_execution_role.name
  policy_arn = aws_iam_policy.invoke_step_function_policy.arn
}
