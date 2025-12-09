import numpy as np
from collections import defaultdict, deque
from datetime import datetime, timedelta

class AnomalyDetector:
    def __init__(self):
        self.latency_history = defaultdict(deque)
        self.error_history = defaultdict(deque)
        self.window_size = 100
        
    def detect_latency_spike(self, spans, service_name):
        latencies = [s['duration'] for s in spans if s.get('serviceName') == service_name]
        if len(latencies) < 10:
            return False
            
        p95 = np.percentile(latencies, 95)
        prev_p95 = np.percentile(list(self.latency_history[service_name])[-50:], 95) if len(self.latency_history[service_name]) > 50 else p95
        
        self.latency_history[service_name].append(p95)
        if len(self.latency_history[service_name]) > self.window_size:
            self.latency_history[service_name].popleft()
            
        return p95 > prev_p95 * 2  # 2x spike
    
    def detect_error_spike(self, spans, service_name):
        errors = sum(1 for s in spans if s.get('serviceName') == service_name and s.get('statusCode') == 'ERROR')
        total = len([s for s in spans if s.get('serviceName') == service_name])
        error_rate = errors / total if total > 0 else 0
        
        self.error_history[service_name].append(error_rate)
        if len(self.error_history[service_name]) > self.window_size:
            self.error_history[service_name].popleft()
            
        return error_rate > 0.05  # >5%
    
detector = AnomalyDetector()
