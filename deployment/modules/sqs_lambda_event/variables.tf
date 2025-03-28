variable "sqs_queue_arn" {
  description = "The ARN of the SQS queue"
  type        = string
}

variable "lambda_arn" {
  description = "The ARN of the Lambda Function"
  type        = string
}

variable "app-env" {
    type = string
}