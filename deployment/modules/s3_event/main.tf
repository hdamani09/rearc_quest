resource "aws_s3_bucket_notification" "s3_bucket_notification" {
    bucket = var.s3_bucket_id
    queue {
        queue_arn = var.sqs_queue_arn
        events = ["s3:ObjectCreated:*", "s3:ObjectCreated:*"]
        filter_prefix = var.s3_prefix
    }
}