resource "aws_s3_bucket" "s3_bucket" {
  bucket = "${var.app-env}-${var.bucket_name}"
  tags = {
    env = var.app-env
  }
}