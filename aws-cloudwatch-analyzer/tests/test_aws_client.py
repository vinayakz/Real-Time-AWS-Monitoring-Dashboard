"""
Unit tests for AWS client utilities.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError

from src.utils.aws_client import AWSClientManager


class TestAWSClientManager:
    """Test cases for AWSClientManager class."""
    
    def setup_method(self):
        """Reset singleton instance before each test."""
        AWSClientManager._instance = None
        AWSClientManager._clients = {}
    
    def test_singleton_pattern(self):
        """Test that AWSClientManager follows singleton pattern."""
        manager1 = AWSClientManager()
        manager2 = AWSClientManager()
        
        assert manager1 is manager2
        assert id(manager1) == id(manager2)
    
    @patch('boto3.client')
    def test_get_client_success(self, mock_boto_client):
        """Test successful client creation."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        manager = AWSClientManager()
        client = manager.get_client('logs', 'us-east-1')
        
        assert client is mock_client
        mock_boto_client.assert_called_once_with('logs', region_name='us-east-1')
    
    @patch('boto3.client')
    def test_get_client_caching(self, mock_boto_client):
        """Test that clients are cached properly."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        manager = AWSClientManager()
        
        # First call
        client1 = manager.get_client('logs', 'us-east-1')
        # Second call - should use cached client
        client2 = manager.get_client('logs', 'us-east-1')
        
        assert client1 is client2
        # boto3.client should only be called once due to caching
        mock_boto_client.assert_called_once()
    
    @patch('boto3.client')
    def test_get_client_different_regions(self, mock_boto_client):
        """Test that different regions create different clients."""
        mock_client1 = Mock()
        mock_client2 = Mock()
        mock_boto_client.side_effect = [mock_client1, mock_client2]
        
        manager = AWSClientManager()
        
        client1 = manager.get_client('logs', 'us-east-1')
        client2 = manager.get_client('logs', 'us-west-2')
        
        assert client1 is not client2
        assert mock_boto_client.call_count == 2
    
    @patch('boto3.client')
    @patch('streamlit.error')
    def test_get_client_no_credentials(self, mock_st_error, mock_boto_client):
        """Test handling of missing AWS credentials."""
        mock_boto_client.side_effect = NoCredentialsError()
        
        manager = AWSClientManager()
        client = manager.get_client('logs')
        
        assert client is None
        mock_st_error.assert_called_once()
    
    @patch('boto3.client')
    @patch('streamlit.error')
    def test_get_client_client_error(self, mock_st_error, mock_boto_client):
        """Test handling of AWS client errors."""
        mock_boto_client.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='CreateClient'
        )
        
        manager = AWSClientManager()
        client = manager.get_client('logs')
        
        assert client is None
        mock_st_error.assert_called_once()
    
    @patch('src.utils.aws_client.AWSClientManager.get_client')
    def test_test_connection_success(self, mock_get_client):
        """Test successful connection test."""
        mock_logs_client = Mock()
        mock_logs_client.describe_log_groups.return_value = {'logGroups': []}
        mock_get_client.return_value = mock_logs_client
        
        manager = AWSClientManager()
        result = manager.test_connection()
        
        assert result is True
        mock_logs_client.describe_log_groups.assert_called_once_with(limit=1)
    
    @patch('src.utils.aws_client.AWSClientManager.get_client')
    @patch('streamlit.error')
    def test_test_connection_failure(self, mock_st_error, mock_get_client):
        """Test connection test failure."""
        mock_logs_client = Mock()
        mock_logs_client.describe_log_groups.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='DescribeLogGroups'
        )
        mock_get_client.return_value = mock_logs_client
        
        manager = AWSClientManager()
        result = manager.test_connection()
        
        assert result is False
        mock_st_error.assert_called_once()
    
    @patch('src.utils.aws_client.AWSClientManager.get_client')
    def test_get_available_regions_success(self, mock_get_client):
        """Test successful region retrieval."""
        mock_ec2_client = Mock()
        mock_ec2_client.describe_regions.return_value = {
            'Regions': [
                {'RegionName': 'us-east-1'},
                {'RegionName': 'us-west-2'},
                {'RegionName': 'eu-west-1'}
            ]
        }
        mock_get_client.return_value = mock_ec2_client
        
        manager = AWSClientManager()
        regions = manager.get_available_regions()
        
        expected_regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        assert regions == expected_regions
    
    @patch('src.utils.aws_client.AWSClientManager.get_client')
    @patch('src.config.settings.get_aws_regions')
    def test_get_available_regions_fallback(self, mock_get_aws_regions, mock_get_client):
        """Test fallback to predefined regions when API fails."""
        mock_get_client.return_value = None  # Simulate client creation failure
        mock_get_aws_regions.return_value = ['us-east-1', 'us-west-2']
        
        manager = AWSClientManager()
        regions = manager.get_available_regions()
        
        assert regions == ['us-east-1', 'us-west-2']
        mock_get_aws_regions.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
