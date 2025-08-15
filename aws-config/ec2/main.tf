terraform {
  required_providers {
    aws = {
        source = "hashicorp/aws"
        version ="5.54.1"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
    region = "us-east-1"
}

# Create a key pair for EC2 instance
resource "aws_key_pair" "EchoMail_key" {
  key_name   = "EchoMail-keypair"
  public_key = tls_private_key.EchoMail_private_key.public_key_openssh
}

# Generate a private key
resource "tls_private_key" "EchoMail_private_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Save the private key to a local file
resource "local_file" "EchoMail_pem" {
  content         = tls_private_key.EchoMail_private_key.private_key_pem
  filename        = "${path.module}/EchoMail-keypair.pem"
  file_permission = "0400"  # Unix-style permissions (read-only for owner)
}

# EC2 Instance for EchoMail Flask Application
resource "aws_instance" "EchoMail-1" {
  ami           = "ami-020cba7c55df1f615"  # Amazon Linux 2
  instance_type = "t2.micro"
  key_name      = aws_key_pair.EchoMail_key.key_name
  vpc_security_group_ids = [aws_security_group.EchoMail.id]
  subnet_id              = aws_subnet.main.id

  tags = {
    Name = "EchoMail-Flask-App"
  }
}

# Output the public IP of the instance
output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.EchoMail-1.public_ip
}

# Output the SSH connection command
output "ssh_connection_command" {
  description = "Command to SSH into the instance"
  value       = "ssh -i EchoMail-keypair.pem ec2-user@${aws_instance.EchoMail-1.public_ip}"
}