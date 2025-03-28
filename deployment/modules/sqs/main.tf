resource "aws_sqs_queue" "s3_event_queue" {
  name                      = "${var.app-env}-${var.queue_name}"
  delay_seconds             = 10
  visibility_timeout_seconds = 150
  
  tags = {
    env = var.app-env
  }
}