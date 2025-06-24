"""
Main Streamlit application for AWS CloudWatch Log Analyzer.
Entry point that orchestrates all components following the MVC pattern.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

# Import application components
from src.config.settings import app_config
from src.services.cloudwatch_service import CloudWatchLogsService, CloudWatchMetricsService
from src.utils.data_processor import LogProcessor, MetricProcessor
from src.components.ui_components import UIComponents, NavigationComponents
from src.components.charts import ChartFactory, LambdaCharts, EC2Charts
from src.utils.aws_client import aws_client_manager


class CloudWatchAnalyzerApp:
    """Main application class following the Controller pattern."""
    
    def __init__(self):
        self.logs_service = CloudWatchLogsService()
        self.metrics_service = CloudWatchMetricsService()
        self.log_processor = LogProcessor()
        self.metric_processor = MetricProcessor()
        self.ui = UIComponents()
        self.nav = NavigationComponents()
    
    def run(self):
        """Main application entry point."""
        self._configure_page()
        self._check_aws_connection()
        self._render_main_interface()
    
    def _configure_page(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=app_config.title,
            page_icon=app_config.page_icon,
            layout=app_config.layout,
            initial_sidebar_state="expanded"
        )
    
    def _check_aws_connection(self):
        """Check AWS connection and display status."""
        if not aws_client_manager.test_connection():
            st.error("❌ Unable to connect to AWS. Please check your credentials.")
            st.info("""
            **Setup Instructions:**
            1. Configure AWS CLI: `aws configure`
            2. Or set environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
            3. Or use IAM roles if running on EC2
            """)
            st.stop()
        else:
            st.success("✅ Connected to AWS successfully")
    
    def _render_main_interface(self):
        """Render the main application interface."""
        # Header
        self.ui.render_header(
            app_config.title,
            "Analyze Lambda functions and EC2 performance with interactive dashboards"
        )
        
        # Sidebar filters
        filters = self.ui.render_sidebar_filters()
        
        # Main navigation
        analysis_types = ["Lambda Function Analysis", "EC2 Performance Monitoring"]
        selected_analysis = self.nav.render_tab_navigation(analysis_types)
        
        # Render selected analysis
        if selected_analysis == "Lambda Function Analysis":
            self._render_lambda_analysis(filters)
        elif selected_analysis == "EC2 Performance Monitoring":
            self._render_ec2_analysis(filters)
    
    def _render_lambda_analysis(self, filters: Dict[str, Any]):
        """Render Lambda function analysis interface."""
        st.header("🚀 Lambda Function Analysis")
        
        # Get Lambda log groups
        with st.spinner("Loading Lambda functions..."):
            lambda_log_groups = self.logs_service.get_lambda_log_groups()
        
        if not lambda_log_groups:
            st.warning("No Lambda function log groups found")
            return
        
        # Resource selector
        selected_function = self.nav.render_resource_selector(
            lambda_log_groups, "Lambda Function"
        )
        
        if not selected_function:
            return
        
        function_name = selected_function['name'].replace('/aws/lambda/', '')
        st.subheader(f"Analysis for: {function_name}")
        
        # Load and process data
        with st.spinner("Analyzing Lambda function logs..."):
            log_events = self.logs_service.get_log_events(
                selected_function['name'],
                filters['time_range_hours']
            )
            
            if log_events:
                metrics = self.log_processor.extract_lambda_metrics(log_events)
                self._display_lambda_metrics(metrics, function_name, filters)
            else:
                st.info("No log events found for the selected time range")
    
    def _display_lambda_metrics(self, metrics: Dict[str, Any], function_name: str, filters: Dict[str, Any]):
        """Display Lambda function metrics and charts."""
        # Key metrics cards
        error_rate = self.log_processor.calculate_error_rate(
            metrics['total_invocations'], metrics['errors']
        )
        
        perf_stats = self.log_processor.get_performance_stats(metrics['durations'])
        
        key_metrics = {
            'Total Invocations': metrics['total_invocations'],
            'Error Rate (%)': error_rate,
            'Avg Duration (ms)': perf_stats['avg'],
            'Cold Starts': metrics['cold_starts']
        }
        
        self.ui.render_metric_cards(key_metrics)
        
        # Charts section
        st.subheader("📊 Performance Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Duration distribution
            duration_chart = LambdaCharts.create_duration_distribution(metrics['durations'])
            st.plotly_chart(duration_chart, use_container_width=True)
        
        with col2:
            # Memory usage
            memory_chart = LambdaCharts.create_memory_usage_chart(metrics['memory_usage'])
            st.plotly_chart(memory_chart, use_container_width=True)
        
        # Error analysis
        if metrics['error_messages']:
            st.subheader("🚨 Recent Errors")
            self.ui.render_data_table(
                metrics['error_messages'][:10],
                "Error Messages",
                max_rows=5
            )
        
        # Performance statistics
        st.subheader("📈 Performance Statistics")
        perf_df = pd.DataFrame([perf_stats])
        st.dataframe(perf_df, use_container_width=True)
        
        # Export functionality
        export_data = {
            'function_name': function_name,
            'time_range': filters['time_range_label'],
            'metrics': key_metrics,
            'performance_stats': perf_stats
        }
        
        self.ui.render_export_button(
            export_data,
            f"lambda_analysis_{function_name}",
            "json"
        )
    
    def _render_ec2_analysis(self, filters: Dict[str, Any]):
        """Render EC2 performance analysis interface."""
        st.header("🖥️ EC2 Performance Monitoring")
        
        # Get EC2 instances
        with st.spinner("Loading EC2 instances..."):
            ec2_instances = self.metrics_service.get_ec2_instances()
        
        if not ec2_instances:
            st.warning("No EC2 instances found")
            return
        
        # Resource selector
        selected_instance = self.nav.render_resource_selector(
            ec2_instances, "EC2 Instance"
        )
        
        if not selected_instance:
            return
        
        st.subheader(f"Analysis for: {selected_instance['name']} ({selected_instance['id']})")
        
        # Load and process metrics
        with st.spinner("Loading EC2 metrics..."):
            ec2_metrics = self.metrics_service.get_ec2_metrics(
                selected_instance['id'],
                filters['time_range_hours']
            )
            
            self._display_ec2_metrics(ec2_metrics, selected_instance, filters)
    
    def _display_ec2_metrics(self, metrics: Dict[str, Any], instance: Dict[str, str], filters: Dict[str, Any]):
        """Display EC2 metrics and charts."""
        # Process metric data
        processed_metrics = {}
        current_values = {}
        
        for metric_name, metric_data in metrics.items():
            df = self.metric_processor.process_metric_data(metric_data)
            processed_metrics[metric_name] = df
            
            if not df.empty:
                stats = self.metric_processor.calculate_metric_stats(df)
                current_values[metric_name] = stats['current']
        
        # Key metrics cards
        key_metrics = {
            'CPU Utilization (%)': current_values.get('cpuutilization', 0),
            'Network In (MB)': current_values.get('networkin', 0) / (1024 * 1024),
            'Network Out (MB)': current_values.get('networkout', 0) / (1024 * 1024),
            'Instance State': instance['state'].title()
        }
        
        self.ui.render_metric_cards(key_metrics)
        
        # Charts section
        st.subheader("📊 Performance Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU utilization
            if 'cpuutilization' in processed_metrics:
                cpu_chart = EC2Charts.create_cpu_utilization_chart(
                    processed_metrics['cpuutilization']
                )
                st.plotly_chart(cpu_chart, use_container_width=True)
        
        with col2:
            # Network I/O
            network_chart = EC2Charts.create_network_io_chart(
                processed_metrics.get('networkin', pd.DataFrame()),
                processed_metrics.get('networkout', pd.DataFrame())
            )
            st.plotly_chart(network_chart, use_container_width=True)
        
        # Resource overview
        if current_values:
            st.subheader("🎯 Resource Overview")
            
            # Create resource overview data (normalize to percentages)
            overview_data = {
                'CPU': current_values.get('cpuutilization', 0),
                'Network Activity': min(
                    (current_values.get('networkin', 0) + current_values.get('networkout', 0)) / (1024 * 1024 * 10),
                    100
                )  # Normalize network to 0-100 scale
            }
            
            overview_chart = EC2Charts.create_resource_overview_chart(overview_data)
            st.plotly_chart(overview_chart, use_container_width=True)
        
        # Anomaly detection
        st.subheader("🔍 Anomaly Detection")
        anomalies_found = False
        
        for metric_name, df in processed_metrics.items():
            if not df.empty:
                anomalies = self.metric_processor.detect_anomalies(df)
                if anomalies:
                    anomalies_found = True
                    st.warning(f"Found {len(anomalies)} anomalies in {metric_name}")
                    self.ui.render_data_table(
                        anomalies,
                        f"{metric_name.title()} Anomalies",
                        max_rows=3
                    )
        
        if not anomalies_found:
            st.success("No anomalies detected in the selected time range")
        
        # Export functionality
        export_data = {
            'instance_id': instance['id'],
            'instance_name': instance['name'],
            'time_range': filters['time_range_label'],
            'current_metrics': key_metrics
        }
        
        self.ui.render_export_button(
            export_data,
            f"ec2_analysis_{instance['id']}",
            "json"
        )


def main():
    """Application entry point."""
    app = CloudWatchAnalyzerApp()
    app.run()


if __name__ == "__main__":
    main()
