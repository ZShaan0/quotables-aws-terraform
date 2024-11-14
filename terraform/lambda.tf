data "archive_file" "lambda" {
  type             = "zip"
  output_file_mode = "0666"
  source_file      = "${path.module}/../src/quotes.py"
  output_path      = "${path.module}/../function.zip"
}

data "archive_file" "layer" {
  type             = "zip"
  output_file_mode = "0666"
  source_dir       = "${path.module}/../layer"
  output_path      = "${path.module}/../layer.zip"
}

resource "aws_lambda_layer_version" "requests_layer" {
  layer_name          = "requests_layer"
  compatible_runtimes = [var.python_runtime]
  s3_bucket           = aws_s3_bucket.code_bucket.bucket
  s3_key              = "layer/layer.zip"
  depends_on          = [aws_s3_object.layer_code]
}

resource "aws_lambda_function" "quote_handler" {
  function_name = "quote_handler"
  handler       = "quotes.lambda_handler"
  runtime       = var.python_runtime
  s3_bucket     = aws_s3_bucket.code_bucket.bucket
  s3_key        = "quote_handler/function.zip"
  timeout       = 10
  role          = aws_iam_role.lambda_role.arn
  layers        = [aws_lambda_layer_version.requests_layer.arn]
  depends_on    = [aws_s3_object.lambda_code]

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.data_bucket.bucket
    }
  }
}
