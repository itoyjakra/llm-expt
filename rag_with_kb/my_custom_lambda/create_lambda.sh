aws lambda create-function --function-name my_lambda_function \
	--runtime python3.11 \
	--role arn:aws:iam::130807196705:role/lambda_exec_role \
	--handler daily_scraper.lambda_handler \
	--zip-file fileb://function.zip

