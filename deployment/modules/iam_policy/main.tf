resource "aws_iam_role_policy" "iam_role_policy" {
  name = "${var.app-env}_${var.policy_name}_policy"
  role = var.iam_role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = var.action
        Effect   = var.effect
        Resource = var.resource
      }
    ]
  })
}