variable "bucket_id" {
  description = "The ID of the S3 bucket where the file will be uploaded"
  type        = string
}

variable "bucket_key" {
  description = "The key (path) of the object in the S3 bucket"
  type        = string
}

variable "file_path" {
  description = "Local path to the file that will be uploaded to S3"
  type        = string
}