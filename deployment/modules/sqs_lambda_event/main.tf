resource "aws_lambda_event_source_mapping" "lambda_event_mapping" {
  event_source_arn  = var.sqs_queue_arn
  function_name     = var.lambda_arn

  tags = {
    env = var.app-env
  }
}