module "db_default" {
  source  = "terraform-aws-modules/rds/aws"
  version = "6.12.0"

  identifier                     = local.dbname
  instance_use_identifier_prefix = true

  # create_db_option_group    = false
  # create_db_parameter_group = false

  # All available versions: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html#PostgreSQL.Concepts
  engine               = "postgres"
  engine_version       = "14"
  family               = "postgres14" # DB parameter group
  major_engine_version = "14"         # DB option group
  instance_class       = "db.t4g.large"

  allocated_storage = 20
  max_allocated_storage = 100

  db_name  = jsondecode(data.aws_secretsmanager_secret_version.galactic-db.secret_string)["POSTGRES_DBNAME"]
  username = jsondecode(data.aws_secretsmanager_secret_version.galactic-db.secret_string)["POSTGRES_USERNAME"]
  password = jsondecode(data.aws_secretsmanager_secret_version.galactic-db.secret_string)["POSTGRES_PASSWORD"]
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.security_group.security_group_id]

  maintenance_window      = "Mon:00:00-Mon:03:00"
  backup_window           = "03:00-06:00"
  backup_retention_period = 1
  skip_final_snapshot     = true
  deletion_protection     = true

  tags = local.tags
}

module "security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = local.dbname
  description = "Complete PostgreSQL example security group"
  vpc_id      = module.vpc.vpc_id

  ingress_with_cidr_blocks = [
    {
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      description = "PostgreSQL access from within VPC"
      cidr_blocks = module.vpc.vpc_cidr_block
    },
  ]

  tags = local.tags
}

