"""
Demo mode for AWS CloudWatch Log Analyzer.
Provides sample data when AWS credentials are not available.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import numpy as np

from src.components.charts import ChartFactory, LambdaCharts, EC2Charts
from src.components.ui_components import UIComponents
from src.config.settings import app_config


class DemoDataGenerator:
    """Generate realistic demo data for testing."""
    
    @staticmethod
    def generate_lambda_log_groups():
        """Generate sample Lambda log groups."""
        return [
            {'name': '/aws/lambda/user-authentication', 'creation_time': 1234567890, 'size_bytes': 1024000},
            {'name': '/aws/lambda/data-processor', 'creation_time': 1234567891, 'size_bytes': 2048000},
            {'name': '/aws/lambda/email-service', 'creation_time': 1234567892, 'size_bytes': 512000},
            {'name': '/aws/lambda/image-resizer', 'creation_time': 1234567893, 'size_bytes': 3072000},
            {'name': '/aws/lambda/payment-handler', 'creation_time': 1234567894, 'size_bytes': 1536000}
        ]
    
    @staticmethod
    def generate_ec2_instances():
        """Generate sample EC2 instances."""
        return [
            {'id': 'i-1234567890abcdef0', 'name': 'Web Server 1', 'type': 't3.medium', 'state': 'running'},
            {'id': 'i-0987654321fedcba0', 'name': 'Database Server', 'type': 't3.large', 'state': 'running'},
            {'id': 'i-abcdef1234567890', 'name': 'API Gateway', 'type': 't3.small', 'state': 'running'},
            {'id': 'i-fedcba0987654321', 'name': 'Cache Server', 'type': 't3.micro', 'state': 'running'}
        ]
    
    @staticmethod
    def generate_lambda_metrics():
        """Generate sample Lambda metrics."""
        now = datetime.now()
        timestamps = [now - timedelta(minutes=i*5) for i in range(24, 0, -1)]
        
        return {
            'total_invocations': 1250,
            'errors': 23,
            'timeouts': 2,
            'durations': [random.uniform(100, 500) for _ in range(50)],
            'memory_usage': [random.randint(128, 512) for _ in range(50)],
            'cold_starts': 8,
            'error_messages': [
                {'timestamp': now - timedelta(minutes=15), 'message': 'ERROR: Database connection timeout'},
                {'timestamp': now - timedelta(minutes=45), 'message': 'ERROR: Invalid JSON payload'},
                {'timestamp': now - timedelta(hours=2), 'message': 'ERROR: Memory limit exceeded'}
            ]
        }
    
    @staticmethod
    def generate_ec2_metrics():
        """Generate sample EC2 metrics."""
        now = datetime.now()
        timestamps = [now - timedelta(minutes=i*5) for i in range(24, 0, -1)]
        
        # Generate realistic CPU data with some variation
        base_cpu = 45
        cpu_values = [max(0, min(100, base_cpu + random.gauss(0, 15))) for _ in timestamps]
        
        # Generate network data
        base_network_in = 1024 * 1024 * 10  # 10 MB
        network_in_values = [max(0, base_network_in + random.gauss(0, base_network_in * 0.3)) for _ in timestamps]
        
        base_network_out = 1024 * 1024 * 5  # 5 MB
        network_out_values = [max(0, base_network_out + random.gauss(0, base_network_out * 0.3)) for _ in timestamps]
        
        return {
            'cpuutilization': pd.DataFrame({
                'timestamp': timestamps,
                'value': cpu_values
            }),
            'networkin': pd.DataFrame({
                'timestamp': timestamps,
                'value': network_in_values
            }),
            'networkout': pd.DataFrame({
                'timestamp': timestamps,
                'value': network_out_values
            })
        }


class DemoApp:
    """Demo version of the CloudWatch Analyzer."""
    
    def __init__(self):
        self.ui = UIComponents()
        self.chart_factory = ChartFactory()
        self.lambda_charts = LambdaCharts()
        self.ec2_charts = EC2Charts()
        self.demo_data = DemoDataGenerator()
    
    def run(self):
        """Run the demo application."""
        self._configure_page()
        self._render_demo_interface()
    
    def _configure_page(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=f"{app_config.title} - Demo Mode",
            page_icon=app_config.page_icon,
            layout=app_config.layout,
            initial_sidebar_state="expanded"
        )
    
    def _render_demo_interface(self):
        """Render the demo interface."""
        # Header with demo notice
        st.title(f"🎯 {app_config.title} - Demo Mode")
        st.info("🚀 **Demo Mode Active** - Using sample data. Configure AWS credentials to analyze real resources.")
        st.markdown("---")
        
        # Sidebar
        st.sidebar.header("🔧 Demo Configuration")
        st.sidebar.info("This is a demonstration with sample data")
        
        analysis_type = st.sidebar.selectbox(
            "Select Analysis Type",
            ["Lambda Function Analysis", "EC2 Performance Monitoring"],
            help="Choose the type of analysis to demonstrate"
        )
        
        time_range = st.sidebar.selectbox(
            "Time Range",
            ["Last Hour", "Last 6 Hours", "Last 24 Hours"],
            index=2
        )
        
        # Main content
        if analysis_type == "Lambda Function Analysis":
            self._render_lambda_demo()
        else:
            self._render_ec2_demo()
    
    def _render_lambda_demo(self):
        """Render Lambda function demo."""
        st.header("🚀 Lambda Function Analysis - Demo")
        
        # Function selector
        lambda_functions = self.demo_data.generate_lambda_log_groups()
        function_names = [f['name'].replace('/aws/lambda/', '') for f in lambda_functions]
        
        selected_function = st.selectbox(
            "Select Lambda Function",
            function_names,
            help="Choose a Lambda function to analyze"
        )
        
        st.subheader(f"Analysis for: {selected_function}")
        
        # Generate demo metrics
        metrics = self.demo_data.generate_lambda_metrics()
        
        # Key metrics
        error_rate = (metrics['errors'] / metrics['total_invocations']) * 100
        avg_duration = np.mean(metrics['durations'])
        
        key_metrics = {
            'Total Invocations': metrics['total_invocations'],
            'Error Rate (%)': round(error_rate, 2),
            'Avg Duration (ms)': round(avg_duration, 2),
            'Cold Starts': metrics['cold_starts']
        }
        
        self.ui.render_metric_cards(key_metrics)
        
        # Charts
        st.subheader("📊 Performance Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Duration distribution
            duration_chart = self.lambda_charts.create_duration_distribution(metrics['durations'])
            st.plotly_chart(duration_chart, use_container_width=True)
        
        with col2:
            # Memory usage
            memory_chart = self.lambda_charts.create_memory_usage_chart(metrics['memory_usage'])
            st.plotly_chart(memory_chart, use_container_width=True)
        
        # Error analysis
        if metrics['error_messages']:
            st.subheader("🚨 Recent Errors")
            error_df = pd.DataFrame(metrics['error_messages'])
            st.dataframe(error_df, use_container_width=True)
        
        # Performance stats
        st.subheader("📈 Performance Statistics")
        perf_stats = {
            'Average Duration (ms)': round(np.mean(metrics['durations']), 2),
            'Min Duration (ms)': round(np.min(metrics['durations']), 2),
            'Max Duration (ms)': round(np.max(metrics['durations']), 2),
            'P95 Duration (ms)': round(np.percentile(metrics['durations'], 95), 2),
            'P99 Duration (ms)': round(np.percentile(metrics['durations'], 99), 2)
        }
        
        perf_df = pd.DataFrame([perf_stats])
        st.dataframe(perf_df, use_container_width=True)
    
    def _render_ec2_demo(self):
        """Render EC2 performance demo."""
        st.header("🖥️ EC2 Performance Monitoring - Demo")
        
        # Instance selector
        ec2_instances = self.demo_data.generate_ec2_instances()
        instance_options = [f"{inst['name']} ({inst['id']})" for inst in ec2_instances]
        
        selected_idx = st.selectbox(
            "Select EC2 Instance",
            range(len(instance_options)),
            format_func=lambda x: instance_options[x],
            help="Choose an EC2 instance to analyze"
        )
        
        selected_instance = ec2_instances[selected_idx]
        st.subheader(f"Analysis for: {selected_instance['name']} ({selected_instance['id']})")
        
        # Generate demo metrics
        metrics_data = self.demo_data.generate_ec2_metrics()
        
        # Key metrics
        current_cpu = metrics_data['cpuutilization']['value'].iloc[-1]
        current_network_in = metrics_data['networkin']['value'].iloc[-1] / (1024 * 1024)  # MB
        current_network_out = metrics_data['networkout']['value'].iloc[-1] / (1024 * 1024)  # MB
        
        key_metrics = {
            'CPU Utilization (%)': round(current_cpu, 1),
            'Network In (MB)': round(current_network_in, 1),
            'Network Out (MB)': round(current_network_out, 1),
            'Instance State': selected_instance['state'].title()
        }
        
        self.ui.render_metric_cards(key_metrics)
        
        # Charts
        st.subheader("📊 Performance Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU utilization
            cpu_chart = self.ec2_charts.create_cpu_utilization_chart(metrics_data['cpuutilization'])
            st.plotly_chart(cpu_chart, use_container_width=True)
        
        with col2:
            # Network I/O
            network_chart = self.ec2_charts.create_network_io_chart(
                metrics_data['networkin'], 
                metrics_data['networkout']
            )
            st.plotly_chart(network_chart, use_container_width=True)
        
        # Resource overview
        st.subheader("🎯 Resource Overview")
        overview_data = {
            'CPU': current_cpu,
            'Network Activity': min((current_network_in + current_network_out) / 10, 100)
        }
        
        overview_chart = self.ec2_charts.create_resource_overview_chart(overview_data)
        st.plotly_chart(overview_chart, use_container_width=True)
        
        # Anomaly detection
        st.subheader("🔍 Anomaly Detection")
        
        # Simple anomaly detection for demo
        cpu_values = metrics_data['cpuutilization']['value']
        cpu_mean = cpu_values.mean()
        cpu_std = cpu_values.std()
        anomalies = cpu_values[cpu_values > cpu_mean + 2 * cpu_std]
        
        if len(anomalies) > 0:
            st.warning(f"Found {len(anomalies)} CPU utilization anomalies")
            anomaly_data = []
            for idx, value in anomalies.items():
                anomaly_data.append({
                    'timestamp': metrics_data['cpuutilization']['timestamp'].iloc[idx],
                    'cpu_value': round(value, 2),
                    'threshold': round(cpu_mean + 2 * cpu_std, 2)
                })
            
            anomaly_df = pd.DataFrame(anomaly_data)
            st.dataframe(anomaly_df, use_container_width=True)
        else:
            st.success("No anomalies detected in the selected time range")


def main():
    """Run the demo application."""
    demo_app = DemoApp()
    demo_app.run()


if __name__ == "__main__":
    main()
