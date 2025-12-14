"""
Performance monitoring and metrics
"""

import time
import psutil
import os
from collections import deque
from functools import wraps
from typing import Callable, Dict, Any, List
from datetime import datetime


class PerformanceMonitor:
    """Monitor application performance metrics"""

    def __init__(self):
        self.request_times = deque(maxlen=1000)  # Auto-pops oldest when full
        self.endpoint_times = {}
        self.memory_snapshots = []
        self.start_time = time.time()

    def record_request(self, endpoint: str, duration: float) -> None:
        """Record request duration"""
        self.request_times.append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'endpoint': endpoint
        })
        # deque with maxlen automatically pops oldest when full

        # Track endpoint-specific metrics
        if endpoint not in self.endpoint_times:
            self.endpoint_times[endpoint] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }

        metrics = self.endpoint_times[endpoint]
        metrics['count'] += 1
        metrics['total_time'] += duration
        metrics['min_time'] = min(metrics['min_time'], duration)
        metrics['max_time'] = max(metrics['max_time'], duration)

    def get_average_request_time(self) -> float:
        """Get average request time"""
        if not self.request_times:
            return 0
        total = sum(r['duration'] for r in self.request_times)
        return total / len(self.request_times)

    def get_endpoint_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Get metrics for specific endpoint"""
        if endpoint not in self.endpoint_times:
            return None

        metrics = self.endpoint_times[endpoint]
        return {
            'endpoint': endpoint,
            'count': metrics['count'],
            'total_time': metrics['total_time'],
            'avg_time': metrics['total_time'] / metrics['count'],
            'min_time': metrics['min_time'],
            'max_time': metrics['max_time']
        }

    def get_slowest_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest endpoints by average time"""
        endpoints = [
            {
                'endpoint': endpoint,
                'avg_time': metrics['total_time'] / metrics['count'],
                'count': metrics['count']
            }
            for endpoint, metrics in self.endpoint_times.items()
        ]
        return sorted(endpoints, key=lambda x: x['avg_time'], reverse=True)[:limit]

    def get_most_called_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most called endpoints"""
        endpoints = [
            {
                'endpoint': endpoint,
                'count': metrics['count'],
                'avg_time': metrics['total_time'] / metrics['count']
            }
            for endpoint, metrics in self.endpoint_times.items()
        ]
        return sorted(endpoints, key=lambda x: x['count'], reverse=True)[:limit]

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }

    def get_cpu_usage(self) -> float:
        """Get current CPU usage"""
        return psutil.cpu_percent(interval=0.1)

    def get_uptime(self) -> Dict[str, Any]:
        """Get application uptime"""
        uptime_seconds = time.time() - self.start_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)

        return {
            'uptime_seconds': uptime_seconds,
            'uptime_formatted': f"{hours}h {minutes}m {seconds}s",
            'started_at': datetime.fromtimestamp(self.start_time).isoformat()
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        return {
            'memory': self.get_memory_usage(),
            'cpu': self.get_cpu_usage(),
            'uptime': self.get_uptime(),
            'request_count': len(self.request_times),
            'avg_request_time': self.get_average_request_time(),
            'unique_endpoints': len(self.endpoint_times)
        }

    def get_full_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            'system_metrics': self.get_system_metrics(),
            'slowest_endpoints': self.get_slowest_endpoints(),
            'most_called_endpoints': self.get_most_called_endpoints(),
            'recent_requests': self.request_times[-20:]  # Last 20 requests
        }


# Global monitor instance
_monitor = None


def get_performance_monitor():
    """Get or create global performance monitor"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def monitor_performance(f: Callable) -> Callable:
    """Decorator for monitoring function performance"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        monitor = get_performance_monitor()
        endpoint = f.__name__

        start_time = time.time()
        result = f(*args, **kwargs)
        duration = time.time() - start_time

        monitor.record_request(endpoint, duration)

        return result

    return decorated_function


class RequestTimer:
    """Context manager for timing code blocks"""

    def __init__(self, endpoint: str = 'unknown'):
        self.endpoint = endpoint
        self.start_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        monitor = get_performance_monitor()
        monitor.record_request(self.endpoint, self.duration)
