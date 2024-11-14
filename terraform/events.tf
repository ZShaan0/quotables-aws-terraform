resource "aws_cloudwatch_event_rule" "quotes_scheduler" {
  name                = "quotes_scheduler"
  description         = "runs lambda quote handler every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "scheduler_target" {
  rule      = aws_cloudwatch_event_rule.quotes_scheduler.name
  arn       = aws_lambda_function.quote_handler.arn
  target_id = "quote_handler_target"
}

resource "aws_lambda_permission" "allow_cloudwatch_events" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.quote_handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.quotes_scheduler.arn
}

resource "aws_cloudwatch_log_metric_filter" "great_quote_filter" {
  name           = "great_quote_count"
  log_group_name = "/aws/lambda/${var.lambda_name}"
  pattern = "GREAT QUOTE"

  metric_transformation {
    name      = "great_quote_count"
    namespace = "great_quotes"
    value     = "1"
  }
}

resource "aws_sns_topic" "great_quote_topic" {
  name = "great-quote-emails"
}

data "aws_iam_policy_document" "great_quotes_policy_doc" {
  statement {
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
    resources = [aws_sns_topic.great_quote_topic.arn]
  }
}

resource "aws_sns_topic_policy" "great_quotes_policy" {
  arn    = aws_sns_topic.great_quote_topic.arn
  policy = data.aws_iam_policy_document.great_quotes_policy_doc.json
}

resource "aws_sns_topic_subscription" "great_quotes_email_subscription" {
  topic_arn = aws_sns_topic.great_quote_topic.arn
  protocol  = "email"
  endpoint  = var.email_endpoint
}

resource "aws_cloudwatch_metric_alarm" "great_quote_alarm" {
  alarm_name          = "great_quote_alarm"
  metric_name         = aws_cloudwatch_log_metric_filter.great_quote_filter.name
  threshold           = 0
  statistic           = "Sum"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  period              = "60"
  namespace           = "great_quotes"
  alarm_description   = "Triggers when a GREAT QUOTE is logged"
  alarm_actions       = [aws_sns_topic.great_quote_topic.arn]

}
