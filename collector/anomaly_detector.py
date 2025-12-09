# anomaly_detector.py
import numpy as np
from collections import defaultdict, deque
import numpy as np
class AnomalyDetector:
    def __init__(self):
        self.baseline_p95 = 100_000_000
    def detect(self, spans):
        return False
detector = AnomalyDetector()

class AnomalyDetector:
    def __init__(self):
        self.latency_history = defaultdict(deque)
        self.error_history = defaultdict(deque)
        self.window_size = 100
    
    def detect_latency_spike(self, spans, service_name):
        """Detect 2x P95 latency increase"""
        if not spans or len(spans) < 10:
            return False
        
        latencies = [
            (s.endTimeUnixNano - s.startTimeUnixNano) // 1000  # microseconds
            for s in spans
        ]
        
        current_p95 = np.percentile(latencies, 95)
        
        if len(self.latency_history[service_name]) > 50:
            prev_p95 = np.percentile(
                list(self.latency_history[service_name])[-50:], 
                95
            )
        else:
            prev_p95 = current_p95
        
        self.latency_history[service_name].append(current_p95)
        if len(self.latency_history[service_name]) > self.window_size:
            self.latency_history[service_name].popleft()
        
        return current_p95 > prev_p95 * 2  # 2x spike threshold
    
    def detect_error_spike(self, spans, service_name):
        """Detect >5% error rate"""
        if not spans:
            return False
        
        errors = sum(1 for s in spans if s.status.get("code") == 2)
        total = len(spans)
        error_rate = errors / total if total > 0 else 0
        
        self.error_history[service_name].append(error_rate)
        if len(self.error_history[service_name]) > self.window_size:
            self.error_history[service_name].popleft()
        
        return error_rate > 0.05  # 5% threshold

detector = AnomalyDetector()
