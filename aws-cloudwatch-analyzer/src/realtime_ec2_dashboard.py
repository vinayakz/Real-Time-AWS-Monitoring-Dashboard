import streamlit as st
import boto3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import psutil
import subprocess
import json

# Page configuration
st.set_page_config(
    page_title='Real-time EC2 Dashboard - AP-South-1',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded'
)

class RealTimeEC2Dashboard:
    def __init__(self):
        self.region = 'ap-south-1'
        self.ec2_client = boto3.client('ec2', region_name=self.region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        
    def get_instance_data(self):
        """Get real-time EC2 instance data"""
        try:
            response = self.ec2_client.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    name = 'Unknown'
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    instances.append({
                        'InstanceId': instance['InstanceId'],
                        'Name': name,
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'PrivateIP': instance.get('PrivateIpAddress', 'N/A'),
                        'PublicIP': instance.get('PublicIpAddress', 'N/A'),
                        'LaunchTime': instance.get('LaunchTime', 'N/A'),
                        'AZ': instance['Placement']['AvailabilityZone']
                    })
            return instances
        except Exception as e:
            st.error(f'Error fetching instance data: {str(e)}')
            return []
    
    def get_cpu_metrics(self, instance_id, hours=24):
        """Get CPU utilization metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average', 'Maximum']
            )
            
            return sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
        except Exception as e:
            st.error(f'Error fetching CPU metrics: {str(e)}')
            return []
    
    def get_network_metrics(self, instance_id, hours=24):
        """Get network metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            network_in = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='NetworkIn',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            network_out = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='NetworkOut',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            return {
                'NetworkIn': sorted(network_in['Datapoints'], key=lambda x: x['Timestamp']),
                'NetworkOut': sorted(network_out['Datapoints'], key=lambda x: x['Timestamp'])
            }
        except Exception as e:
            st.error(f'Error fetching network metrics: {str(e)}')
            return {'NetworkIn': [], 'NetworkOut': []}
    
    def get_local_system_metrics(self):
        """Get local system metrics from the current instance"""
        try:
            # Memory info
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk info
            disk = psutil.disk_usage('/')
            
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Load average
            load_avg = psutil.getloadavg()
            
            return {
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'free': memory.free,
                    'percent': memory.percent,
                    'available': memory.available
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'cpu': {
                    'percent': cpu_percent,
                    'load_avg': load_avg
                }
            }
        except Exception as e:
            st.error(f'Error getting local metrics: {str(e)}')
            return None

def main():
    dashboard = RealTimeEC2Dashboard()
    
    # Title and header
    st.title('🚀 Real-time EC2 Dashboard - AP-South-1')
    st.markdown('**Live monitoring of your EC2 instances with real-time metrics**')
    
    # Auto-refresh
    if st.sidebar.button('🔄 Refresh Data'):
        st.rerun()
    
    # Auto-refresh every 30 seconds
    refresh_rate = st.sidebar.selectbox('Auto-refresh rate', [30, 60, 120, 300], index=0)
    if st.sidebar.checkbox('Enable auto-refresh', value=True):
        time.sleep(refresh_rate)
        st.rerun()
    
    # Get instance data
    instances = dashboard.get_instance_data()
    
    if not instances:
        st.error('No EC2 instances found or unable to fetch data')
        return
    
    # Instance overview
    st.header('📊 Instance Overview')
    
    # Create columns for instance cards
    cols = st.columns(len(instances))
    
    for i, instance in enumerate(instances):
        with cols[i]:
            status_color = '🟢' if instance['State'] == 'running' else '🔴'
            st.metric(
                label=f"{status_color} {instance['Name']}",
                value=instance['InstanceType'],
                delta=instance['State']
            )
            st.write(f"**ID:** {instance['InstanceId']}")
            st.write(f"**Private IP:** {instance['PrivateIP']}")
            st.write(f"**Public IP:** {instance['PublicIP']}")
    
    # Running instances metrics
    running_instances = [i for i in instances if i['State'] == 'running']
    
    if running_instances:
        st.header('📈 Real-time Metrics')
        
        # Select instance for detailed metrics
        selected_instance = st.selectbox(
            'Select instance for detailed metrics:',
            options=[f"{i['Name']} ({i['InstanceId']})" for i in running_instances],
            index=0
        )
        
        instance_id = selected_instance.split('(')[1].split(')')[0]
        
        # Get metrics for selected instance
        cpu_data = dashboard.get_cpu_metrics(instance_id)
        network_data = dashboard.get_network_metrics(instance_id)
        
        # Create two columns for charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader('💻 CPU Utilization (24h)')
            if cpu_data:
                df_cpu = pd.DataFrame(cpu_data)
                fig_cpu = go.Figure()
                fig_cpu.add_trace(go.Scatter(
                    x=df_cpu['Timestamp'],
                    y=df_cpu['Average'],
                    mode='lines+markers',
                    name='Average CPU',
                    line=dict(color='blue')
                ))
                fig_cpu.add_trace(go.Scatter(
                    x=df_cpu['Timestamp'],
                    y=df_cpu['Maximum'],
                    mode='lines+markers',
                    name='Max CPU',
                    line=dict(color='red')
                ))
                fig_cpu.update_layout(
                    title='CPU Utilization Over Time',
                    xaxis_title='Time',
                    yaxis_title='CPU %',
                    height=400
                )
                st.plotly_chart(fig_cpu, use_container_width=True)
            else:
                st.info('No CPU data available for this instance')
        
        with col2:
            st.subheader('🌐 Network Traffic (24h)')
            if network_data['NetworkIn']:
                df_net_in = pd.DataFrame(network_data['NetworkIn'])
                df_net_out = pd.DataFrame(network_data['NetworkOut'])
                
                fig_net = go.Figure()
                if not df_net_in.empty:
                    fig_net.add_trace(go.Scatter(
                        x=df_net_in['Timestamp'],
                        y=df_net_in['Sum'] / (1024*1024),  # Convert to MB
                        mode='lines+markers',
                        name='Network In (MB)',
                        line=dict(color='green')
                    ))
                if not df_net_out.empty:
                    fig_net.add_trace(go.Scatter(
                        x=df_net_out['Timestamp'],
                        y=df_net_out['Sum'] / (1024*1024),  # Convert to MB
                        mode='lines+markers',
                        name='Network Out (MB)',
                        line=dict(color='orange')
                    ))
                
                fig_net.update_layout(
                    title='Network Traffic Over Time',
                    xaxis_title='Time',
                    yaxis_title='Traffic (MB)',
                    height=400
                )
                st.plotly_chart(fig_net, use_container_width=True)
            else:
                st.info('No network data available for this instance')
    
    # Local system metrics (if running on EC2)
    st.header('🖥️ Local System Metrics (Current Instance)')
    local_metrics = dashboard.get_local_system_metrics()
    
    if local_metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                'Memory Usage',
                f"{local_metrics['memory']['percent']:.1f}%",
                f"{local_metrics['memory']['used'] / (1024**3):.1f}GB / {local_metrics['memory']['total'] / (1024**3):.1f}GB"
            )
        
        with col2:
            st.metric(
                'Swap Usage',
                f"{local_metrics['swap']['percent']:.1f}%",
                f"{local_metrics['swap']['used'] / (1024**3):.1f}GB / {local_metrics['swap']['total'] / (1024**3):.1f}GB"
            )
        
        with col3:
            st.metric(
                'Disk Usage',
                f"{local_metrics['disk']['percent']:.1f}%",
                f"{local_metrics['disk']['used'] / (1024**3):.1f}GB / {local_metrics['disk']['total'] / (1024**3):.1f}GB"
            )
        
        with col4:
            st.metric(
                'CPU Usage',
                f"{local_metrics['cpu']['percent']:.1f}%",
                f"Load: {local_metrics['cpu']['load_avg'][0]:.2f}"
            )
        
        # Memory and disk usage charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Memory usage pie chart
            fig_mem = go.Figure(data=[go.Pie(
                labels=['Used', 'Free'],
                values=[local_metrics['memory']['used'], local_metrics['memory']['free']],
                hole=0.3,
                marker_colors=['#ff6b6b', '#51cf66']
            )])
            fig_mem.update_layout(title='Memory Usage Distribution', height=300)
            st.plotly_chart(fig_mem, use_container_width=True)
        
        with col2:
            # Disk usage pie chart
            fig_disk = go.Figure(data=[go.Pie(
                labels=['Used', 'Free'],
                values=[local_metrics['disk']['used'], local_metrics['disk']['free']],
                hole=0.3,
                marker_colors=['#ffa726', '#66bb6a']
            )])
            fig_disk.update_layout(title='Disk Usage Distribution', height=300)
            st.plotly_chart(fig_disk, use_container_width=True)
    
    # Cost estimation
    st.header('💰 Cost Estimation')
    running_count = len(running_instances)
    stopped_count = len(instances) - running_count
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Running Instances', running_count, f'${running_count * 8.5:.2f}/month')
    with col2:
        st.metric('Stopped Instances', stopped_count, f'${stopped_count * 0.8:.2f}/month (storage only)')
    with col3:
        total_cost = (running_count * 8.5) + (stopped_count * 0.8)
        st.metric('Total Estimated Cost', f'${total_cost:.2f}/month')
    
    # Footer
    st.markdown('---')
    st.markdown(f'**Last updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}')
    st.markdown('**Region:** ap-south-1 | **Auto-refresh:** Enabled')

if __name__ == '__main__':
    main()
