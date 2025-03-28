output "lambda_arn" {
  description = "The ARN of the Lambda Function"
  value       = aws_lambda_function.lambda_function.arn
}

output "lambda_function_name" {
  description = "The Lambda Function Name"
  value       = aws_lambda_function.lambda_function.function_name
}