variable "iam_role_id" {
    type = string
}

variable "policy_name" {
    type = string
}

variable "action" {
    type = list(string)
}

variable "effect" {
    type = string
}

variable "resource" {
    type = string
}

variable "app-env" {
    type = string
}