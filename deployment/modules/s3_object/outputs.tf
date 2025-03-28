output "s3_uri" {
  description = "Full S3 URI of the uploaded object"
  value       = "s3://${var.bucket_id}/${var.bucket_key}"
}

output "object_key" {
  description = "The key of the uploaded object in the S3 bucket"
  value       = var.bucket_key
}