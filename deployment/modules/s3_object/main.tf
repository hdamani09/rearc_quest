resource "aws_s3_object" "file" {
  bucket = var.bucket_id
  key    = var.bucket_key
  source = var.file_path

  etag = filemd5(var.file_path)
}