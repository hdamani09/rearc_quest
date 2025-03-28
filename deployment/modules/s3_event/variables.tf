variable "sqs_queue_arn" {
  description = "The ARN of the SQS queue"
  type        = string
}

variable "s3_bucket_id" {
  description = "The ID of the S3 bucket sending notifications"
  type        = string
}

variable "s3_prefix" {
  description = "The specific S3 prefix to track for notification"
  type        = string
}