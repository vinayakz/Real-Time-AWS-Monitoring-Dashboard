"""
Chart components for data visualization.
Follows the Single Responsibility Principle with reusable chart components.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.config.settings import app_config


class ChartFactory:
    """Factory class for creating different types of charts."""
    
    @staticmethod
    def create_time_series_chart(df: pd.DataFrame, title: str, y_label: str, 
                               color: str = '#1f77b4') -> go.Figure:
        """
        Create a time series line chart.
        
        Args:
            df: DataFrame with 'timestamp' and 'value' columns
            title: Chart title
            y_label: Y-axis label
            color: Line color
            
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        if not df.empty:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['value'],
                mode='lines+markers',
                name=y_label,
                line=dict(color=color, width=2),
                marker=dict(size=4)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title=y_label,
            height=app_config.chart_height,
            showlegend=False,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_metric_comparison_chart(metrics_data: Dict[str, pd.DataFrame], 
                                     title: str) -> go.Figure:
        """
        Create a multi-line chart comparing different metrics.
        
        Args:
            metrics_data: Dictionary of metric name to DataFrame
            title: Chart title
            
        Returns:
            Plotly figure object
        """
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, (metric_name, df) in enumerate(metrics_data.items()):
            if not df.empty:
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['value'],
                    mode='lines+markers',
                    name=metric_name.replace('_', ' ').title(),
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=4)
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Value",
            height=app_config.chart_height,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_bar_chart(data: Dict[str, float], title: str, 
                        color: str = '#1f77b4') -> go.Figure:
        """
        Create a horizontal bar chart.
        
        Args:
            data: Dictionary of labels to values
            title: Chart title
            color: Bar color
            
        Returns:
            Plotly figure object
        """
        fig = go.Figure(go.Bar(
            x=list(data.values()),
            y=list(data.keys()),
            orientation='h',
            marker_color=color
        ))
        
        fig.update_layout(
            title=title,
            height=app_config.chart_height,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_pie_chart(data: Dict[str, float], title: str) -> go.Figure:
        """
        Create a pie chart.
        
        Args:
            data: Dictionary of labels to values
            title: Chart title
            
        Returns:
            Plotly figure object
        """
        fig = go.Figure(go.Pie(
            labels=list(data.keys()),
            values=list(data.values()),
            hole=0.3
        ))
        
        fig.update_layout(
            title=title,
            height=app_config.chart_height,
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def create_gauge_chart(value: float, title: str, max_value: float = 100,
                          threshold_good: float = 70, threshold_warning: float = 85) -> go.Figure:
        """
        Create a gauge chart for single metric display.
        
        Args:
            value: Current value
            title: Chart title
            max_value: Maximum value for the gauge
            threshold_good: Good performance threshold
            threshold_warning: Warning threshold
            
        Returns:
            Plotly figure object
        """
        # Determine color based on thresholds
        if value <= threshold_good:
            color = "green"
        elif value <= threshold_warning:
            color = "yellow"
        else:
            color = "red"
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, threshold_good], 'color': "lightgray"},
                    {'range': [threshold_good, threshold_warning], 'color': "gray"},
                    {'range': [threshold_warning, max_value], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': threshold_warning
                }
            }
        ))
        
        fig.update_layout(height=300)
        return fig


class LambdaCharts:
    """Specialized charts for Lambda function analysis."""
    
    @staticmethod
    def create_error_rate_chart(error_data: List[Dict]) -> go.Figure:
        """Create error rate trend chart."""
        if not error_data:
            return ChartFactory.create_time_series_chart(
                pd.DataFrame(), "Error Rate Over Time", "Error Rate (%)"
            )
        
        df = pd.DataFrame(error_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return ChartFactory.create_time_series_chart(
            df, "Error Rate Over Time", "Error Rate (%)", color='#d62728'
        )
    
    @staticmethod
    def create_duration_distribution(durations: List[float]) -> go.Figure:
        """Create duration distribution histogram."""
        fig = go.Figure()
        
        if durations:
            fig.add_trace(go.Histogram(
                x=durations,
                nbinsx=30,
                name="Duration Distribution",
                marker_color='#1f77b4'
            ))
        
        fig.update_layout(
            title="Lambda Duration Distribution",
            xaxis_title="Duration (ms)",
            yaxis_title="Frequency",
            height=app_config.chart_height,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_memory_usage_chart(memory_data: List[int]) -> go.Figure:
        """Create memory usage trend chart."""
        if not memory_data:
            return ChartFactory.create_time_series_chart(
                pd.DataFrame(), "Memory Usage Over Time", "Memory (MB)"
            )
        
        # Create time series data (simplified for demo)
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='now', periods=len(memory_data), freq='5min'),
            'value': memory_data
        })
        
        return ChartFactory.create_time_series_chart(
            df, "Memory Usage Over Time", "Memory (MB)", color='#2ca02c'
        )


class EC2Charts:
    """Specialized charts for EC2 instance analysis."""
    
    @staticmethod
    def create_cpu_utilization_chart(cpu_data: pd.DataFrame) -> go.Figure:
        """Create CPU utilization chart."""
        return ChartFactory.create_time_series_chart(
            cpu_data, "CPU Utilization", "CPU %", color='#ff7f0e'
        )
    
    @staticmethod
    def create_network_io_chart(network_in: pd.DataFrame, network_out: pd.DataFrame) -> go.Figure:
        """Create network I/O comparison chart."""
        fig = go.Figure()
        
        if not network_in.empty:
            fig.add_trace(go.Scatter(
                x=network_in['timestamp'],
                y=network_in['value'] / (1024 * 1024),  # Convert to MB
                mode='lines+markers',
                name='Network In',
                line=dict(color='#2ca02c', width=2)
            ))
        
        if not network_out.empty:
            fig.add_trace(go.Scatter(
                x=network_out['timestamp'],
                y=network_out['value'] / (1024 * 1024),  # Convert to MB
                mode='lines+markers',
                name='Network Out',
                line=dict(color='#d62728', width=2)
            ))
        
        fig.update_layout(
            title="Network I/O",
            xaxis_title="Time",
            yaxis_title="Data (MB)",
            height=app_config.chart_height,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_resource_overview_chart(metrics: Dict[str, float]) -> go.Figure:
        """Create resource overview radar chart."""
        categories = list(metrics.keys())
        values = list(metrics.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Current Usage'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            title="Resource Overview",
            height=app_config.chart_height,
            showlegend=False
        )
        
        return fig
