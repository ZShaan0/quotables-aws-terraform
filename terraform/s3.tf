resource "aws_s3_bucket" "data_bucket" {
  bucket_prefix = var.data_bucket_prefix
  tags = {
    name = "bucket_for_data"
  }
}

resource "aws_s3_bucket" "code_bucket" {
  bucket_prefix = var.code_bucket_prefix
  tags = {
    name = "bucket_for_code"
  }
}

resource "aws_s3_object" "lambda_code" {
  bucket     = aws_s3_bucket.code_bucket.bucket
  key        = "quote_handler/function.zip"
  source     = data.archive_file.lambda.output_path
  depends_on = [data.archive_file.lambda]
}

resource "aws_s3_object" "layer_code" {
  bucket     = aws_s3_bucket.code_bucket.bucket
  key        = "layer/layer.zip"
  source     = data.archive_file.layer.output_path
  depends_on = [data.archive_file.layer]
}
