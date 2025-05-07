# EKS Container Approach

## Infrastructure

The infrastructure is created by Terraform. 
The files are located in the infra directory split into 3 folders based on their purpose:

### State folder
As the name indicates this handles the state management of the Terraform configuration. 
It needs to be run before anything else as it creates the S3 bucket with the DynamoDB table.
It runs only **once** and it is **not** modified later on.

### VPC folder
In this folder you will find the main infrastructure which was requested - Complete VPC, EKS cluster, RDS Postgres DB.
All of the resources are inside one VPC and use official Terraform modules.
The files have the names of the resource configuration they hold - vpc.tf for the VPC, eks.tf for the EKS, rds.tf for the RDS
In the locals.tf and the variables.tf are located the parameters which are handled as vars. Depending on the needs and customization needed, more could be parameterized.
For the DB secrets I have used **AWS Secrets Manager**. The resources are addressed in the data.tf to avoid pasting secrets in plain text in the repo.

### S3 folder
It holds the configuration of the S3 bucket for the user queries.
It uses KMS server-side encryption, however this could be changed.

## Helm folder
In the helm folder is located the Helm Chart for the DevOps Home Task App. 
The Helm chart contains the required resources to setup the kubernetes resources for the application.

## How to Build and Deploy the Infrastructure and the DevOps Home Task

Run the **CI-CD-Infra** workflow to deploy the Infrastructure
It requires AWS credentials which need to be added as Github Secrets:
>AWS_ACCESS_KEY: ${{ secrets.AWS_ACCESS_KEY }}

>AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

Run the **CI-CD-Deploy** workflow to deploy the DevOps Home Task

It requires the AWS credentials as well.
It also requires the kubeconfig to be added as Github Secret:
>KUBE_CONFIG_DATA

A base64-encoded kubeconfig file with credentials for Kubernetes to access the cluster. 

