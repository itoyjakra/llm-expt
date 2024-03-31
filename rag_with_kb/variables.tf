variable "runtime" {
  default = "python3.11"
}

variable "path_source_code" {
  default = "lambda_functions"
}

variable "lambda_scraper_function_name" {
  default = "paper_scraper"
}

variable "topic" {
  description = "The topic for the Arxiv paper"
  type        = string
  default     = "LLM"
}

variable "db_name" {
  description = "The DynamoDB table name for storing paper metadata"
  type        = string
  default     = "arxiv_papers_master_collection"
}

variable "max_results" {
  description = "The maximum number of Arxiv results to fetch"
  type        = number
  default     = 1000
}

variable "lambda_timeout" {
  description = "Timeout in seconds for lambda function"
  type        = number
  default     = 900
}
