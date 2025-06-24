# Architecture Documentation

## Overview

The AWS CloudWatch Log Analyzer is built following SOLID principles and clean architecture patterns to ensure maintainability, testability, and extensibility.

## Architecture Patterns

### 1. Model-View-Controller (MVC)
- **Model**: Data processing utilities and AWS service interactions
- **View**: Streamlit UI components and charts
- **Controller**: Main application orchestrating the flow

### 2. Repository Pattern
- `CloudWatchLogsService` and `CloudWatchMetricsService` abstract AWS API interactions
- Provides consistent interface for data access
- Enables easy mocking for testing

### 3. Factory Pattern
- `ChartFactory` creates different types of charts
- Specialized chart classes for Lambda and EC2 metrics
- Promotes code reuse and consistency

### 4. Singleton Pattern
- `AWSClientManager` ensures single AWS client instances per service/region
- Reduces resource usage and connection overhead

## SOLID Principles Implementation

### Single Responsibility Principle (SRP)
- Each class has a single, well-defined responsibility
- `LogProcessor` handles only log data processing
- `MetricProcessor` handles only metric data processing
- `UIComponents` handles only UI rendering

### Open/Closed Principle (OCP)
- Chart components are open for extension (new chart types)
- Closed for modification (existing charts remain unchanged)
- Service layer can be extended with new AWS services

### Liskov Substitution Principle (LSP)
- All chart classes can be used interchangeably through common interfaces
- Service classes implement consistent interfaces

### Interface Segregation Principle (ISP)
- Components depend only on interfaces they use
- UI components don't depend on AWS service details
- Chart components don't depend on data processing logic

### Dependency Inversion Principle (DIP)
- High-level modules don't depend on low-level modules
- Both depend on abstractions (service interfaces)
- AWS client management is abstracted from business logic

## Project Structure

```
aws-cloudwatch-analyzer/
├── src/
│   ├── main.py                 # Application entry point (Controller)
│   ├── config/                 # Configuration management
│   │   └── settings.py
│   ├── services/               # Business logic layer (Model)
│   │   └── cloudwatch_service.py
│   ├── utils/                  # Utility functions
│   │   ├── aws_client.py       # AWS client management
│   │   └── data_processor.py   # Data processing utilities
│   └── components/             # UI layer (View)
│       ├── ui_components.py    # Reusable UI components
│       └── charts.py           # Chart components
├── tests/                      # Test suite
├── docs/                       # Documentation
└── requirements/               # Dependencies
```

## Data Flow

1. **User Input**: User selects analysis type and filters
2. **Service Layer**: AWS services fetch data from CloudWatch
3. **Processing Layer**: Data processors transform raw data
4. **Presentation Layer**: UI components render results
5. **Visualization Layer**: Charts display processed data

## Key Design Decisions

### Caching Strategy
- Streamlit's `@st.cache_data` decorator for expensive operations
- 5-minute TTL for AWS API calls
- Singleton pattern for AWS clients

### Error Handling
- Graceful degradation when AWS services are unavailable
- User-friendly error messages
- Fallback options for missing data

### Performance Optimization
- Lazy loading of AWS resources
- Pagination for large datasets
- Efficient data structures (pandas DataFrames)

### Security Considerations
- No hardcoded credentials
- Uses standard AWS credential chain
- Minimal required permissions

## Extension Points

### Adding New AWS Services
1. Create new service class in `services/`
2. Implement consistent interface
3. Add UI components for new service
4. Create specialized charts if needed

### Adding New Chart Types
1. Extend `ChartFactory` with new methods
2. Create specialized chart classes
3. Follow existing naming conventions

### Adding New Data Sources
1. Create new processor in `utils/`
2. Implement consistent data transformation
3. Add configuration options

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (AWS APIs)
- Focus on business logic and data processing

### Integration Tests
- Test component interactions
- Use test fixtures for AWS responses
- Validate end-to-end workflows

### Test Coverage
- Aim for >80% code coverage
- Focus on critical business logic
- Test error handling paths

## Deployment Considerations

### Local Development
- Use AWS credentials from local environment
- Streamlit development server
- Hot reloading for rapid development

### Production Deployment
- Use IAM roles for AWS access
- Container-based deployment (Docker)
- Environment-specific configuration

### Monitoring
- Application logs for debugging
- Performance metrics collection
- Error tracking and alerting
