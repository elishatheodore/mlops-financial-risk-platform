"""
Prometheus metrics collection for credit card fraud detection API.
"""

import logging
import time
import os
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Prediction metrics
predictions_total = Counter(
    'risk_platform_predictions_total',
    'Total number of predictions made',
    ['risk_label', 'model_version']
)

prediction_latency_seconds = Histogram(
    'risk_platform_prediction_latency_seconds',
    'Time spent processing predictions',
    ['endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Model performance metrics
model_drift_score = Gauge(
    'risk_platform_model_drift_score',
    'Current model drift score (0-1)',
    ['model_version']
)

model_accuracy_score = Gauge(
    'risk_platform_model_accuracy_score',
    'Current model accuracy score (0-1)',
    ['model_version']
)

# Error metrics
prediction_errors_total = Counter(
    'risk_platform_prediction_errors_total',
    'Total number of prediction errors',
    ['error_type', 'endpoint']
)

# Business metrics
high_risk_predictions_total = Counter(
    'risk_platform_high_risk_predictions_total',
    'Total number of high-risk predictions',
    ['model_version']
)

medium_risk_predictions_total = Counter(
    'risk_platform_medium_risk_predictions_total',
    'Total number of medium-risk predictions',
    ['model_version']
)

low_risk_predictions_total = Counter(
    'risk_platform_low_risk_predictions_total',
    'Total number of low-risk predictions',
    ['model_version']
)

# System metrics
api_requests_total = Counter(
    'risk_platform_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration_seconds = Histogram(
    'risk_platform_api_request_duration_seconds',
    'Time spent processing API requests',
    ['method', 'endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Model loading metrics
model_loads_total = Counter(
    'risk_platform_model_loads_total',
    'Total number of model loads',
    ['status', 'model_version']
)

model_load_duration_seconds = Histogram(
    'risk_platform_model_load_duration_seconds',
    'Time spent loading models',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]
)

# Feature metrics
feature_importance = Gauge(
    'risk_platform_feature_importance',
    'Feature importance scores',
    ['feature_name', 'model_version']
)

# Health metrics
service_uptime_seconds = Gauge(
    'risk_platform_service_uptime_seconds',
    'Service uptime in seconds'
)

memory_usage_bytes = Gauge(
    'risk_platform_memory_usage_bytes',
    'Current memory usage in bytes'
)

cpu_usage_percent = Gauge(
    'risk_platform_cpu_usage_percent',
    'Current CPU usage percentage'
)

# Batch processing metrics
batch_predictions_total = Counter(
    'risk_platform_batch_predictions_total',
    'Total number of batch prediction requests',
    ['model_version']
)

batch_size_histogram = Histogram(
    'risk_platform_batch_size_histogram',
    'Size of batch prediction requests',
    buckets=[1, 5, 10, 25, 50, 100]
)

batch_processing_duration_seconds = Histogram(
    'risk_platform_batch_processing_duration_seconds',
    'Time spent processing batch predictions',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]
)

class MetricsCollector:
    """Metrics collector for the fraud detection service."""
    
    def __init__(self):
        self.start_time = time.time()
        self.update_service_metrics()
    
    def record_prediction(self, risk_score: float, risk_label: str, model_version: str):
        """Record a prediction metric."""
        predictions_total.labels(risk_label=risk_label, model_version=model_version).inc()
        
        # Record risk-specific counters
        if risk_label == "HIGH":
            high_risk_predictions_total.labels(model_version=model_version).inc()
        elif risk_label == "MEDIUM":
            medium_risk_predictions_total.labels(model_version=model_version).inc()
        else:
            low_risk_predictions_total.labels(model_version=model_version).inc()
    
    def record_prediction_latency(self, duration: float, endpoint: str = 'predict'):
        """Record prediction latency."""
        prediction_latency_seconds.labels(endpoint=endpoint).observe(duration)
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics."""
        api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_prediction_error(self, error_type: str, endpoint: str = 'predict'):
        """Record prediction error."""
        prediction_errors_total.labels(error_type=error_type, endpoint=endpoint).inc()
    
    def record_model_load(self, status: str, model_version: str, duration: float):
        """Record model load metrics."""
        model_loads_total.labels(status=status, model_version=model_version).inc()
        model_load_duration_seconds.observe(duration)
    
    def update_model_drift_score(self, drift_score: float, model_version: str):
        """Update model drift score."""
        model_drift_score.labels(model_version=model_version).set(drift_score)
    
    def update_model_accuracy(self, accuracy: float, model_version: str):
        """Update model accuracy score."""
        model_accuracy_score.labels(model_version=model_version).set(accuracy)
    
    def update_feature_importance(self, feature_importance_dict: Dict[str, float], model_version: str):
        """Update feature importance metrics."""
        for feature_name, importance in feature_importance_dict.items():
            feature_importance.labels(feature_name=feature_name, model_version=model_version).set(importance)
    
    def update_service_metrics(self):
        """Update service-level metrics."""
        # Update uptime
        uptime = time.time() - self.start_time
        service_uptime_seconds.set(uptime)
        
        # Update memory and CPU usage (if psutil is available)
        try:
            import psutil
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_usage_bytes.set(memory_info.rss)
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            cpu_usage_percent.set(cpu_percent)
            
        except ImportError:
            logger.warning("psutil not available, cannot collect system metrics")
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
    
    def record_batch_prediction(self, batch_size: int, model_version: str, duration: float):
        """Record batch prediction metrics."""
        batch_predictions_total.labels(model_version=model_version).inc()
        batch_size_histogram.observe(batch_size)
        batch_processing_duration_seconds.observe(duration)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        try:
            from prometheus_client import REGISTRY
            
            metrics_summary = {}
            
            # Collect all metrics
            for metric_family in REGISTRY.collect():
                metric_name = metric_family.name
                samples = []
                
                for sample in metric_family.samples:
                    samples.append({
                        'labels': sample.labels,
                        'value': sample.value
                    })
                
                metrics_summary[metric_name] = samples
            
            return metrics_summary
            
        except Exception as e:
            logger.error(f"Failed to collect metrics summary: {e}")
            return {}

# Global metrics collector instance
metrics_collector = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector

# Decorators for automatic metrics collection
def track_prediction_metrics(endpoint: str = 'predict'):
    """Decorator to track prediction metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error_type = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_type = type(e).__name__
                metrics_collector.record_prediction_error(error_type, endpoint)
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_prediction_latency(duration, endpoint)
        
        return wrapper
    return decorator

def track_api_metrics(method: str = 'POST'):
    """Decorator to track API request metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                endpoint = func.__name__.replace('_', '/')
                metrics_collector.record_api_request(method, endpoint, status_code, duration)
        
        return wrapper
    return decorator

def track_model_load_metrics():
    """Decorator to track model loading metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            model_version = 'unknown'
            
            try:
                result = func(*args, **kwargs)
                if isinstance(result, dict) and 'model_version' in result:
                    model_version = result['model_version']
                return result
            except Exception as e:
                status = 'failure'
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_model_load(status, model_version, duration)
        
        return wrapper
    return decorator

# Create ASGI app for Prometheus metrics
metrics_app = make_asgi_app()

def update_metrics_periodically():
    """Update metrics periodically (should be called by a background task)."""
    metrics_collector.update_service_metrics()

# Business metrics helpers
def calculate_risk_distribution(risk_scores: list) -> Dict[str, int]:
    """Calculate risk distribution from a list of risk scores."""
    distribution = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
    
    for score in risk_scores:
        if score < 0.3:
            distribution['LOW'] += 1
        elif score < 0.7:
            distribution['MEDIUM'] += 1
        else:
            distribution['HIGH'] += 1
    
    return distribution

def record_prediction_batch(risk_scores: list, risk_labels: list, model_version: str):
    """Record a batch of predictions."""
    for score, label in zip(risk_scores, risk_labels):
        metrics_collector.record_prediction(score, label, model_version)

# Initialize logging for metrics
logger.info("📊 Prometheus metrics initialized")
logger.info("   • Metrics endpoint: /metrics")
logger.info("   • Tracking: predictions, latency, errors, drift, accuracy")
                model_version="latest",
                risk_level=prediction_result.get('risk_level', 'Unknown')
            ).inc()
            
            if prediction_result.get('risk_score'):
                self.metrics.risk_score_distribution.observe(prediction_result['risk_score'])
            
            if prediction_result.get('probability_default'):
                self.metrics.default_probability_distribution.observe(prediction_result['probability_default'])
                
        except Exception as e:
            logger.error(f"Error recording prediction metrics: {e}")
    
    def get_risk_level_distribution(self) -> Dict[str, int]:
        """Get distribution of risk levels."""
        if not self.prediction_history:
            return {}
        
        distribution = {}
        for entry in self.prediction_history:
            risk_level = entry.get('risk_level', 'Unknown')
            distribution[risk_level] = distribution.get(risk_level, 0) + 1
        
        return distribution
    
    def get_average_risk_score(self) -> float:
        """Get average risk score."""
        if not self.prediction_history:
            return 0.0
        
        risk_scores = [entry.get('risk_score', 0) for entry in self.prediction_history if entry.get('risk_score')]
        return sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
    
    def get_high_risk_percentage(self, threshold: float = 70.0) -> float:
        """Get percentage of high-risk predictions."""
        if not self.prediction_history:
            return 0.0
        
        high_risk_count = sum(
            1 for entry in self.prediction_history 
            if entry.get('risk_score', 0) > threshold
        )
        
        return (high_risk_count / len(self.prediction_history)) * 100

def update_system_metrics(metrics: MetricsCollector):
    """Update system metrics."""
    try:
        import psutil
        
        # Memory usage
        memory = psutil.virtual_memory()
        metrics.memory_usage.set(memory.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        metrics.cpu_usage.set(cpu_percent)
        
    except ImportError:
        logger.warning("psutil not available, system metrics disabled")
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")

def get_metrics_summary(metrics: MetricsCollector) -> Dict[str, Any]:
    """Get a summary of current metrics."""
    try:
        # Get the latest metrics from the registry
        metric_family_list = metrics.registry._collector_to_names.items()
        
        summary = {
            'total_predictions': 0,
            'avg_prediction_time': 0.0,
            'total_requests': 0,
            'error_count': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
        
        # Extract metric values (simplified version)
        for collector, names in metric_family_list:
            for name in names:
                if 'predictions_total' in name:
                    # This is a simplified extraction
                    pass
                elif 'http_requests_total' in name:
                    pass
                elif 'errors_total' in name:
                    pass
                elif 'memory_usage' in name:
                    pass
                elif 'cpu_usage' in name:
                    pass
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        return {}
