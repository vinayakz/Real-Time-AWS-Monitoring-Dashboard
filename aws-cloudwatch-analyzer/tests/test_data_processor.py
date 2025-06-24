"""
Unit tests for data processing utilities.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.utils.data_processor import LogProcessor, MetricProcessor, TimeRangeProcessor


class TestLogProcessor:
    """Test cases for LogProcessor class."""
    
    def test_extract_lambda_metrics_empty_logs(self):
        """Test extracting metrics from empty log events."""
        processor = LogProcessor()
        result = processor.extract_lambda_metrics([])
        
        assert result['total_invocations'] == 0
        assert result['errors'] == 0
        assert result['timeouts'] == 0
        assert len(result['durations']) == 0
        assert len(result['memory_usage']) == 0
        assert result['cold_starts'] == 0
    
    def test_extract_lambda_metrics_with_data(self):
        """Test extracting metrics from sample log events."""
        processor = LogProcessor()
        
        sample_logs = [
            {'message': 'START RequestId: 123-456-789', 'timestamp': 1234567890},
            {'message': 'Duration: 150.25 ms', 'timestamp': 1234567891},
            {'message': 'Max Memory Used: 128 MB', 'timestamp': 1234567892},
            {'message': 'ERROR Something went wrong', 'timestamp': 1234567893},
            {'message': 'INIT_START Runtime Version: python3.9', 'timestamp': 1234567894}
        ]
        
        result = processor.extract_lambda_metrics(sample_logs)
        
        assert result['total_invocations'] == 1
        assert result['errors'] == 1
        assert result['cold_starts'] == 1
        assert len(result['durations']) == 1
        assert result['durations'][0] == 150.25
        assert len(result['memory_usage']) == 1
        assert result['memory_usage'][0] == 128
    
    def test_calculate_error_rate(self):
        """Test error rate calculation."""
        processor = LogProcessor()
        
        # Normal case
        assert processor.calculate_error_rate(100, 5) == 5.0
        
        # Zero invocations
        assert processor.calculate_error_rate(0, 0) == 0.0
        
        # No errors
        assert processor.calculate_error_rate(100, 0) == 0.0
    
    def test_get_performance_stats(self):
        """Test performance statistics calculation."""
        processor = LogProcessor()
        
        # Empty durations
        stats = processor.get_performance_stats([])
        assert all(value == 0 for value in stats.values())
        
        # Sample durations
        durations = [100, 200, 300, 400, 500]
        stats = processor.get_performance_stats(durations)
        
        assert stats['avg'] == 300.0
        assert stats['min'] == 100.0
        assert stats['max'] == 500.0
        assert stats['p95'] == 480.0  # 95th percentile


class TestMetricProcessor:
    """Test cases for MetricProcessor class."""
    
    def test_process_metric_data_empty(self):
        """Test processing empty metric data."""
        processor = MetricProcessor()
        result = processor.process_metric_data([])
        
        assert result.empty
        assert list(result.columns) == ['timestamp', 'value']
    
    def test_process_metric_data_with_data(self):
        """Test processing sample metric data."""
        processor = MetricProcessor()
        
        sample_data = [
            {'Timestamp': datetime(2023, 1, 1, 12, 0), 'Average': 50.5},
            {'Timestamp': datetime(2023, 1, 1, 12, 5), 'Average': 60.2},
            {'Timestamp': datetime(2023, 1, 1, 12, 10), 'Average': 45.8}
        ]
        
        result = processor.process_metric_data(sample_data)
        
        assert len(result) == 3
        assert 'timestamp' in result.columns
        assert 'value' in result.columns
        assert result['value'].tolist() == [50.5, 60.2, 45.8]
    
    def test_calculate_metric_stats(self):
        """Test metric statistics calculation."""
        processor = MetricProcessor()
        
        # Empty DataFrame
        empty_df = pd.DataFrame(columns=['timestamp', 'value'])
        stats = processor.calculate_metric_stats(empty_df)
        assert all(value == 0 for value in stats.values())
        
        # Sample DataFrame
        df = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=5, freq='5min'),
            'value': [10, 20, 30, 40, 50]
        })
        
        stats = processor.calculate_metric_stats(df)
        assert stats['avg'] == 30.0
        assert stats['min'] == 10.0
        assert stats['max'] == 50.0
        assert stats['current'] == 50.0
    
    def test_detect_anomalies(self):
        """Test anomaly detection."""
        processor = MetricProcessor()
        
        # Normal data - no anomalies
        normal_df = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=20, freq='5min'),
            'value': [50 + i for i in range(20)]  # Gradual increase
        })
        
        anomalies = processor.detect_anomalies(normal_df)
        assert len(anomalies) == 0
        
        # Data with anomaly
        anomaly_df = pd.DataFrame({
            'timestamp': pd.date_range('2023-01-01', periods=20, freq='5min'),
            'value': [50] * 19 + [500]  # One spike
        })
        
        anomalies = processor.detect_anomalies(anomaly_df)
        assert len(anomalies) > 0


class TestTimeRangeProcessor:
    """Test cases for TimeRangeProcessor class."""
    
    def test_get_time_range(self):
        """Test time range calculation."""
        processor = TimeRangeProcessor()
        
        start_time, end_time = processor.get_time_range(24)
        
        # Check that the time range is approximately 24 hours
        time_diff = end_time - start_time
        assert abs(time_diff.total_seconds() - 24 * 3600) < 60  # Within 1 minute
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        processor = TimeRangeProcessor()
        
        test_time = datetime(2023, 1, 1, 12, 30, 45)
        formatted = processor.format_timestamp(test_time)
        
        assert formatted == "2023-01-01 12:30:45 UTC"
    
    def test_get_time_buckets(self):
        """Test time bucket generation."""
        processor = TimeRangeProcessor()
        
        start_time = datetime(2023, 1, 1, 0, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 0, 0)  # 12 hours
        
        buckets = processor.get_time_buckets(start_time, end_time, 12)
        
        assert len(buckets) == 13  # 12 buckets + 1 end point
        assert buckets[0] == start_time
        assert buckets[-1] == end_time
        
        # Check bucket intervals (should be 1 hour each)
        for i in range(1, len(buckets)):
            interval = buckets[i] - buckets[i-1]
            assert abs(interval.total_seconds() - 3600) < 1  # 1 hour ± 1 second


if __name__ == "__main__":
    pytest.main([__file__])
