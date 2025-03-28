resource "aws_sqs_queue_policy" "s3_event_queue_policy" {
  queue_url = var.sqs_queue_url
  policy    = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "s3.amazonaws.com" },
      "Action": "SQS:SendMessage",
      "Resource": "${var.sqs_queue_arn}",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "${var.s3_bucket_arn}"
        }
      }
    }
  ]
}
EOF
}