"""
Reusable UI components for the Streamlit application.
Follows the DRY principle with modular, reusable components.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from src.config.settings import get_time_range_options, get_aws_regions


class UIComponents:
    """Collection of reusable UI components."""
    
    @staticmethod
    def render_header(title: str, subtitle: str = None):
        """Render application header."""
        st.title(title)
        if subtitle:
            st.markdown(f"*{subtitle}*")
        st.markdown("---")
    
    @staticmethod
    def render_sidebar_filters() -> Dict[str, Any]:
        """
        Render sidebar filters and return selected values.
        
        Returns:
            Dictionary containing filter selections
        """
        st.sidebar.header("🔧 Configuration")
        
        # AWS Region selection
        regions = get_aws_regions()
        selected_region = st.sidebar.selectbox(
            "AWS Region",
            regions,
            index=0,
            help="Select the AWS region to analyze"
        )
        
        # Time range selection
        time_options = get_time_range_options()
        selected_time_range = st.sidebar.selectbox(
            "Time Range",
            list(time_options.keys()),
            index=2,  # Default to "Last 24 Hours"
            help="Select the time range for analysis"
        )
        
        # Auto-refresh option
        auto_refresh = st.sidebar.checkbox(
            "Auto Refresh",
            value=False,
            help="Automatically refresh data every 5 minutes"
        )
        
        return {
            'region': selected_region,
            'time_range_hours': time_options[selected_time_range],
            'time_range_label': selected_time_range,
            'auto_refresh': auto_refresh
        }
    
    @staticmethod
    def render_metric_cards(metrics: Dict[str, Any], title: str = "Key Metrics"):
        """
        Render metric cards in columns.
        
        Args:
            metrics: Dictionary of metric name to value
            title: Section title
        """
        st.subheader(title)
        
        # Create columns based on number of metrics
        num_metrics = len(metrics)
        if num_metrics == 0:
            st.info("No metrics available")
            return
        
        cols = st.columns(min(num_metrics, 4))  # Max 4 columns
        
        for i, (metric_name, metric_value) in enumerate(metrics.items()):
            with cols[i % 4]:
                UIComponents._render_metric_card(metric_name, metric_value)
    
    @staticmethod
    def _render_metric_card(name: str, value: Any):
        """Render individual metric card."""
        # Format value based on type
        if isinstance(value, float):
            if value < 1:
                formatted_value = f"{value:.3f}"
            elif value < 100:
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = f"{value:.0f}"
        elif isinstance(value, int):
            formatted_value = f"{value:,}"
        else:
            formatted_value = str(value)
        
        # Determine color based on metric name and value
        color = UIComponents._get_metric_color(name, value)
        
        st.markdown(f"""
        <div style="
            background-color: {color};
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            margin-bottom: 1rem;
        ">
            <h3 style="margin: 0; color: white;">{formatted_value}</h3>
            <p style="margin: 0; color: white; font-size: 0.9rem;">{name.replace('_', ' ').title()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def _get_metric_color(name: str, value: Any) -> str:
        """Determine color for metric card based on name and value."""
        name_lower = name.lower()
        
        # Error-related metrics - red for high values
        if any(keyword in name_lower for keyword in ['error', 'fail', 'timeout']):
            if isinstance(value, (int, float)) and value > 0:
                return "#dc3545"  # Red
            return "#28a745"  # Green
        
        # Performance metrics - color based on thresholds
        if 'cpu' in name_lower or 'utilization' in name_lower:
            if isinstance(value, (int, float)):
                if value > 80:
                    return "#dc3545"  # Red
                elif value > 60:
                    return "#ffc107"  # Yellow
                return "#28a745"  # Green
        
        # Duration/latency metrics
        if any(keyword in name_lower for keyword in ['duration', 'latency', 'response']):
            if isinstance(value, (int, float)):
                if value > 5000:  # > 5 seconds
                    return "#dc3545"  # Red
                elif value > 1000:  # > 1 second
                    return "#ffc107"  # Yellow
                return "#28a745"  # Green
        
        # Default color
        return "#007bff"  # Blue
    
    @staticmethod
    def render_data_table(data: List[Dict], title: str, max_rows: int = 10):
        """
        Render data table with pagination.
        
        Args:
            data: List of dictionaries to display
            title: Table title
            max_rows: Maximum rows to display
        """
        st.subheader(title)
        
        if not data:
            st.info("No data available")
            return
        
        # Display total count
        st.write(f"Total records: {len(data)}")
        
        # Show first max_rows
        display_data = data[:max_rows]
        st.dataframe(display_data, use_container_width=True)
        
        if len(data) > max_rows:
            st.info(f"Showing first {max_rows} of {len(data)} records")
    
    @staticmethod
    def render_status_indicator(status: str, message: str = ""):
        """
        Render status indicator.
        
        Args:
            status: Status type ('success', 'warning', 'error', 'info')
            message: Status message
        """
        status_config = {
            'success': ('✅', 'success', '#28a745'),
            'warning': ('⚠️', 'warning', '#ffc107'),
            'error': ('❌', 'error', '#dc3545'),
            'info': ('ℹ️', 'info', '#007bff')
        }
        
        if status in status_config:
            icon, st_type, color = status_config[status]
            if st_type == 'success':
                st.success(f"{icon} {message}")
            elif st_type == 'warning':
                st.warning(f"{icon} {message}")
            elif st_type == 'error':
                st.error(f"{icon} {message}")
            else:
                st.info(f"{icon} {message}")
    
    @staticmethod
    def render_loading_spinner(message: str = "Loading..."):
        """Render loading spinner with message."""
        with st.spinner(message):
            return st.empty()
    
    @staticmethod
    def render_refresh_button(callback: Callable, label: str = "🔄 Refresh Data"):
        """
        Render refresh button that calls a callback function.
        
        Args:
            callback: Function to call when button is clicked
            label: Button label
        """
        if st.button(label, type="primary"):
            callback()
            st.rerun()
    
    @staticmethod
    def render_export_button(data: Any, filename: str, file_format: str = "csv"):
        """
        Render export button for data download.
        
        Args:
            data: Data to export
            filename: Name of the file
            file_format: Export format ('csv', 'json')
        """
        if file_format == "csv" and hasattr(data, 'to_csv'):
            csv_data = data.to_csv(index=False)
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=f"{filename}.csv",
                mime="text/csv"
            )
        elif file_format == "json":
            import json
            json_data = json.dumps(data, indent=2, default=str)
            st.download_button(
                label="📥 Export JSON",
                data=json_data,
                file_name=f"{filename}.json",
                mime="application/json"
            )


class NavigationComponents:
    """Components for application navigation."""
    
    @staticmethod
    def render_tab_navigation(tabs: List[str]) -> str:
        """
        Render tab navigation and return selected tab.
        
        Args:
            tabs: List of tab names
            
        Returns:
            Selected tab name
        """
        selected_tab = st.selectbox(
            "Select Analysis Type",
            tabs,
            index=0,
            help="Choose the type of analysis to perform"
        )
        return selected_tab
    
    @staticmethod
    def render_resource_selector(resources: List[Dict], resource_type: str) -> Optional[Dict]:
        """
        Render resource selector dropdown.
        
        Args:
            resources: List of resource dictionaries
            resource_type: Type of resource (e.g., "Lambda Function", "EC2 Instance")
            
        Returns:
            Selected resource dictionary or None
        """
        if not resources:
            st.warning(f"No {resource_type.lower()}s found")
            return None
        
        # Create display options
        options = []
        for resource in resources:
            if resource_type == "Lambda Function":
                display_name = resource['name'].replace('/aws/lambda/', '')
                options.append(f"{display_name}")
            elif resource_type == "EC2 Instance":
                display_name = f"{resource['name']} ({resource['id']})"
                options.append(display_name)
            else:
                options.append(resource.get('name', resource.get('id', 'Unknown')))
        
        selected_index = st.selectbox(
            f"Select {resource_type}",
            range(len(options)),
            format_func=lambda x: options[x],
            help=f"Choose a {resource_type.lower()} to analyze"
        )
        
        return resources[selected_index] if selected_index is not None else None
