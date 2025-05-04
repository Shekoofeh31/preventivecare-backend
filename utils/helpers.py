# utils/helpers.py

def sanitize_input(input_data):
    """Sanitize input data to prevent security issues."""
    # For now, just return the input data
    return input_data

def format_health_data(data):
    """Format health data for consistent output."""
    # For now, just return the data
    return data

def log_api_request(endpoint, status_code, processing_time):
    """Log API request details."""
    print(f"API Request: {endpoint}, Status: {status_code}, Processing Time: {processing_time:.4f}s")