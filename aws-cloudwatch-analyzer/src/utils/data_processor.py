"""
Data processing utilities for log analysis and metric processing.
Follows the Single Responsibility Principle.
"""

import re
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from src.config.settings import log_config


class LogProcessor:
    """Handles log data processing and analysis."""
    
    @staticmethod
    def extract_lambda_metrics(log_events: List[Dict]) -> Dict[str, Any]:
        """
        Extract Lambda function metrics from log events.
        
        Args:
            log_events: List of CloudWatch log events
            
        Returns:
            Dictionary containing extracted metrics
        """
        metrics = {
            'total_invocations': 0,
            'errors': 0,
            'timeouts': 0,
            'durations': [],
            'memory_usage': [],
            'cold_starts': 0,
            'error_messages': []
        }
        
        for event in log_events:
            message = event.get('message', '')
            
            # Count invocations (START events)
            if 'START RequestId:' in message:
                metrics['total_invocations'] += 1
            
            # Detect errors
            if any(pattern in message for pattern in log_config.lambda_error_patterns):
                metrics['errors'] += 1
                metrics['error_messages'].append({
                    'timestamp': event.get('timestamp'),
                    'message': message[:200]  # Truncate long messages
                })
            
            # Detect timeouts
            if re.search(log_config.lambda_timeout_pattern, message):
                metrics['timeouts'] += 1
            
            # Extract duration
            duration_match = re.search(log_config.lambda_duration_pattern, message)
            if duration_match:
                metrics['durations'].append(float(duration_match.group(1)))
            
            # Extract memory usage
            memory_match = re.search(log_config.lambda_memory_pattern, message)
            if memory_match:
                metrics['memory_usage'].append(int(memory_match.group(1)))
            
            # Detect cold starts
            if 'INIT_START' in message:
                metrics['cold_starts'] += 1
        
        return metrics
    
    @staticmethod
    def calculate_error_rate(total_invocations: int, errors: int) -> float:
        """Calculate error rate percentage."""
        if total_invocations == 0:
            return 0.0
        return (errors / total_invocations) * 100
    
    @staticmethod
    def get_performance_stats(durations: List[float]) -> Dict[str, float]:
        """Calculate performance statistics from duration data."""
        if not durations:
            return {'avg': 0, 'min': 0, 'max': 0, 'p95': 0, 'p99': 0}
        
        df = pd.Series(durations)
        return {
            'avg': df.mean(),
            'min': df.min(),
            'max': df.max(),
            'p95': df.quantile(0.95),
            'p99': df.quantile(0.99)
        }


class MetricProcessor:
    """Handles CloudWatch metrics processing."""
    
    @staticmethod
    def process_metric_data(metric_data: List[Dict]) -> pd.DataFrame:
        """
        Process CloudWatch metric data into pandas DataFrame.
        
        Args:
            metric_data: List of metric data points
            
        Returns:
            DataFrame with timestamp and value columns
        """
        if not metric_data:
            return pd.DataFrame(columns=['timestamp', 'value'])
        
        df = pd.DataFrame([
            {
                'timestamp': point['Timestamp'],
                'value': point.get('Average', point.get('Sum', point.get('Maximum', 0)))
            }
            for point in metric_data
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df
    
    @staticmethod
    def calculate_metric_stats(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate statistics for metric data."""
        if df.empty:
            return {'avg': 0, 'min': 0, 'max': 0, 'current': 0}
        
        return {
            'avg': df['value'].mean(),
            'min': df['value'].min(),
            'max': df['value'].max(),
            'current': df['value'].iloc[-1] if not df.empty else 0
        }
    
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, threshold_multiplier: float = 2.0) -> List[Dict]:
        """
        Detect anomalies in metric data using simple statistical method.
        
        Args:
            df: DataFrame with metric data
            threshold_multiplier: Multiplier for standard deviation threshold
            
        Returns:
            List of anomaly points
        """
        if df.empty or len(df) < 10:
            return []
        
        mean_val = df['value'].mean()
        std_val = df['value'].std()
        threshold = mean_val + (threshold_multiplier * std_val)
        
        anomalies = df[df['value'] > threshold]
        
        return [
            {
                'timestamp': row['timestamp'],
                'value': row['value'],
                'threshold': threshold
            }
            for _, row in anomalies.iterrows()
        ]


class TimeRangeProcessor:
    """Handles time range calculations and formatting."""
    
    @staticmethod
    def get_time_range(hours: int) -> Tuple[datetime, datetime]:
        """
        Get start and end time for specified hours back from now.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Tuple of (start_time, end_time)
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        return start_time, end_time
    
    @staticmethod
    def format_timestamp(timestamp: datetime) -> str:
        """Format timestamp for display."""
        return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    @staticmethod
    def get_time_buckets(start_time: datetime, end_time: datetime, bucket_count: int = 24) -> List[datetime]:
        """
        Generate time buckets for time series analysis.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            bucket_count: Number of buckets to create
            
        Returns:
            List of datetime objects representing bucket boundaries
        """
        delta = (end_time - start_time) / bucket_count
        return [start_time + (i * delta) for i in range(bucket_count + 1)]
