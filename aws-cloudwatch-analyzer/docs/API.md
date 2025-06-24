# API Documentation

## CloudWatch Services API

### CloudWatchLogsService

#### `get_log_groups() -> List[Dict[str, str]]`
Retrieve all CloudWatch log groups.

**Returns:**
- List of dictionaries containing log group information
- Each dictionary contains: `name`, `creation_time`, `size_bytes`

**Example:**
```python
service = CloudWatchLogsService()
log_groups = service.get_log_groups()
# [{'name': '/aws/lambda/my-function', 'creation_time': 1234567890, 'size_bytes': 1024}]
```

#### `get_lambda_log_groups() -> List[Dict[str, str]]`
Get log groups for Lambda functions only.

**Returns:**
- Filtered list of Lambda log groups (names starting with '/aws/lambda/')

#### `get_log_events(log_group_name: str, hours_back: int = 24, limit: int = 1000) -> List[Dict]`
Retrieve log events from a specific log group.

**Parameters:**
- `log_group_name`: Name of the log group
- `hours_back`: Number of hours to look back (default: 24)
- `limit`: Maximum number of events to retrieve (default: 1000)

**Returns:**
- List of log event dictionaries

#### `search_log_events(log_group_name: str, filter_pattern: str, hours_back: int = 24) -> List[Dict]`
Search log events with a filter pattern.

**Parameters:**
- `log_group_name`: Name of the log group
- `filter_pattern`: CloudWatch Logs filter pattern
- `hours_back`: Number of hours to look back (default: 24)

**Returns:**
- List of matching log events

### CloudWatchMetricsService

#### `get_ec2_instances() -> List[Dict[str, str]]`
Get list of EC2 instances.

**Returns:**
- List of dictionaries containing instance information
- Each dictionary contains: `id`, `name`, `type`, `state`

#### `get_metric_data(namespace: str, metric_name: str, dimensions: List[Dict], hours_back: int = 24, statistic: str = 'Average') -> List[Dict]`
Retrieve metric data from CloudWatch.

**Parameters:**
- `namespace`: AWS namespace (e.g., 'AWS/EC2', 'AWS/Lambda')
- `metric_name`: Name of the metric
- `dimensions`: List of dimension dictionaries
- `hours_back`: Number of hours to look back (default: 24)
- `statistic`: Statistic to retrieve (default: 'Average')

**Returns:**
- List of metric data points

#### `get_lambda_metrics(function_name: str, hours_back: int = 24) -> Dict[str, List[Dict]]`
Get comprehensive Lambda function metrics.

**Parameters:**
- `function_name`: Name of the Lambda function
- `hours_back`: Number of hours to look back (default: 24)

**Returns:**
- Dictionary containing different metric types: `invocations`, `errors`, `duration`, `throttles`, `concurrentexecutions`

#### `get_ec2_metrics(instance_id: str, hours_back: int = 24) -> Dict[str, List[Dict]]`
Get comprehensive EC2 instance metrics.

**Parameters:**
- `instance_id`: EC2 instance ID
- `hours_back`: Number of hours to look back (default: 24)

**Returns:**
- Dictionary containing different metric types: `cpuutilization`, `networkin`, `networkout`, `diskreadbytes`, `diskwritebytes`

## Data Processing API

### LogProcessor

#### `extract_lambda_metrics(log_events: List[Dict]) -> Dict[str, Any]`
Extract Lambda function metrics from log events.

**Parameters:**
- `log_events`: List of CloudWatch log events

**Returns:**
- Dictionary containing extracted metrics:
  - `total_invocations`: Number of function invocations
  - `errors`: Number of errors
  - `timeouts`: Number of timeouts
  - `durations`: List of execution durations
  - `memory_usage`: List of memory usage values
  - `cold_starts`: Number of cold starts
  - `error_messages`: List of error message details

#### `calculate_error_rate(total_invocations: int, errors: int) -> float`
Calculate error rate percentage.

**Parameters:**
- `total_invocations`: Total number of invocations
- `errors`: Number of errors

**Returns:**
- Error rate as percentage (0-100)

#### `get_performance_stats(durations: List[float]) -> Dict[str, float]`
Calculate performance statistics from duration data.

**Parameters:**
- `durations`: List of execution durations

**Returns:**
- Dictionary containing: `avg`, `min`, `max`, `p95`, `p99`

### MetricProcessor

#### `process_metric_data(metric_data: List[Dict]) -> pd.DataFrame`
Process CloudWatch metric data into pandas DataFrame.

**Parameters:**
- `metric_data`: List of metric data points

**Returns:**
- DataFrame with `timestamp` and `value` columns

#### `calculate_metric_stats(df: pd.DataFrame) -> Dict[str, float]`
Calculate statistics for metric data.

**Parameters:**
- `df`: DataFrame with metric data

**Returns:**
- Dictionary containing: `avg`, `min`, `max`, `current`

#### `detect_anomalies(df: pd.DataFrame, threshold_multiplier: float = 2.0) -> List[Dict]`
Detect anomalies in metric data using statistical method.

**Parameters:**
- `df`: DataFrame with metric data
- `threshold_multiplier`: Multiplier for standard deviation threshold (default: 2.0)

**Returns:**
- List of anomaly points with `timestamp`, `value`, and `threshold`

## Chart Components API

### ChartFactory

#### `create_time_series_chart(df: pd.DataFrame, title: str, y_label: str, color: str = '#1f77b4') -> go.Figure`
Create a time series line chart.

#### `create_metric_comparison_chart(metrics_data: Dict[str, pd.DataFrame], title: str) -> go.Figure`
Create a multi-line chart comparing different metrics.

#### `create_bar_chart(data: Dict[str, float], title: str, color: str = '#1f77b4') -> go.Figure`
Create a horizontal bar chart.

#### `create_pie_chart(data: Dict[str, float], title: str) -> go.Figure`
Create a pie chart.

#### `create_gauge_chart(value: float, title: str, max_value: float = 100, threshold_good: float = 70, threshold_warning: float = 85) -> go.Figure`
Create a gauge chart for single metric display.

### LambdaCharts

#### `create_error_rate_chart(error_data: List[Dict]) -> go.Figure`
Create error rate trend chart.

#### `create_duration_distribution(durations: List[float]) -> go.Figure`
Create duration distribution histogram.

#### `create_memory_usage_chart(memory_data: List[int]) -> go.Figure`
Create memory usage trend chart.

### EC2Charts

#### `create_cpu_utilization_chart(cpu_data: pd.DataFrame) -> go.Figure`
Create CPU utilization chart.

#### `create_network_io_chart(network_in: pd.DataFrame, network_out: pd.DataFrame) -> go.Figure`
Create network I/O comparison chart.

#### `create_resource_overview_chart(metrics: Dict[str, float]) -> go.Figure`
Create resource overview radar chart.

## UI Components API

### UIComponents

#### `render_header(title: str, subtitle: str = None)`
Render application header.

#### `render_sidebar_filters() -> Dict[str, Any]`
Render sidebar filters and return selected values.

#### `render_metric_cards(metrics: Dict[str, Any], title: str = "Key Metrics")`
Render metric cards in columns.

#### `render_data_table(data: List[Dict], title: str, max_rows: int = 10)`
Render data table with pagination.

#### `render_status_indicator(status: str, message: str = "")`
Render status indicator.

#### `render_loading_spinner(message: str = "Loading...")`
Render loading spinner with message.

#### `render_refresh_button(callback: Callable, label: str = "🔄 Refresh Data")`
Render refresh button that calls a callback function.

#### `render_export_button(data: Any, filename: str, file_format: str = "csv")`
Render export button for data download.

### NavigationComponents

#### `render_tab_navigation(tabs: List[str]) -> str`
Render tab navigation and return selected tab.

#### `render_resource_selector(resources: List[Dict], resource_type: str) -> Optional[Dict]`
Render resource selector dropdown.

## Configuration API

### Settings

#### `AWSConfig`
AWS configuration settings including region, profile, and CloudWatch settings.

#### `AppConfig`
Application configuration including UI settings and performance parameters.

#### `LogAnalysisConfig`
Log analysis specific configuration including error patterns and metric names.

#### `get_aws_regions() -> List[str]`
Get list of available AWS regions.

#### `get_time_range_options() -> Dict[str, int]`
Get available time range options in hours.
