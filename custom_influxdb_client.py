import time
import threading
import logging

from fast_influxdb_client.fast_influxdb_client import FastInfluxDBClient, InfluxMetric


class CustomInfluxDBClient(FastInfluxDBClient):
    def __init__(self, env_filepath=None, delay=5):
        super().__init__(env_filepath)
        self.queue = []
        self.delay = delay  # Delay in seconds
        self.lock = threading.Lock()  # To ensure thread-safe operations on the queue

        # Start a thread to periodically send metrics from the queue
        self._start_sender_thread()

    def _start_sender_thread(self):
        sender_thread = threading.Thread(target=self._send_metrics_periodically)
        sender_thread.daemon = True
        sender_thread.start()

    def _send_metrics_periodically(self):
        while True:
            time.sleep(self.delay)
            with self.lock:
                if self.queue:
                    self._send_metrics(self.queue)

    def _send_metrics(self, metrics):
        # Implement the logic to send metrics to InfluxDB server
        # This can be done using the methods provided by InfluxDBClient
        # For example:
        for metric in metrics:
            self.write_metric(metric)

    def add_metrics_to_queue(self, metrics):
        with self.lock:
            if not isinstance(metrics, list):
                metrics = [metrics]
            self.queue.extend(metrics)

    def getLoggingHandler(self):
        return InfluxDBLoggingHandler(self)


class InfluxDBLoggingHandler(logging.Handler):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def emit(self, record):
        log_entry = InfluxMetric(
            measurement="logs",
            tags={"level": record.levelname, "logger": record.name},
            fields={
                "message": self.format(record),
            },
        )
        self.client.add_metrics_to_queue(log_entry)
