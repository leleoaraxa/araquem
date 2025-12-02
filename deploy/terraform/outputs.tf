output "vpc_id" {
  value       = aws_vpc.this.id
  description = "ID da VPC do Stage"
}

output "ec2_private_ip" {
  value       = aws_instance.stage.private_ip
  description = "IP privado da EC2 do Stage"
}

output "alb_dns_name" {
  value       = aws_lb.this.dns_name
  description = "DNS do ALB para acessar a API do Stage"
}

output "rds_endpoint" {
  value       = aws_db_instance.this.address
  description = "Endpoint do RDS Postgres do Stage"
}
