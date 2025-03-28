resource "aws_cloudwatch_event_rule" "daily_lambda_trigger" {
  name                = "${var.app-env}-${var.lambda_function_name}-daily-trigger"
  description         = "Triggers Lambda function daily"
  schedule_expression = var.schedule_cron

  tags = {
    env = var.app-env
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_lambda_trigger.name
  target_id = "LambdaFunction"
  arn       = var.lambda_function_arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_lambda_trigger.arn
}