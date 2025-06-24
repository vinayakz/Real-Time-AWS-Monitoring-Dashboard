#!/usr/bin/env python3
"""
Demo script to showcase the AWS CloudWatch Log Analyzer functionality
without requiring actual AWS credentials.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.data_processor import LogProcessor, MetricProcessor, TimeRangeProcessor
from src.components.charts import ChartFactory, LambdaCharts, EC2Charts
import pandas as pd
from datetime import datetime, timedelta

def demo_log_processing():
    """Demonstrate log processing capabilities."""
    print("🔍 Demo: Log Processing")
    print("=" * 50)
    
    # Sample Lambda log events
    sample_logs = [
        {'message': 'START RequestId: 123-456-789', 'timestamp': 1234567890},
        {'message': 'Duration: 150.25 ms', 'timestamp': 1234567891},
        {'message': 'Max Memory Used: 128 MB', 'timestamp': 1234567892},
        {'message': 'ERROR Something went wrong', 'timestamp': 1234567893},
        {'message': 'INIT_START Runtime Version: python3.9', 'timestamp': 1234567894},
        {'message': 'START RequestId: 456-789-012', 'timestamp': 1234567895},
        {'message': 'Duration: 200.50 ms', 'timestamp': 1234567896},
        {'message': 'Max Memory Used: 256 MB', 'timestamp': 1234567897},
    ]
    
    processor = LogProcessor()
    metrics = processor.extract_lambda_metrics(sample_logs)
    
    print(f"📊 Extracted Metrics:")
    print(f"   Total Invocations: {metrics['total_invocations']}")
    print(f"   Errors: {metrics['errors']}")
    print(f"   Cold Starts: {metrics['cold_starts']}")
    print(f"   Average Duration: {sum(metrics['durations'])/len(metrics['durations']):.2f} ms")
    print(f"   Error Rate: {processor.calculate_error_rate(metrics['total_invocations'], metrics['errors']):.1f}%")
    
    perf_stats = processor.get_performance_stats(metrics['durations'])
    print(f"   Performance Stats: {perf_stats}")
    print()

def demo_metric_processing():
    """Demonstrate metric processing capabilities."""
    print("📈 Demo: Metric Processing")
    print("=" * 50)
    
    # Sample metric data
    sample_metrics = [
        {'Timestamp': datetime.now() - timedelta(minutes=30), 'Average': 45.2},
        {'Timestamp': datetime.now() - timedelta(minutes=25), 'Average': 52.1},
        {'Timestamp': datetime.now() - timedelta(minutes=20), 'Average': 48.7},
        {'Timestamp': datetime.now() - timedelta(minutes=15), 'Average': 61.3},
        {'Timestamp': datetime.now() - timedelta(minutes=10), 'Average': 55.8},
        {'Timestamp': datetime.now() - timedelta(minutes=5), 'Average': 49.2},
        {'Timestamp': datetime.now(), 'Average': 53.5},
    ]
    
    processor = MetricProcessor()
    df = processor.process_metric_data(sample_metrics)
    
    print(f"📊 Processed {len(df)} metric data points")
    print(f"   Data shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    
    stats = processor.calculate_metric_stats(df)
    print(f"   Statistics: {stats}")
    
    anomalies = processor.detect_anomalies(df)
    print(f"   Anomalies detected: {len(anomalies)}")
    print()

def demo_time_processing():
    """Demonstrate time range processing."""
    print("⏰ Demo: Time Range Processing")
    print("=" * 50)
    
    processor = TimeRangeProcessor()
    
    # Test different time ranges
    for hours in [1, 6, 24, 168]:  # 1 hour, 6 hours, 1 day, 1 week
        start_time, end_time = processor.get_time_range(hours)
        formatted_start = processor.format_timestamp(start_time)
        formatted_end = processor.format_timestamp(end_time)
        
        print(f"   {hours:3d} hours: {formatted_start} to {formatted_end}")
    
    # Test time buckets
    start_time, end_time = processor.get_time_range(12)  # 12 hours
    buckets = processor.get_time_buckets(start_time, end_time, 6)  # 6 buckets
    print(f"   Time buckets (6): {len(buckets)} intervals")
    print()

def demo_chart_creation():
    """Demonstrate chart creation (without rendering)."""
    print("📊 Demo: Chart Creation")
    print("=" * 50)
    
    # Create sample data
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=10, freq='1H'),
        'value': [45, 52, 48, 61, 55, 49, 53, 58, 44, 50]
    })
    
    factory = ChartFactory()
    
    # Test different chart types
    charts_created = []
    
    try:
        # Time series chart
        ts_chart = factory.create_time_series_chart(df, "CPU Utilization", "CPU %")
        charts_created.append("Time Series Chart")
        
        # Bar chart
        bar_data = {'CPU': 55.2, 'Memory': 67.8, 'Disk': 23.4}
        bar_chart = factory.create_bar_chart(bar_data, "Resource Usage")
        charts_created.append("Bar Chart")
        
        # Pie chart
        pie_data = {'Success': 85, 'Error': 10, 'Timeout': 5}
        pie_chart = factory.create_pie_chart(pie_data, "Request Status")
        charts_created.append("Pie Chart")
        
        # Gauge chart
        gauge_chart = factory.create_gauge_chart(75.5, "CPU Usage", 100)
        charts_created.append("Gauge Chart")
        
        print(f"   ✅ Successfully created {len(charts_created)} chart types:")
        for chart_type in charts_created:
            print(f"      - {chart_type}")
        
    except Exception as e:
        print(f"   ❌ Error creating charts: {e}")
    
    print()

def demo_lambda_charts():
    """Demonstrate Lambda-specific charts."""
    print("🚀 Demo: Lambda Charts")
    print("=" * 50)
    
    lambda_charts = LambdaCharts()
    
    try:
        # Duration distribution
        durations = [120, 150, 180, 145, 200, 175, 160, 190, 155, 170]
        duration_chart = lambda_charts.create_duration_distribution(durations)
        print("   ✅ Duration distribution chart created")
        
        # Memory usage chart
        memory_usage = [128, 135, 142, 138, 145, 140, 133, 148, 136, 141]
        memory_chart = lambda_charts.create_memory_usage_chart(memory_usage)
        print("   ✅ Memory usage chart created")
        
    except Exception as e:
        print(f"   ❌ Error creating Lambda charts: {e}")
    
    print()

def demo_ec2_charts():
    """Demonstrate EC2-specific charts."""
    print("🖥️ Demo: EC2 Charts")
    print("=" * 50)
    
    ec2_charts = EC2Charts()
    
    try:
        # CPU utilization chart
        cpu_df = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=10, freq='5min'),
            'value': [45, 52, 48, 61, 55, 49, 53, 58, 44, 50]
        })
        cpu_chart = ec2_charts.create_cpu_utilization_chart(cpu_df)
        print("   ✅ CPU utilization chart created")
        
        # Network I/O chart
        network_in_df = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=10, freq='5min'),
            'value': [1024000, 1536000, 2048000, 1792000, 1280000, 1600000, 1920000, 1408000, 1152000, 1344000]
        })
        network_out_df = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=10, freq='5min'),
            'value': [512000, 768000, 1024000, 896000, 640000, 800000, 960000, 704000, 576000, 672000]
        })
        network_chart = ec2_charts.create_network_io_chart(network_in_df, network_out_df)
        print("   ✅ Network I/O chart created")
        
        # Resource overview chart
        resource_data = {'CPU': 55.2, 'Memory': 67.8, 'Network': 23.4, 'Disk': 45.6}
        overview_chart = ec2_charts.create_resource_overview_chart(resource_data)
        print("   ✅ Resource overview chart created")
        
    except Exception as e:
        print(f"   ❌ Error creating EC2 charts: {e}")
    
    print()

def main():
    """Run all demos."""
    print("🎯 AWS CloudWatch Log Analyzer - Demo Mode")
    print("=" * 60)
    print("This demo showcases the application's data processing")
    print("and chart creation capabilities without AWS credentials.")
    print("=" * 60)
    print()
    
    try:
        demo_log_processing()
        demo_metric_processing()
        demo_time_processing()
        demo_chart_creation()
        demo_lambda_charts()
        demo_ec2_charts()
        
        print("🎉 Demo completed successfully!")
        print("=" * 60)
        print("To run the full application with AWS integration:")
        print("1. Configure AWS credentials")
        print("2. Run: streamlit run src/main.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
