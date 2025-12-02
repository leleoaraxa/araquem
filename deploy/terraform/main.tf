terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # TODO: configurar backend remoto (S3 + DynamoDB) se quiser
}

provider "aws" {
  region = var.aws_region
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# -----------------------
# VPC, Subnets, Gateways
# -----------------------

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${locals.name_prefix}-vpc"
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${locals.name_prefix}-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true

  tags = {
    Name = "${locals.name_prefix}-public-subnet"
  }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.private_subnet_cidr
  map_public_ip_on_launch = false

  tags = {
    Name = "${locals.name_prefix}-private-subnet"
  }
}

resource "aws_eip" "nat" {
  vpc = true

  tags = {
    Name = "${locals.name_prefix}-nat-eip"
  }
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "${locals.name_prefix}-nat"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "${locals.name_prefix}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this.id
  }

  tags = {
    Name = "${locals.name_prefix}-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

# -----------------------
# Security Groups
# -----------------------

# SG para a instância EC2 (API + stack)
resource "aws_security_group" "ec2" {
  name        = "${locals.name_prefix}-ec2-sg"
  description = "Security group para EC2 Stage"
  vpc_id      = aws_vpc.this.id

  # SSH opcional (restringir a um IP fixo)
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # TODO: restringir
  }

  # API (8000) somente vinda do ALB
  ingress {
    description      = "API from ALB"
    from_port        = 8000
    to_port          = 8000
    protocol         = "tcp"
    security_groups  = [aws_security_group.alb.id]
  }

  # Egress full
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${locals.name_prefix}-ec2-sg"
  }
}

# SG para o ALB
resource "aws_security_group" "alb" {
  name        = "${locals.name_prefix}-alb-sg"
  description = "Security group para o ALB"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.allowed_http_ingress_cidrs
  }

  # Se for usar HTTPS, adicionar aqui
  # ingress {
  #   description = "HTTPS"
  #   from_port   = 443
  #   to_port     = 443
  #   protocol    = "tcp"
  #   cidr_blocks = var.allowed_http_ingress_cidrs
  # }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${locals.name_prefix}-alb-sg"
  }
}

# -----------------------
# RDS Postgres
# -----------------------

resource "aws_db_subnet_group" "this" {
  name       = "${locals.name_prefix}-db-subnet-group"
  subnet_ids = [aws_subnet.private.id]

  tags = {
    Name = "${locals.name_prefix}-db-subnet-group"
  }
}

resource "aws_security_group" "db" {
  name        = "${locals.name_prefix}-db-sg"
  description = "Security group para RDS Postgres"
  vpc_id      = aws_vpc.this.id

  ingress {
    description      = "Postgres from EC2"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    security_groups  = [aws_security_group.ec2.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${locals.name_prefix}-db-sg"
  }
}

resource "aws_db_instance" "this" {
  identifier              = "${locals.name_prefix}-db"
  engine                  = "postgres"
  engine_version          = "15.5"
  instance_class          = "db.t3.medium"
  username                = var.db_username
  password                = var.db_password
  allocated_storage       = var.db_allocated_storage
  db_subnet_group_name    = aws_db_subnet_group.this.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  publicly_accessible     = false
  skip_final_snapshot     = true
  deletion_protection     = false

  tags = {
    Name = "${locals.name_prefix}-db"
  }
}

# -----------------------
# IAM para EC2
# -----------------------

resource "aws_iam_role" "ec2_role" {
  name = "${locals.name_prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Permissões para ler parâmetros/segredos (ajuste conforme necessidade)
resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "ec2_secrets" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
  # TODO: Em produção, prefira uma policy custom só de leitura e com ARNs limitados
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${locals.name_prefix}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# -----------------------
# EC2 Instance (Stage)
# -----------------------

data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "stage" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.private.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name               = var.ec2_key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  associate_public_ip_address = false

  root_block_device {
    volume_size = 60
    volume_type = "gp3"
  }

  # TODO: se quiser volumes separados pra /data, usar aws_ebs_volume + aws_volume_attachment

  user_data = <<-EOF
              #!/bin/bash
              set -e

              apt-get update -y
              apt-get install -y docker.io docker-compose git

              usermod -aG docker ubuntu

              mkdir -p /data/ollama /data/prometheus /data/grafana /data/tempo
              chown -R ubuntu:ubuntu /data

              cd /home/ubuntu
              sudo -u ubuntu git clone https://github.com/leleoaraxa/araquem.git
              cd araquem

              # TODO: aqui você pode:
              # - buscar .env.stage no SSM/Secrets Manager via script
              # - ou copiar manualmente via SSH

              # Exemplo simples (esperando que .env.stage já exista):
              sudo -u ubuntu docker-compose -f docker-compose.stage.yaml --env-file .env.stage up -d
              EOF

  tags = {
    Name = "${locals.name_prefix}-ec2"
  }
}

# -----------------------
# ALB + Target Group + Listener
# -----------------------

resource "aws_lb" "this" {
  name               = "${locals.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public.id]

  tags = {
    Name = "${locals.name_prefix}-alb"
  }
}

resource "aws_lb_target_group" "api" {
  name     = "${locals.name_prefix}-tg-api"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.this.id

  health_check {
    path                = "/healthz"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${locals.name_prefix}-tg-api"
  }
}

resource "aws_lb_target_group_attachment" "ec2_api" {
  target_group_arn = aws_lb_target_group.api.arn
  target_id        = aws_instance.stage.id
  port             = 8000
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}
