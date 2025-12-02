variable "project_name" {
  description = "Nome do projeto"
  type        = string
  default     = "araquem"
}

variable "environment" {
  description = "Ambiente (dev/stage/prod)"
  type        = string
  default     = "stage"
}

variable "aws_region" {
  description = "Região AWS"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR da VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR da subnet pública"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR da subnet privada"
  type        = string
  default     = "10.0.2.0/24"
}

variable "ec2_instance_type" {
  description = "Tipo da instância EC2 para Stage"
  type        = string
  default     = "c6a.2xlarge"
}

variable "ec2_key_name" {
  description = "Nome da key pair para acesso SSH"
  type        = string
}

variable "db_username" {
  description = "Usuário do banco Postgres"
  type        = string
}

variable "db_password" {
  description = "Senha do banco Postgres"
  type        = string
  sensitive   = true
}

variable "db_allocated_storage" {
  description = "Storage em GB para o RDS"
  type        = number
  default     = 20
}

variable "allowed_http_ingress_cidrs" {
  description = "Lista de CIDRs que podem acessar o ALB (HTTP/HTTPS)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
