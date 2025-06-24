"""
Configuration settings for the AWS CloudWatch Log Analyzer application.
"""

import os
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class AWSConfig:
    """AWS configuration settings."""
    
    region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    profile: str = os.getenv("AWS_PROFILE", "default")
    
    # CloudWatch Logs settings
    max_log_events: int = 1000
    default_time_range_hours: int = 24
    
    # CloudWatch Metrics settings
    metric_period_seconds: int = 300  # 5 minutes
    max_datapoints: int = 1440  # 24 hours of 5-minute intervals


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    title: str = "AWS CloudWatch Log Analyzer"
    page_icon: str = "📊"
    layout: str = "wide"
    
    # UI settings
    sidebar_width: int = 300
    chart_height: int = 400
    
    # Performance settings
    cache_ttl_seconds: int = 300  # 5 minutes


@dataclass
class LogAnalysisConfig:
    """Log analysis specific configuration."""
    
    # Lambda function patterns
    lambda_error_patterns: List[str] = None
    lambda_timeout_pattern: str = r"Task timed out after"
    lambda_memory_pattern: str = r"Max Memory Used: (\d+) MB"
    lambda_duration_pattern: str = r"Duration: ([\d.]+) ms"
    
    # EC2 metric names
    ec2_cpu_metric: str = "CPUUtilization"
    ec2_memory_metric: str = "MemoryUtilization"
    ec2_network_in_metric: str = "NetworkIn"
    ec2_network_out_metric: str = "NetworkOut"
    
    def __post_init__(self):
        if self.lambda_error_patterns is None:
            self.lambda_error_patterns = [
                "ERROR",
                "Exception",
                "Traceback",
                "Failed",
                "Error"
            ]


# Global configuration instances
aws_config = AWSConfig()
app_config = AppConfig()
log_config = LogAnalysisConfig()


def get_aws_regions() -> List[str]:
    """Get list of available AWS regions."""
    return [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
    ]


def get_time_range_options() -> Dict[str, int]:
    """Get available time range options in hours."""
    return {
        "Last Hour": 1,
        "Last 6 Hours": 6,
        "Last 24 Hours": 24,
        "Last 3 Days": 72,
        "Last Week": 168
    }
