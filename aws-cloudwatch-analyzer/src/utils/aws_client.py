"""
AWS client utilities following the Singleton pattern for efficient resource management.
"""

import boto3
import streamlit as st
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError
from src.config.settings import aws_config


class AWSClientManager:
    """
    Singleton class to manage AWS clients efficiently.
    Implements the Singleton pattern to ensure single instance per session.
    """
    
    _instance = None
    _clients = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AWSClientManager, cls).__new__(cls)
        return cls._instance
    
    def get_client(self, service_name: str, region: Optional[str] = None) -> Optional[object]:
        """
        Get AWS client for specified service.
        
        Args:
            service_name: AWS service name (e.g., 'logs', 'cloudwatch')
            region: AWS region (defaults to configured region)
            
        Returns:
            AWS client object or None if failed
        """
        region = region or aws_config.region
        client_key = f"{service_name}_{region}"
        
        if client_key not in self._clients:
            try:
                self._clients[client_key] = boto3.client(
                    service_name,
                    region_name=region
                )
            except (NoCredentialsError, ClientError) as e:
                st.error(f"Failed to create AWS {service_name} client: {str(e)}")
                return None
                
        return self._clients[client_key]
    
    def test_connection(self) -> bool:
        """
        Test AWS connection by attempting to list log groups.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logs_client = self.get_client('logs')
            if logs_client:
                logs_client.describe_log_groups(limit=1)
                return True
        except Exception as e:
            st.error(f"AWS connection test failed: {str(e)}")
        return False
    
    def get_available_regions(self) -> list:
        """
        Get list of available AWS regions for the current account.
        
        Returns:
            List of region names
        """
        try:
            ec2_client = self.get_client('ec2')
            if ec2_client:
                response = ec2_client.describe_regions()
                return [region['RegionName'] for region in response['Regions']]
        except Exception:
            # Fallback to predefined regions if API call fails
            from src.config.settings import get_aws_regions
            return get_aws_regions()
        
        return []


# Global instance
aws_client_manager = AWSClientManager()
