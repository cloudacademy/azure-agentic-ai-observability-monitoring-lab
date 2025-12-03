### Provider

provider "aws" {
  region = "us-west-2"
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

### Vars

# variable "default_tag" {
#   type    = string
#   default = "lab"
# }

### Data

# data "aws_vpc" "default" {
#   default = true
#   state   = "available"
# }

# data "aws_subnet" "subnet_a" {
#   vpc_id            = data.aws_vpc.default.id
#   availability_zone = "us-west-2a"
#   state             = "available"
# }

# data "aws_subnet" "subnet_b" {
#   vpc_id            = data.aws_vpc.default.id
#   availability_zone = "us-west-2b"
#   state             = "available"
# }

# data "aws_ami" "amazon_linux_2" {
#   most_recent = true
#   owners      = ["amazon"]
#   filter {
#     name   = "name"
#     values = ["amzn2-ami-hvm*"]
#   }
# }

### Resources

resource "aws_iam_access_key" "student" {
  user   = "student"
  status = "Active"
}

### Outputs

output "student_access_key_id" { value = aws_iam_access_key.student.id }
output "student_secret_access_key_id" { value = aws_iam_access_key.student.secret }
output "userdatastudent_access_key_id" { value = aws_iam_access_key.student.id }
output "userdatastudent_secret_access_key_id" { value = aws_iam_access_key.student.secret }
