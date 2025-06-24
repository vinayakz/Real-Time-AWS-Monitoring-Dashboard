"""
Unit tests for CloudWatch service layer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError

from src.services.cloudwatch_service import CloudWatchLogsService, CloudWatchMetricsService


class TestCloudWatchLogsService:
    """Test cases for CloudWatchLogsService class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = CloudWatchLogsService()
    
    @patch('src.services.cloudwatch_service.aws_client_manager')
    def test_get_log_groups_success(self, mock_client_manager):
        """Test successful log groups retrieval."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                'logGroups': [
                    {
                        'logGroupName': '/aws/lambda/test-function',
                        'creationTime': 1234567890,
                        'storedBytes': 1024
                    },
                    {
                        'logGroupName': '/aws/apigateway/test-api',
                        'creationTime': 1234567891,
                        'storedBytes': 2048
                    }
                ]
            }
        ]
        mock_client_manager.get_client.return_value = mock_client
        
        # Create new service instance to use mocked client
        service = CloudWatchLogsService()
        result = service.get_log_groups()
        
        assert len(result) == 2
        assert result[0]['name'] == '/aws/apigateway/test-api'  # Should be sorted
        assert result[1]['name'] == '/aws/lambda/test-function'
    
    @patch('src.services.cloudwatch_service.aws_client_manager')
    @patch('streamlit.error')
    def test_get_log_groups_client_error(self, mock_st_error, mock_client_manager):
        """Test log groups retrieval with client error."""
        mock_client = Mock()
        mock_client.get_paginator.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='DescribeLogGroups'
        )
        mock_client_manager.get_client.return_value = mock_client
        
        service = CloudWatchLogsService()
        result = service.get_log_groups()
        
        assert result == []
        mock_st_error.assert_called_once()
    
    @patch('src.services.cloudwatch_service.CloudWatchLogsService.get_log_groups')
    def test_get_lambda_log_groups(self, mock_get_log_groups):
        """Test filtering for Lambda log groups only."""
        mock_get_log_groups.return_value = [
            {'name': '/aws/lambda/function1', 'creation_time': 123, 'size_bytes': 1024},
            {'name': '/aws/apigateway/api1', 'creation_time': 124, 'size_bytes': 2048},
            {'name': '/aws/lambda/function2', 'creation_time': 125, 'size_bytes': 512}
        ]
        
        service = CloudWatchLogsService()
        result = service.get_lambda_log_groups()
        
        assert len(result) == 2
        assert all('/aws/lambda/' in group['name'] for group in result)
    
    @patch('src.services.cloudwatch_service.aws_client_manager')
    def test_get_log_events_success(self, mock_client_manager):
        """Test successful log events retrieval."""
        mock_client = Mock()
        mock_paginator = Mock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                'events': [
                    {
                        'timestamp': 1234567890000,
                        'message': 'START RequestId: 123',
                        'ingestionTime': 1234567890001
                    },
                    {
                        'timestamp': 1234567891000,
                        'message': 'Duration: 150.25 ms',
                        'ingestionTime': 1234567891001
                    }
                ]
            }
        ]
        mock_client_manager.get_client.return_value = mock_client
        
        service = CloudWatchLogsService()
        result = service.get_log_events('/aws/lambda/test-function', 24, 1000)
        
        assert len(result) == 2
        assert result[0]['message'] == 'START RequestId: 123'
        assert result[1]['message'] == 'Duration: 150.25 ms'
    
    @patch('src.services.cloudwatch_service.aws_client_manager')
    def test_search_log_events_success(self, mock_client_manager):
        """Test successful log events search."""
        mock_client = Mock()
        mock_client.filter_log_events.return_value = {
            'events': [
                {
                    'timestamp': 1234567890000,
                    'message': 'ERROR Something went wrong',
                    'ingestionTime': 1234567890001
                }
            ]
        }
        mock_client_manager.get_client.return_value = mock_client
        
        service = CloudWatchLogsService()
        result = service.search_log_events('/aws/lambda/test-function', 'ERROR', 24)
        
        assert len(result) == 1
        assert 'ERROR' in result[0]['message']


class TestCloudWatchMetricsService:
    """Test cases for CloudWatchMetricsService class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = CloudWatchMetricsService()
    
    @patch('src.services.cloudwatch_service.aws_client_manager')
    def test_get_ec2_instances_success(self, mock_client_manager):
        """Test successful EC2 instances retrieval."""
        mock_ec2_client = Mock()
        mock_ec2_client.describe_instances.return_value = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't2.micro',
                            'State': {'Name': 'running'},
                            'Tags': [
                                {'Key': 'Name', 'Value': 'Test Instance'}
                            ]
                        },
                        {
                            'InstanceId': 'i-0987654321fedcba0',
                            'InstanceType': 't2.small',
                            'State': {'Name': 'terminated'},
                            'Tags': []
                        }
                    ]
                }
            ]
        }
        mock_client_manager.get_client.return_value = mock_ec2_client
        
        service = CloudWatchMetricsService()
        result = service.get_ec2_instances()
        
        # Should only return non-terminated instances
        assert len(result) == 1
        assert result[0]['id'] == 'i-1234567890abcdef0'
        assert result[0]['name'] == 'Test Instance'
        assert result[0]['type'] == 't2.micro'
        assert result[0]['state'] == 'running'
    
    @patch('src.services.cloudwatch_service.aws_client_manager')
    def test_get_metric_data_success(self, mock_client_manager):
        """Test successful metric data retrieval."""
        mock_cw_client = Mock()
        mock_cw_client.get_metric_statistics.return_value = {
            'Datapoints': [
                {
                    'Timestamp': datetime(2023, 1, 1, 12, 0),
                    'Average': 50.5,
                    'Unit': 'Percent'
                },
                {
                    'Timestamp': datetime(2023, 1, 1, 12, 5),
                    'Average': 60.2,
                    'Unit': 'Percent'
                }
            ]
        }
        mock_client_manager.get_client.return_value = mock_cw_client
        
        service = CloudWatchMetricsService()
        result = service.get_metric_data(
            'AWS/EC2',
            'CPUUtilization',
            [{'Name': 'InstanceId', 'Value': 'i-1234567890abcdef0'}],
            24,
            'Average'
        )
        
        assert len(result) == 2
        assert result[0]['Average'] == 50.5
        assert result[1]['Average'] == 60.2
    
    @patch('src.services.cloudwatch_service.CloudWatchMetricsService.get_metric_data')
    def test_get_lambda_metrics(self, mock_get_metric_data):
        """Test Lambda metrics aggregation."""
        mock_get_metric_data.return_value = [
            {'Timestamp': datetime(2023, 1, 1, 12, 0), 'Sum': 100}
        ]
        
        service = CloudWatchMetricsService()
        result = service.get_lambda_metrics('test-function', 24)
        
        # Should call get_metric_data for each Lambda metric
        expected_metrics = ['invocations', 'errors', 'duration', 'throttles', 'concurrentexecutions']
        assert all(metric in result for metric in expected_metrics)
        assert mock_get_metric_data.call_count == 5
    
    @patch('src.services.cloudwatch_service.CloudWatchMetricsService.get_metric_data')
    def test_get_ec2_metrics(self, mock_get_metric_data):
        """Test EC2 metrics aggregation."""
        mock_get_metric_data.return_value = [
            {'Timestamp': datetime(2023, 1, 1, 12, 0), 'Average': 50.0}
        ]
        
        service = CloudWatchMetricsService()
        result = service.get_ec2_metrics('i-1234567890abcdef0', 24)
        
        # Should call get_metric_data for each EC2 metric
        expected_metrics = ['cpuutilization', 'networkin', 'networkout', 'diskreadbytes', 'diskwritebytes']
        assert all(metric in result for metric in expected_metrics)
        assert mock_get_metric_data.call_count == 5


if __name__ == "__main__":
    pytest.main([__file__])
