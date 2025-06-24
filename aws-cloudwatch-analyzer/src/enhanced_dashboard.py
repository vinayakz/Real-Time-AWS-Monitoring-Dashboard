import streamlit as st
import boto3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import psutil
import json
import logging

# Page configuration
st.set_page_config(
    page_title='AWS Dashboard - AP-South-1',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .cost-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .log-container {
        background: #1e1e1e;
        color: #00ff00;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

class EnhancedAWSDashboard:
    def __init__(self):
        self.region = 'ap-south-1'
        self.ec2_client = boto3.client('ec2', region_name=self.region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.logs_client = boto3.client('logs', region_name=self.region)
        
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
    
    def get_lambda_functions(self):
        """Get Lambda functions"""
        try:
            response = self.lambda_client.list_functions()
            functions = []
            
            for func in response['Functions']:
                functions.append({
                    'FunctionName': func['FunctionName'],
                    'Runtime': func['Runtime'],
                    'MemorySize': func['MemorySize'],
                    'Timeout': func['Timeout'],
                    'LastModified': func['LastModified'],
                    'CodeSize': func['CodeSize'],
                    'Handler': func['Handler']
                })
            return functions
        except Exception as e:
            st.error(f'Error fetching Lambda functions: {str(e)}')
            return []
    
    def get_lambda_logs(self, function_name, limit=50):
        """Get Lambda function logs"""
        try:
            log_group_name = f"/aws/lambda/{function_name}"
            
            # Get recent log streams
            streams_response = self.logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=True,
                limit=3
            )
            
            logs = []
            for stream in streams_response['logStreams']:
                try:
                    events_response = self.logs_client.get_log_events(
                        logGroupName=log_group_name,
                        logStreamName=stream['logStreamName'],
                        limit=limit,
                        startFromHead=False
                    )
                    
                    for event in events_response['events']:
                        logs.append({
                            'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                            'message': event['message'].strip()
                        })
                except:
                    continue
            
            return sorted(logs, key=lambda x: x['timestamp'], reverse=True)[:limit]
            
        except Exception as e:
            st.error(f'Error fetching Lambda logs: {str(e)}')
            return []
    
    def get_lambda_metrics(self, function_name):
        """Get Lambda function metrics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            # Invocations
            invocations = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Errors
            errors = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            # Duration
            duration = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            return {
                'invocations': sorted(invocations['Datapoints'], key=lambda x: x['Timestamp']),
                'errors': sorted(errors['Datapoints'], key=lambda x: x['Timestamp']),
                'duration': sorted(duration['Datapoints'], key=lambda x: x['Timestamp'])
            }
            
        except Exception as e:
            st.error(f'Error fetching Lambda metrics: {str(e)}')
            return {'invocations': [], 'errors': [], 'duration': []}
    
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
    
    def calculate_cost_analysis(self, instances, functions):
        """Calculate comprehensive cost analysis"""
        cost_analysis = {
            'total_monthly_estimate': 0,
            'service_breakdown': {},
            'recommendations': []
        }
        
        # EC2 Cost Calculation
        ec2_cost = 0
        instance_costs = {}
        
        # AP-South-1 pricing (hourly rates in USD)
        hourly_rates = {
            't2.micro': 0.0116, 't2.small': 0.0232, 't2.medium': 0.0464,
            't3.micro': 0.0116, 't3.small': 0.0232, 't3.medium': 0.0464,
            't3.large': 0.0928, 't3.xlarge': 0.1856, 't3.2xlarge': 0.3712,
            'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
            'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34
        }
        
        for instance in instances:
            if instance['State'] == 'running':
                instance_type = instance['InstanceType']
                hourly_rate = hourly_rates.get(instance_type, 0.05)
                monthly_cost = hourly_rate * 720  # 30 days * 24 hours
                
                instance_costs[instance['InstanceId']] = {
                    'name': instance['Name'],
                    'type': instance_type,
                    'hourly_rate': hourly_rate,
                    'monthly_cost': monthly_cost
                }
                ec2_cost += monthly_cost
        
        cost_analysis['service_breakdown']['EC2'] = ec2_cost
        cost_analysis['instance_details'] = instance_costs
        
        # Lambda Cost Calculation (estimated)
        lambda_cost = 0
        function_costs = {}
        
        for func in functions:
            memory_mb = func['MemorySize']
            estimated_requests = 50000  # per month
            avg_duration_ms = 1000
            
            # Lambda pricing for AP-South-1
            request_cost = (estimated_requests / 1_000_000) * 0.20
            gb_seconds = (estimated_requests * avg_duration_ms / 1000) * (memory_mb / 1024)
            compute_cost = gb_seconds * 0.0000166667
            
            total_func_cost = request_cost + compute_cost
            
            function_costs[func['FunctionName']] = {
                'memory_mb': memory_mb,
                'estimated_requests': estimated_requests,
                'total_cost': total_func_cost
            }
            lambda_cost += total_func_cost
        
        cost_analysis['service_breakdown']['Lambda'] = lambda_cost
        cost_analysis['function_details'] = function_costs
        
        # Add other estimated costs
        cost_analysis['service_breakdown']['EBS Storage'] = 20.0
        cost_analysis['service_breakdown']['Data Transfer'] = 5.0
        cost_analysis['service_breakdown']['CloudWatch'] = 3.0
        
        # Calculate total
        cost_analysis['total_monthly_estimate'] = sum(cost_analysis['service_breakdown'].values())
        
        # Generate recommendations
        cost_analysis['recommendations'] = [
            {
                'type': 'immediate',
                'title': 'Right-size EC2 instances',
                'description': 'Monitor CPU utilization and downsize underutilized instances',
                'potential_savings': '$15-30/month'
            },
            {
                'type': 'immediate',
                'title': 'Optimize Lambda memory allocation',
                'description': 'Adjust Lambda function memory based on actual usage patterns',
                'potential_savings': '$5-10/month'
            },
            {
                'type': 'medium_term',
                'title': 'Consider Reserved Instances',
                'description': 'For stable workloads, Reserved Instances can save up to 75%',
                'potential_savings': f'${ec2_cost * 0.4:.0f}/month'
            },
            {
                'type': 'long_term',
                'title': 'Implement auto-scaling',
                'description': 'Use auto-scaling groups to optimize resource usage',
                'potential_savings': '$20-50/month'
            }
        ]
        
        return cost_analysis

def render_cost_analysis(dashboard, instances, functions):
    """Render cost analysis section"""
    st.header('💰 Cost Analysis')
    
    cost_data = dashboard.calculate_cost_analysis(instances, functions)
    
    # Cost overview cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="cost-card">
            <h3>${cost_data['total_monthly_estimate']:.2f}</h3>
            <p>Total Monthly Cost</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="cost-card">
            <h3>${cost_data['service_breakdown'].get('EC2', 0):.2f}</h3>
            <p>EC2 Instances</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="cost-card">
            <h3>${cost_data['service_breakdown'].get('Lambda', 0):.2f}</h3>
            <p>Lambda Functions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="cost-card">
            <h3>${cost_data['service_breakdown'].get('EBS Storage', 0):.2f}</h3>
            <p>Storage & Others</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Cost breakdown chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('📊 Cost Breakdown by Service')
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(cost_data['service_breakdown'].keys()),
            values=list(cost_data['service_breakdown'].values()),
            hole=0.3,
            marker_colors=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']
        )])
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader('💡 Cost Optimization Recommendations')
        for rec in cost_data['recommendations']:
            with st.expander(f"{rec['title']} - {rec['potential_savings']}"):
                st.write(f"**Type:** {rec['type'].title()}")
                st.write(f"**Description:** {rec['description']}")
                st.write(f"**Potential Savings:** {rec['potential_savings']}")
    
    # Detailed cost breakdown
    st.subheader('📋 Detailed Cost Breakdown')
    
    # EC2 instances
    if cost_data.get('instance_details'):
        st.write("**EC2 Instances:**")
        ec2_df = pd.DataFrame([
            {
                'Instance ID': k,
                'Name': v['name'],
                'Type': v['type'],
                'Hourly Rate': f"${v['hourly_rate']:.4f}",
                'Monthly Cost': f"${v['monthly_cost']:.2f}"
            }
            for k, v in cost_data['instance_details'].items()
        ])
        st.dataframe(ec2_df, use_container_width=True)
    
    # Lambda functions
    if cost_data.get('function_details'):
        st.write("**Lambda Functions:**")
        lambda_df = pd.DataFrame([
            {
                'Function Name': k,
                'Memory (MB)': v['memory_mb'],
                'Est. Requests/Month': f"{v['estimated_requests']:,}",
                'Monthly Cost': f"${v['total_cost']:.2f}"
            }
            for k, v in cost_data['function_details'].items()
        ])
        st.dataframe(lambda_df, use_container_width=True)

def render_ec2_realtime(dashboard, instances):
    """Render EC2 real-time monitoring section"""
    st.header('🖥️ EC2 Real-time Monitoring')
    
    if not instances:
        st.error('No EC2 instances found')
        return
    
    # Instance overview cards
    st.subheader('📊 Instance Overview')
    cols = st.columns(min(len(instances), 4))
    
    for i, instance in enumerate(instances[:4]):  # Show max 4 cards
        with cols[i]:
            status_color = '🟢' if instance['State'] == 'running' else '🔴'
            st.markdown(f"""
            <div class="metric-card">
                <h4>{status_color} {instance['Name']}</h4>
                <p><strong>Type:</strong> {instance['InstanceType']}</p>
                <p><strong>State:</strong> {instance['State']}</p>
                <p><strong>AZ:</strong> {instance['AZ']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Running instances metrics
    running_instances = [i for i in instances if i['State'] == 'running']
    
    if running_instances:
        st.subheader('📈 Real-time Metrics')
        
        # Instance selector
        selected_instance = st.selectbox(
            'Select instance for detailed metrics:',
            options=[f"{i['Name']} ({i['InstanceId']})" for i in running_instances],
            key='ec2_selector'
        )
        
        instance_id = selected_instance.split('(')[1].split(')')[0]
        
        # Get metrics
        cpu_data = dashboard.get_cpu_metrics(instance_id)
        
        # CPU metrics chart
        if cpu_data:
            st.subheader('💻 CPU Utilization (24h)')
            df_cpu = pd.DataFrame(cpu_data)
            
            fig_cpu = go.Figure()
            fig_cpu.add_trace(go.Scatter(
                x=df_cpu['Timestamp'],
                y=df_cpu['Average'],
                mode='lines+markers',
                name='Average CPU',
                line=dict(color='#667eea', width=3)
            ))
            fig_cpu.add_trace(go.Scatter(
                x=df_cpu['Timestamp'],
                y=df_cpu['Maximum'],
                mode='lines+markers',
                name='Max CPU',
                line=dict(color='#f5576c', width=2)
            ))
            fig_cpu.update_layout(
                title='CPU Utilization Over Time',
                xaxis_title='Time',
                yaxis_title='CPU %',
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig_cpu, use_container_width=True)
            
            # Current CPU status
            if df_cpu['Average'].iloc[-1] > 80:
                st.warning(f"⚠️ High CPU usage detected: {df_cpu['Average'].iloc[-1]:.1f}%")
            elif df_cpu['Average'].iloc[-1] < 10:
                st.info(f"💡 Low CPU usage: {df_cpu['Average'].iloc[-1]:.1f}% - Consider downsizing")
        else:
            st.info('No CPU data available for this instance')

def render_lambda_logs(dashboard, functions):
    """Render Lambda logs section"""
    st.header('📝 Lambda Function Logs')
    
    if not functions:
        st.error('No Lambda functions found')
        return
    
    # Function selector
    selected_function = st.selectbox(
        'Select Lambda function:',
        options=[f['FunctionName'] for f in functions],
        key='lambda_selector'
    )
    
    # Function details
    selected_func_details = next(f for f in functions if f['FunctionName'] == selected_function)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('Runtime', selected_func_details['Runtime'])
    with col2:
        st.metric('Memory', f"{selected_func_details['MemorySize']} MB")
    with col3:
        st.metric('Timeout', f"{selected_func_details['Timeout']} sec")
    with col4:
        st.metric('Code Size', f"{selected_func_details['CodeSize'] / 1024:.1f} KB")
    
    # Get logs and metrics
    logs = dashboard.get_lambda_logs(selected_function)
    metrics = dashboard.get_lambda_metrics(selected_function)
    
    # Metrics charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('📊 Invocations (24h)')
        if metrics['invocations']:
            df_inv = pd.DataFrame(metrics['invocations'])
            fig_inv = go.Figure()
            fig_inv.add_trace(go.Bar(
                x=df_inv['Timestamp'],
                y=df_inv['Sum'],
                name='Invocations',
                marker_color='#667eea'
            ))
            fig_inv.update_layout(
                title='Function Invocations',
                xaxis_title='Time',
                yaxis_title='Count',
                height=300
            )
            st.plotly_chart(fig_inv, use_container_width=True)
        else:
            st.info('No invocation data available')
    
    with col2:
        st.subheader('⚠️ Errors (24h)')
        if metrics['errors']:
            df_err = pd.DataFrame(metrics['errors'])
            total_errors = df_err['Sum'].sum()
            st.metric('Total Errors', int(total_errors))
            
            if total_errors > 0:
                fig_err = go.Figure()
                fig_err.add_trace(go.Bar(
                    x=df_err['Timestamp'],
                    y=df_err['Sum'],
                    name='Errors',
                    marker_color='#f5576c'
                ))
                fig_err.update_layout(
                    title='Function Errors',
                    xaxis_title='Time',
                    yaxis_title='Count',
                    height=300
                )
                st.plotly_chart(fig_err, use_container_width=True)
        else:
            st.success('No errors detected')
    
    # Recent logs
    st.subheader('📋 Recent Logs')
    if logs:
        log_text = "\n".join([f"[{log['timestamp']}] {log['message']}" for log in logs[:20]])
        st.markdown(f"""
        <div class="log-container">
            <pre>{log_text}</pre>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info('No recent logs available')

def main():
    dashboard = EnhancedAWSDashboard()
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 AWS Dashboard - AP-South-1</h1>
        <p>Real-time monitoring with Cost Analysis, EC2 Metrics, and Lambda Logs</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar controls
    st.sidebar.title('🎛️ Dashboard Controls')
    
    # Main section selector
    section = st.sidebar.selectbox(
        '📊 Select Dashboard Section:',
        ['Cost Analysis', 'EC2 Real-time', 'Lambda Logs', 'Overview'],
        index=0
    )
    
    # Auto-refresh controls
    st.sidebar.markdown('---')
    st.sidebar.subheader('🔄 Auto-refresh')
    auto_refresh = st.sidebar.checkbox('Enable auto-refresh', value=True)
    refresh_rate = st.sidebar.selectbox('Refresh rate (seconds)', [30, 60, 120, 300], index=1)
    
    if st.sidebar.button('🔄 Refresh Now'):
        st.rerun()
    
    # Get data
    with st.spinner('Loading AWS data...'):
        instances = dashboard.get_instance_data()
        functions = dashboard.get_lambda_functions()
    
    # Render selected section
    if section == 'Cost Analysis':
        render_cost_analysis(dashboard, instances, functions)
    elif section == 'EC2 Real-time':
        render_ec2_realtime(dashboard, instances)
    elif section == 'Lambda Logs':
        render_lambda_logs(dashboard, functions)
    elif section == 'Overview':
        st.header('📈 Infrastructure Overview')
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        running_instances = len([i for i in instances if i['State'] == 'running'])
        total_instances = len(instances)
        total_functions = len(functions)
        
        with col1:
            st.metric('Total EC2 Instances', total_instances, f'{running_instances} running')
        with col2:
            st.metric('Lambda Functions', total_functions)
        with col3:
            estimated_cost = dashboard.calculate_cost_analysis(instances, functions)['total_monthly_estimate']
            st.metric('Monthly Cost Estimate', f'${estimated_cost:.2f}')
        with col4:
            st.metric('Region', 'ap-south-1', 'Mumbai')
        
        # Quick charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Instance states
            state_counts = {}
            for instance in instances:
                state = instance['State']
                state_counts[state] = state_counts.get(state, 0) + 1
            
            if state_counts:
                fig_states = go.Figure(data=[go.Pie(
                    labels=list(state_counts.keys()),
                    values=list(state_counts.values()),
                    hole=0.3
                )])
                fig_states.update_layout(title='EC2 Instance States', height=300)
                st.plotly_chart(fig_states, use_container_width=True)
        
        with col2:
            # Function memory distribution
            if functions:
                memory_sizes = [f['MemorySize'] for f in functions]
                fig_memory = go.Figure(data=[go.Histogram(
                    x=memory_sizes,
                    nbinsx=10,
                    marker_color='#667eea'
                )])
                fig_memory.update_layout(
                    title='Lambda Memory Distribution',
                    xaxis_title='Memory (MB)',
                    yaxis_title='Count',
                    height=300
                )
                st.plotly_chart(fig_memory, use_container_width=True)
    
    # Footer
    st.markdown('---')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'**Last updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    with col2:
        st.markdown('**Region:** ap-south-1')
    with col3:
        st.markdown(f'**Auto-refresh:** {"Enabled" if auto_refresh else "Disabled"}')
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == '__main__':
    main()
