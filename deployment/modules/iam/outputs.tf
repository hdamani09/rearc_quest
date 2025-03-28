output "iam_role_arn" {
  description = "The ARN of the IAM Role"
  value       = aws_iam_role.iam_role.arn
}

output "iam_role_id" {
  description = "The ID of the IAM Role"
  value       = aws_iam_role.iam_role.id
}