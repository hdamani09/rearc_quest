resource "aws_s3_bucket_public_access_block" "allow_public" {
  bucket = var.s3_bucket_id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# resource "aws_s3_bucket_policy" "public_access" {
#   depends_on = [aws_s3_bucket_public_access_block.allow_public]
#   bucket = var.s3_bucket_id
#   policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Sid       = "PublicReadForSpecificPrefix",
#         Effect    = "Allow",
#         Principal = "*",
#         Action    = "s3:GetObject",
#         Resource  = "${var.s3_bucket_arn}/${var.s3_prefix}"
#       },
#       {
#         Sid       = "PublicListForSpecificPrefix",
#         Effect    = "Allow",
#         Principal = "*",
#         Action    = "s3:ListBucket",
#         Resource  = "${var.s3_bucket_arn}",
#         Condition = {
#           "StringLike": {
#             "s3:prefix": "${var.s3_prefix}"
#           }
#         }
#       }
#     ]
#   })
# }