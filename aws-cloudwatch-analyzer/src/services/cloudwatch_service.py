"""
CloudWatch service layer implementing the Repository pattern.
Handles all AWS CloudWatch API interactions.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Any
from botocore.exceptions import ClientError

from src.utils.aws_client import aws_client_manager
from src.utils.data_processor import TimeRangeProcessor
from src.config.settings import aws_config


class CloudWatchLogsService:
    """Service for CloudWatch Logs operations."""
    
    def __init__(self):
        self.client = aws_client_manager.get_client('logs')
        self.time_processor = TimeRangeProcessor()
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_log_groups(_self) -> List[Dict[str, str]]:
        """
        Retrieve all log groups.
        
        Returns:
            List of log group information
        """
        if not _self.client:
            return []
        
        try:
            log_groups = []
            paginator = _self.client.get_paginator('describe_log_groups')
            
            for page in paginator.paginate():
                for group in page['logGroups']:
                    log_groups.append({
                        'name': group['logGroupName'],
                        'creation_time': group.get('creationTime', 0),
                        'size_bytes': group.get('storedBytes', 0)
                    })
            
            return sorted(log_groups, key=lambda x: x['name'])
            
        except ClientError as e:
            st.error(f"Error fetching log groups: {str(e)}")
            return []
    
    def get_lambda_log_groups(self) -> List[Dict[str, str]]:
        """Get log groups for Lambda functions only."""
        all_groups = self.get_log_groups()
        return [group for group in all_groups if group['name'].startswith('/aws/lambda/')]
    
    @st.cache_data(ttl=300)
    def get_log_events(_self, log_group_name: str, hours_back: int = 24, limit: int = 1000) -> List[Dict]:
        """
        Retrieve log events from a specific log group.
        
        Args:
            log_group_name: Name of the log group
            hours_back: Number of hours to look back
            limit: Maximum number of events to retrieve
            
        Returns:
            List of log events
        """
        if not _self.client:
            return []
        
        try:
            start_time, end_time = _self.time_processor.get_time_range(hours_back)
            
            # Convert to milliseconds timestamp
            start_time_ms = int(start_time.timestamp() * 1000)
            end_time_ms = int(end_time.timestamp() * 1000)
            
            events = []
            paginator = _self.client.get_paginator('filter_log_events')
            
            page_iterator = paginator.paginate(
                logGroupName=log_group_name,
                startTime=start_time_ms,
                endTime=end_time_ms,
                PaginationConfig={'MaxItems': limit}
            )
            
            for page in page_iterator:
                events.extend(page.get('events', []))
            
            return events
            
        except ClientError as e:
            st.error(f"Error fetching log events: {str(e)}")
            return []
    
    def search_log_events(self, log_group_name: str, filter_pattern: str, hours_back: int = 24) -> List[Dict]:
        """
        Search log events with a filter pattern.
        
        Args:
            log_group_name: Name of the log group
            filter_pattern: CloudWatch Logs filter pattern
            hours_back: Number of hours to look back
            
        Returns:
            List of matching log events
        """
        if not self.client:
            return []
        
        try:
            start_time, end_time = self.time_processor.get_time_range(hours_back)
            start_time_ms = int(start_time.timestamp() * 1000)
            end_time_ms = int(end_time.timestamp() * 1000)
            
            response = self.client.filter_log_events(
                logGroupName=log_group_name,
                filterPattern=filter_pattern,
                startTime=start_time_ms,
                endTime=end_time_ms,
                limit=aws_config.max_log_events
            )
            
            return response.get('events', [])
            
        except ClientError as e:
            st.error(f"Error searching log events: {str(e)}")
            return []


class CloudWatchMetricsService:
    """Service for CloudWatch Metrics operations."""
    
    def __init__(self):
        self.client = aws_client_manager.get_client('cloudwatch')
        self.time_processor = TimeRangeProcessor()
    
    @st.cache_data(ttl=300)
    def get_ec2_instances(_self) -> List[Dict[str, str]]:
        """
        Get list of EC2 instances.
        
        Returns:
            List of EC2 instance information
        """
        ec2_client = aws_client_manager.get_client('ec2')
        if not ec2_client:
            return []
        
        try:
            response = ec2_client.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'terminated':
                        name = 'N/A'
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                        
                        instances.append({
                            'id': instance['InstanceId'],
                            'name': name,
                            'type': instance['InstanceType'],
                            'state': instance['State']['Name']
                        })
            
            return instances
            
        except ClientError as e:
            st.error(f"Error fetching EC2 instances: {str(e)}")
            return []
    
    @st.cache_data(ttl=300)
    def get_metric_data(_self, namespace: str, metric_name: str, dimensions: List[Dict], 
                       hours_back: int = 24, statistic: str = 'Average') -> List[Dict]:
        """
        Retrieve metric data from CloudWatch.
        
        Args:
            namespace: AWS namespace (e.g., 'AWS/EC2', 'AWS/Lambda')
            metric_name: Name of the metric
            dimensions: List of dimension dictionaries
            hours_back: Number of hours to look back
            statistic: Statistic to retrieve (Average, Sum, Maximum, etc.)
            
        Returns:
            List of metric data points
        """
        if not _self.client:
            return []
        
        try:
            start_time, end_time = _self.time_processor.get_time_range(hours_back)
            
            response = _self.client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=aws_config.metric_period_seconds,
                Statistics=[statistic]
            )
            
            return response.get('Datapoints', [])
            
        except ClientError as e:
            st.error(f"Error fetching metric data: {str(e)}")
            return []
    
    def get_lambda_metrics(self, function_name: str, hours_back: int = 24) -> Dict[str, List[Dict]]:
        """
        Get comprehensive Lambda function metrics.
        
        Args:
            function_name: Name of the Lambda function
            hours_back: Number of hours to look back
            
        Returns:
            Dictionary containing different metric types
        """
        dimensions = [{'Name': 'FunctionName', 'Value': function_name}]
        
        metrics = {}
        lambda_metrics = [
            ('Invocations', 'Sum'),
            ('Errors', 'Sum'),
            ('Duration', 'Average'),
            ('Throttles', 'Sum'),
            ('ConcurrentExecutions', 'Maximum')
        ]
        
        for metric_name, statistic in lambda_metrics:
            metrics[metric_name.lower()] = self.get_metric_data(
                namespace='AWS/Lambda',
                metric_name=metric_name,
                dimensions=dimensions,
                hours_back=hours_back,
                statistic=statistic
            )
        
        return metrics
    
    def get_ec2_metrics(self, instance_id: str, hours_back: int = 24) -> Dict[str, List[Dict]]:
        """
        Get comprehensive EC2 instance metrics.
        
        Args:
            instance_id: EC2 instance ID
            hours_back: Number of hours to look back
            
        Returns:
            Dictionary containing different metric types
        """
        dimensions = [{'Name': 'InstanceId', 'Value': instance_id}]
        
        metrics = {}
        ec2_metrics = [
            ('CPUUtilization', 'Average'),
            ('NetworkIn', 'Sum'),
            ('NetworkOut', 'Sum'),
            ('DiskReadBytes', 'Sum'),
            ('DiskWriteBytes', 'Sum')
        ]
        
        for metric_name, statistic in ec2_metrics:
            metrics[metric_name.lower()] = self.get_metric_data(
                namespace='AWS/EC2',
                metric_name=metric_name,
                dimensions=dimensions,
                hours_back=hours_back,
                statistic=statistic
            )
        
        return metrics
