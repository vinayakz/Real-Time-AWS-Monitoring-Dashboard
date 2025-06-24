# Deployment Guide

## Quick Start

### Prerequisites
- Python 3.8+
- AWS CLI configured or AWS credentials available
- Required AWS permissions for CloudWatch Logs and Metrics

### Installation

1. **Clone/Download the project**
   ```bash
   # If you have the project files
   cd aws-cloudwatch-analyzer
   ```

2. **Install Dependencies**
   ```bash
   # Install production dependencies
   pip install -r requirements/requirements.txt
   
   # Or install development dependencies
   pip install -r requirements/requirements-dev.txt
   ```

3. **Configure AWS Credentials**
   
   **Option A: AWS CLI**
   ```bash
   aws configure
   ```
   
   **Option B: Environment Variables**
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```
   
   **Option C: IAM Roles (for EC2/ECS deployment)**
   - Attach appropriate IAM role to your compute instance

4. **Run the Application**
   ```bash
   streamlit run src/main.py
   ```

5. **Access the Application**
   - Open your browser to `http://localhost:8501`

## AWS Permissions Required

Create an IAM policy with the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams",
                "logs:FilterLogEvents",
                "logs:GetLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeRegions"
            ],
            "Resource": "*"
        }
    ]
}
```

## Docker Deployment

### Build and Run with Docker

1. **Build the Docker image**
   ```bash
   docker build -t aws-cloudwatch-analyzer .
   ```

2. **Run the container**
   ```bash
   docker run -p 8501:8501 \
     -e AWS_ACCESS_KEY_ID=your_access_key \
     -e AWS_SECRET_ACCESS_KEY=your_secret_key \
     -e AWS_DEFAULT_REGION=us-east-1 \
     aws-cloudwatch-analyzer
   ```

3. **Using Docker Compose** (create docker-compose.yml)
   ```yaml
   version: '3.8'
   services:
     cloudwatch-analyzer:
       build: .
       ports:
         - "8501:8501"
       environment:
         - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
         - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
         - AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}
   ```

   Run with:
   ```bash
   docker-compose up
   ```

## Cloud Deployment Options

### AWS ECS (Elastic Container Service)

1. **Push to ECR**
   ```bash
   # Create ECR repository
   aws ecr create-repository --repository-name aws-cloudwatch-analyzer
   
   # Get login token
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Tag and push
   docker tag aws-cloudwatch-analyzer:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/aws-cloudwatch-analyzer:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/aws-cloudwatch-analyzer:latest
   ```

2. **Create ECS Task Definition**
   ```json
   {
     "family": "cloudwatch-analyzer",
     "taskRoleArn": "arn:aws:iam::<account-id>:role/CloudWatchAnalyzerRole",
     "containerDefinitions": [
       {
         "name": "cloudwatch-analyzer",
         "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/aws-cloudwatch-analyzer:latest",
         "portMappings": [
           {
             "containerPort": 8501,
             "protocol": "tcp"
           }
         ],
         "memory": 512,
         "cpu": 256
       }
     ]
   }
   ```

### AWS EC2

1. **Launch EC2 instance**
2. **Install Docker**
   ```bash
   sudo yum update -y
   sudo yum install -y docker
   sudo service docker start
   sudo usermod -a -G docker ec2-user
   ```
3. **Deploy the application**
   ```bash
   docker run -d -p 8501:8501 \
     --name cloudwatch-analyzer \
     aws-cloudwatch-analyzer
   ```

### Streamlit Cloud

1. **Push code to GitHub**
2. **Connect to Streamlit Cloud**
3. **Configure secrets** in Streamlit Cloud dashboard:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`

## Environment Configuration

### Production Settings

Create a `.env` file:
```bash
AWS_DEFAULT_REGION=us-east-1
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
```

### Streamlit Configuration

The application includes a `.streamlit/config.toml` file with optimized settings:
- Disabled development mode
- Enabled XSRF protection
- Disabled usage statistics collection

## Monitoring and Logging

### Application Logs
- Streamlit logs are available in the container/instance logs
- AWS API errors are displayed in the UI
- Use CloudWatch Logs for centralized logging in AWS deployments

### Health Checks
- Docker health check endpoint: `/_stcore/health`
- Monitor application availability and performance

### Performance Optimization
- Use caching for AWS API calls (5-minute TTL)
- Implement pagination for large datasets
- Use efficient data structures (pandas DataFrames)

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   - Verify AWS credentials are properly configured
   - Check IAM permissions
   - Ensure region is set correctly

2. **No Lambda Functions Found**
   - Verify Lambda functions exist in the selected region
   - Check CloudWatch Logs permissions
   - Ensure log groups are created (functions have been invoked)

3. **No EC2 Instances Found**
   - Verify EC2 instances exist in the selected region
   - Check EC2 describe permissions
   - Ensure instances are not terminated

4. **Performance Issues**
   - Reduce time range for analysis
   - Limit number of log events retrieved
   - Use appropriate instance size for deployment

### Debug Mode

Run with debug logging:
```bash
STREAMLIT_LOGGER_LEVEL=debug streamlit run src/main.py
```

## Security Considerations

1. **Credentials Management**
   - Never hardcode AWS credentials
   - Use IAM roles when possible
   - Rotate credentials regularly

2. **Network Security**
   - Use HTTPS in production
   - Implement proper firewall rules
   - Consider VPC deployment for sensitive environments

3. **Access Control**
   - Implement authentication if needed
   - Use least privilege IAM policies
   - Monitor access logs

## Scaling Considerations

1. **Horizontal Scaling**
   - Deploy multiple instances behind a load balancer
   - Use container orchestration (ECS, EKS, Kubernetes)

2. **Vertical Scaling**
   - Increase instance size for better performance
   - Optimize memory usage for large datasets

3. **Caching Strategy**
   - Implement Redis for shared caching
   - Use CloudFront for static assets
   - Consider database caching for frequent queries
