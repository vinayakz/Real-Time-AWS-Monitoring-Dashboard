#!/usr/bin/env python3
"""
Real EC2 Analysis Script for ap-south-1 region
Provides detailed cost optimization recommendations
"""

import boto3
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

class EC2CostAnalyzer:
    def __init__(self, region='ap-south-1'):
        self.region = region
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
    def get_all_instances(self) -> List[Dict]:
        """Get all EC2 instances in the region"""
        try:
            response = self.ec2_client.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'terminated':
                        instances.append({
                            'InstanceId': instance['InstanceId'],
                            'InstanceType': instance['InstanceType'],
                            'State': instance['State']['Name'],
                            'LaunchTime': instance['LaunchTime'],
                            'Platform': instance.get('Platform', 'Linux'),
                            'VpcId': instance.get('VpcId', 'N/A'),
                            'SubnetId': instance.get('SubnetId', 'N/A'),
                            'Tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        })
            return instances
        except Exception as e:
            print(f"Error fetching instances: {e}")
            return []
    
    def get_cpu_utilization(self, instance_id: str, days: int = 7) -> Dict:
        """Get CPU utilization metrics for an instance"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour intervals
                Statistics=['Average', 'Maximum']
            )
            
            if response['Datapoints']:
                datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                max_cpu = max(dp['Maximum'] for dp in datapoints)
                
                return {
                    'average_cpu': round(avg_cpu, 2),
                    'max_cpu': round(max_cpu, 2),
                    'datapoints': len(datapoints),
                    'period_days': days
                }
            return {'average_cpu': 0, 'max_cpu': 0, 'datapoints': 0, 'period_days': days}
        except Exception as e:
            print(f"Error fetching CPU metrics for {instance_id}: {e}")
            return {'average_cpu': 0, 'max_cpu': 0, 'datapoints': 0, 'period_days': days}
    
    def get_memory_utilization(self, instance_id: str, days: int = 7) -> Dict:
        """Get memory utilization if CloudWatch agent is installed"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='CWAgent',
                MetricName='mem_used_percent',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            if response['Datapoints']:
                datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                avg_memory = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                max_memory = max(dp['Maximum'] for dp in datapoints)
                
                return {
                    'average_memory': round(avg_memory, 2),
                    'max_memory': round(max_memory, 2),
                    'free_memory': round(100 - avg_memory, 2),
                    'datapoints': len(datapoints)
                }
            return {'average_memory': 0, 'max_memory': 0, 'free_memory': 0, 'datapoints': 0}
        except Exception as e:
            return {'average_memory': 0, 'max_memory': 0, 'free_memory': 0, 'datapoints': 0}
    
    def get_instance_pricing(self, instance_type: str) -> Dict:
        """Get approximate pricing for instance types in ap-south-1"""
        # Approximate pricing for ap-south-1 (Mumbai) - On-Demand Linux instances
        pricing = {
            't2.nano': {'hourly': 0.0058, 'monthly': 4.18},
            't2.micro': {'hourly': 0.0116, 'monthly': 8.35},
            't2.small': {'hourly': 0.023, 'monthly': 16.56},
            't2.medium': {'hourly': 0.046, 'monthly': 33.12},
            't2.large': {'hourly': 0.092, 'monthly': 66.24},
            't2.xlarge': {'hourly': 0.184, 'monthly': 132.48},
            't3.nano': {'hourly': 0.0052, 'monthly': 3.74},
            't3.micro': {'hourly': 0.0104, 'monthly': 7.49},
            't3.small': {'hourly': 0.0208, 'monthly': 14.98},
            't3.medium': {'hourly': 0.0416, 'monthly': 29.95},
            't3.large': {'hourly': 0.0832, 'monthly': 59.90},
            't3.xlarge': {'hourly': 0.1664, 'monthly': 119.81},
            't3.2xlarge': {'hourly': 0.3328, 'monthly': 239.62},
            'm5.large': {'hourly': 0.096, 'monthly': 69.12},
            'm5.xlarge': {'hourly': 0.192, 'monthly': 138.24},
            'm5.2xlarge': {'hourly': 0.384, 'monthly': 276.48},
            'm5.4xlarge': {'hourly': 0.768, 'monthly': 552.96},
            'c5.large': {'hourly': 0.085, 'monthly': 61.20},
            'c5.xlarge': {'hourly': 0.17, 'monthly': 122.40},
            'c5.2xlarge': {'hourly': 0.34, 'monthly': 244.80},
            'r5.large': {'hourly': 0.126, 'monthly': 90.72},
            'r5.xlarge': {'hourly': 0.252, 'monthly': 181.44}
        }
        
        return pricing.get(instance_type, {'hourly': 0, 'monthly': 0})
    
    def analyze_cost_optimization(self, instance_data: Dict) -> Dict:
        """Provide cost optimization recommendations"""
        cpu_avg = instance_data.get('cpu_metrics', {}).get('average_cpu', 0)
        cpu_max = instance_data.get('cpu_metrics', {}).get('max_cpu', 0)
        instance_type = instance_data['InstanceType']
        current_cost = instance_data.get('pricing', {}).get('monthly', 0)
        
        recommendations = []
        potential_savings = 0
        
        # CPU-based recommendations
        if cpu_avg < 10:
            recommendations.append({
                'type': 'UNDERUTILIZED',
                'severity': 'HIGH',
                'message': f'Instance is severely underutilized (avg CPU: {cpu_avg}%). Consider stopping or downsizing.',
                'action': 'Consider t3.nano or t3.micro',
                'potential_saving': current_cost * 0.7
            })
            potential_savings += current_cost * 0.7
        elif cpu_avg < 25:
            recommendations.append({
                'type': 'LOW_UTILIZATION',
                'severity': 'MEDIUM',
                'message': f'Instance has low utilization (avg CPU: {cpu_avg}%). Consider downsizing.',
                'action': 'Downsize to smaller instance type',
                'potential_saving': current_cost * 0.4
            })
            potential_savings += current_cost * 0.4
        elif cpu_avg > 80:
            recommendations.append({
                'type': 'HIGH_UTILIZATION',
                'severity': 'MEDIUM',
                'message': f'Instance has high utilization (avg CPU: {cpu_avg}%). Consider upgrading.',
                'action': 'Upgrade to larger instance type',
                'potential_saving': 0
            })
        
        # Instance type specific recommendations
        if instance_type.startswith('t2.') and cpu_avg > 20:
            recommendations.append({
                'type': 'INSTANCE_FAMILY',
                'severity': 'LOW',
                'message': 'Consider upgrading from t2 to t3 family for better performance and cost efficiency.',
                'action': f'Upgrade to {instance_type.replace("t2.", "t3.")}',
                'potential_saving': current_cost * 0.1
            })
        
        return {
            'recommendations': recommendations,
            'total_potential_savings': round(potential_savings, 2),
            'optimization_score': self._calculate_optimization_score(cpu_avg, cpu_max)
        }
    
    def _calculate_optimization_score(self, cpu_avg: float, cpu_max: float) -> int:
        """Calculate optimization score (0-100)"""
        if cpu_avg < 10:
            return 20  # Very poor utilization
        elif cpu_avg < 25:
            return 50  # Poor utilization
        elif cpu_avg < 50:
            return 75  # Good utilization
        elif cpu_avg < 80:
            return 90  # Very good utilization
        else:
            return 70  # High utilization, might need upgrade
    
    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        print("🔍 Fetching EC2 instances in ap-south-1...")
        instances = self.get_all_instances()
        
        if not instances:
            return {'error': 'No instances found or unable to access AWS'}
        
        print(f"📊 Found {len(instances)} instances. Analyzing metrics...")
        
        detailed_analysis = []
        total_monthly_cost = 0
        total_potential_savings = 0
        
        for instance in instances:
            instance_id = instance['InstanceId']
            instance_type = instance['InstanceType']
            
            print(f"   Analyzing {instance_id} ({instance_type})...")
            
            # Get metrics
            cpu_metrics = self.get_cpu_utilization(instance_id)
            memory_metrics = self.get_memory_utilization(instance_id)
            pricing = self.get_instance_pricing(instance_type)
            
            # Combine data
            instance_data = {
                **instance,
                'cpu_metrics': cpu_metrics,
                'memory_metrics': memory_metrics,
                'pricing': pricing
            }
            
            # Get optimization recommendations
            optimization = self.analyze_cost_optimization(instance_data)
            instance_data['optimization'] = optimization
            
            detailed_analysis.append(instance_data)
            total_monthly_cost += pricing.get('monthly', 0)
            total_potential_savings += optimization.get('total_potential_savings', 0)
        
        return {
            'region': self.region,
            'total_instances': len(instances),
            'total_monthly_cost': round(total_monthly_cost, 2),
            'total_potential_savings': round(total_potential_savings, 2),
            'savings_percentage': round((total_potential_savings / total_monthly_cost * 100) if total_monthly_cost > 0 else 0, 1),
            'instances': detailed_analysis,
            'generated_at': datetime.utcnow().isoformat()
        }

def main():
    analyzer = EC2CostAnalyzer('ap-south-1')
    
    try:
        report = analyzer.generate_report()
        
        if 'error' in report:
            print(f"❌ Error: {report['error']}")
            return
        
        print("\n" + "="*80)
        print("🎯 EC2 COST OPTIMIZATION ANALYSIS - AP-SOUTH-1")
        print("="*80)
        print(f"📊 Total Instances: {report['total_instances']}")
        print(f"💰 Total Monthly Cost: ${report['total_monthly_cost']}")
        print(f"💡 Potential Savings: ${report['total_potential_savings']} ({report['savings_percentage']}%)")
        print("\n📋 INSTANCE DETAILS:")
        print("-" * 80)
        
        for instance in report['instances']:
            print(f"\n🖥️  {instance['InstanceId']} ({instance['InstanceType']})")
            print(f"   State: {instance['State']}")
            print(f"   CPU Usage: Avg {instance['cpu_metrics']['average_cpu']}% | Max {instance['cpu_metrics']['max_cpu']}%")
            
            if instance['memory_metrics']['datapoints'] > 0:
                print(f"   Memory: Used {instance['memory_metrics']['average_memory']}% | Free {instance['memory_metrics']['free_memory']}%")
            else:
                print("   Memory: No CloudWatch agent data available")
            
            print(f"   Monthly Cost: ${instance['pricing']['monthly']}")
            print(f"   Optimization Score: {instance['optimization']['optimization_score']}/100")
            
            if instance['optimization']['recommendations']:
                print("   🔧 Recommendations:")
                for rec in instance['optimization']['recommendations']:
                    print(f"      • {rec['message']}")
                    print(f"        Action: {rec['action']}")
                    if rec['potential_saving'] > 0:
                        print(f"        Potential Saving: ${rec['potential_saving']:.2f}/month")
        
        # Save detailed report
        with open('/home/ubuntu/aws-cloudwatch-analyzer/ec2_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: ec2_analysis_report.json")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    main()
