"""
Cost Analysis Module for AWS Dashboard
Integrates with Cost Analysis MCP Server
"""

import boto3
import json
import subprocess
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AWSCostAnalyzer:
    def __init__(self, region='ap-south-1'):
        self.region = region
        self.ce_client = boto3.client('ce', region_name='us-east-1')  # Cost Explorer is only in us-east-1
        
        # AP-South-1 pricing data (hourly rates in USD)
        self.ec2_pricing = {
            't2.nano': 0.0058, 't2.micro': 0.0116, 't2.small': 0.0232, 't2.medium': 0.0464,
            't2.large': 0.0928, 't2.xlarge': 0.1856, 't2.2xlarge': 0.3712,
            't3.nano': 0.0052, 't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
            't3.large': 0.0832, 't3.xlarge': 0.1664, 't3.2xlarge': 0.3328,
            'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384, 'm5.4xlarge': 0.768,
            'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34, 'c5.4xlarge': 0.68,
            'r5.large': 0.126, 'r5.xlarge': 0.252, 'r5.2xlarge': 0.504
        }
        
        self.lambda_pricing = {
            'requests_per_million': 0.20,
            'gb_second_rate': 0.0000166667,
            'free_tier_requests': 1_000_000,
            'free_tier_gb_seconds': 400_000
        }
        
        self.storage_pricing = {
            'ebs_gp3': 0.08,  # per GB/month
            'ebs_gp2': 0.10,  # per GB/month
            's3_standard': 0.023,  # per GB/month
            's3_ia': 0.0125  # per GB/month
        }
    
    def get_actual_costs(self, days=30):
        """Get actual costs from AWS Cost Explorer"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            cost_by_service = {}
            total_cost = 0
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    if cost > 0:
                        cost_by_service[service] = cost
                        total_cost += cost
            
            return {
                'total_cost': total_cost,
                'cost_by_service': cost_by_service,
                'period': f"{start_date} to {end_date}"
            }
            
        except Exception as e:
            logger.error(f"Error fetching actual costs: {e}")
            return None
    
    def calculate_ec2_costs(self, instances):
        """Calculate EC2 costs based on instance data"""
        total_cost = 0
        instance_costs = {}
        
        for instance in instances:
            if instance['State'] == 'running':
                instance_type = instance['InstanceType']
                hourly_rate = self.ec2_pricing.get(instance_type, 0.05)  # Default rate
                
                # Calculate monthly cost (720 hours = 30 days * 24 hours)
                monthly_cost = hourly_rate * 720
                
                instance_costs[instance['InstanceId']] = {
                    'name': instance['Name'],
                    'type': instance_type,
                    'hourly_rate': hourly_rate,
                    'monthly_cost': monthly_cost,
                    'daily_cost': hourly_rate * 24,
                    'state': instance['State']
                }
                
                total_cost += monthly_cost
        
        return {
            'total_monthly_cost': total_cost,
            'instance_details': instance_costs,
            'running_instances': len([i for i in instances if i['State'] == 'running']),
            'total_instances': len(instances)
        }
    
    def calculate_lambda_costs(self, functions, estimated_usage=None):
        """Calculate Lambda costs based on function data"""
        total_cost = 0
        function_costs = {}
        
        # Default usage estimates if not provided
        default_usage = {
            'requests_per_month': 50000,
            'avg_duration_ms': 1000
        }
        
        for func in functions:
            function_name = func['FunctionName']
            memory_mb = func['MemorySize']
            
            # Use provided usage or defaults
            if estimated_usage and function_name in estimated_usage:
                usage = estimated_usage[function_name]
            else:
                usage = default_usage
            
            requests = usage['requests_per_month']
            duration_ms = usage['avg_duration_ms']
            
            # Calculate costs
            request_cost = max(0, (requests - self.lambda_pricing['free_tier_requests']) / 1_000_000) * self.lambda_pricing['requests_per_million']
            
            gb_seconds = (requests * duration_ms / 1000) * (memory_mb / 1024)
            compute_cost = max(0, gb_seconds - self.lambda_pricing['free_tier_gb_seconds']) * self.lambda_pricing['gb_second_rate']
            
            total_func_cost = request_cost + compute_cost
            
            function_costs[function_name] = {
                'memory_mb': memory_mb,
                'timeout': func['Timeout'],
                'runtime': func['Runtime'],
                'requests_per_month': requests,
                'avg_duration_ms': duration_ms,
                'gb_seconds': gb_seconds,
                'request_cost': request_cost,
                'compute_cost': compute_cost,
                'total_cost': total_func_cost
            }
            
            total_cost += total_func_cost
        
        return {
            'total_monthly_cost': total_cost,
            'function_details': function_costs,
            'total_functions': len(functions)
        }
    
    def estimate_storage_costs(self, instances):
        """Estimate storage costs based on instances"""
        # This is a rough estimate - in practice you'd query EBS volumes
        estimated_storage_gb = len([i for i in instances if i['State'] == 'running']) * 20  # 20GB per instance
        storage_cost = estimated_storage_gb * self.storage_pricing['ebs_gp3']
        
        return {
            'estimated_storage_gb': estimated_storage_gb,
            'monthly_cost': storage_cost,
            'storage_type': 'EBS gp3'
        }
    
    def generate_cost_recommendations(self, ec2_costs, lambda_costs, instances, functions):
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # EC2 Recommendations
        if ec2_costs['total_monthly_cost'] > 50:
            recommendations.append({
                'type': 'immediate',
                'category': 'EC2',
                'title': 'Consider Reserved Instances',
                'description': f'You could save up to 75% on EC2 costs with Reserved Instances for stable workloads',
                'potential_savings': f"${ec2_costs['total_monthly_cost'] * 0.4:.0f}/month",
                'priority': 'high'
            })
        
        # Check for over-provisioned instances
        over_provisioned = 0
        for instance_id, details in ec2_costs['instance_details'].items():
            if details['type'] in ['t3.large', 't3.xlarge', 'm5.large', 'm5.xlarge']:
                over_provisioned += 1
        
        if over_provisioned > 0:
            recommendations.append({
                'type': 'immediate',
                'category': 'EC2',
                'title': 'Right-size EC2 instances',
                'description': f'{over_provisioned} instances may be over-provisioned. Monitor CPU usage and downsize if needed.',
                'potential_savings': f"${over_provisioned * 15:.0f}/month",
                'priority': 'medium'
            })
        
        # Lambda Recommendations
        high_memory_functions = 0
        for func_name, details in lambda_costs['function_details'].items():
            if details['memory_mb'] > 1024:
                high_memory_functions += 1
        
        if high_memory_functions > 0:
            recommendations.append({
                'type': 'immediate',
                'category': 'Lambda',
                'title': 'Optimize Lambda memory allocation',
                'description': f'{high_memory_functions} functions have high memory allocation. Review and optimize based on actual usage.',
                'potential_savings': f"${high_memory_functions * 3:.0f}/month",
                'priority': 'low'
            })
        
        # General recommendations
        recommendations.extend([
            {
                'type': 'medium_term',
                'category': 'General',
                'title': 'Implement auto-scaling',
                'description': 'Use auto-scaling groups to automatically adjust capacity based on demand',
                'potential_savings': '20-40% of compute costs',
                'priority': 'medium'
            },
            {
                'type': 'long_term',
                'category': 'Architecture',
                'title': 'Consider serverless migration',
                'description': 'Evaluate opportunities to migrate workloads to serverless architecture',
                'potential_savings': '30-60% of infrastructure costs',
                'priority': 'low'
            }
        ])
        
        return sorted(recommendations, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)
    
    def generate_comprehensive_analysis(self, instances, functions):
        """Generate comprehensive cost analysis"""
        # Calculate costs for each service
        ec2_costs = self.calculate_ec2_costs(instances)
        lambda_costs = self.calculate_lambda_costs(functions)
        storage_costs = self.estimate_storage_costs(instances)
        
        # Estimate other AWS services
        other_costs = {
            'CloudWatch': 3.0,
            'Data Transfer': 5.0,
            'NAT Gateway': 15.0 if len([i for i in instances if i['State'] == 'running']) > 0 else 0
        }
        
        # Calculate totals
        total_monthly_cost = (
            ec2_costs['total_monthly_cost'] +
            lambda_costs['total_monthly_cost'] +
            storage_costs['monthly_cost'] +
            sum(other_costs.values())
        )
        
        # Get actual costs if available
        actual_costs = self.get_actual_costs()
        
        # Generate recommendations
        recommendations = self.generate_cost_recommendations(ec2_costs, lambda_costs, instances, functions)
        
        # Calculate potential savings
        total_potential_savings = 0
        for rec in recommendations:
            if rec['potential_savings'].startswith('$') and '/month' in rec['potential_savings']:
                try:
                    savings = float(rec['potential_savings'].replace('$', '').replace('/month', ''))
                    total_potential_savings += savings
                except:
                    pass
        
        return {
            'summary': {
                'total_monthly_estimate': total_monthly_cost,
                'total_potential_savings': total_potential_savings,
                'optimization_percentage': (total_potential_savings / total_monthly_cost * 100) if total_monthly_cost > 0 else 0,
                'last_updated': datetime.now().isoformat()
            },
            'service_breakdown': {
                'EC2': ec2_costs['total_monthly_cost'],
                'Lambda': lambda_costs['total_monthly_cost'],
                'EBS Storage': storage_costs['monthly_cost'],
                **other_costs
            },
            'detailed_costs': {
                'ec2': ec2_costs,
                'lambda': lambda_costs,
                'storage': storage_costs
            },
            'actual_costs': actual_costs,
            'recommendations': recommendations,
            'region': self.region
        }

# Example usage
if __name__ == "__main__":
    analyzer = AWSCostAnalyzer()
    
    # Sample data for testing
    sample_instances = [
        {'InstanceId': 'i-123', 'Name': 'Web Server', 'InstanceType': 't3.medium', 'State': 'running'},
        {'InstanceId': 'i-456', 'Name': 'Database', 'InstanceType': 't3.large', 'State': 'running'}
    ]
    
    sample_functions = [
        {'FunctionName': 'auth-function', 'MemorySize': 512, 'Timeout': 30, 'Runtime': 'python3.9'},
        {'FunctionName': 'data-processor', 'MemorySize': 1024, 'Timeout': 60, 'Runtime': 'python3.9'}
    ]
    
    analysis = analyzer.generate_comprehensive_analysis(sample_instances, sample_functions)
    print(json.dumps(analysis, indent=2, default=str))
