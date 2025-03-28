data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = var.identifiers
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_role" {
  name               = "${var.app-env}-${var.role_name}"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = {
    env = var.app-env
  }
}