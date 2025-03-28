output "queue_url" {
  description = "The URL of the SQS queue"
  value       = aws_sqs_queue.s3_event_queue.id
}

output "queue_arn" {
  description = "The ARN of the SQS queue"
  value       = aws_sqs_queue.s3_event_queue.arn
}