import logging
import os
import sys

from flask import Flask, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from exporter.collector import ProSafeCollector
from exporter.metrics import update_metrics, set_switch_down

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global collector instance
collector = None


def get_config() -> tuple[str, str, int]:
    """Get configuration from environment variables."""
    host = os.environ.get('SWITCH_HOST')
    password = os.environ.get('SWITCH_PASSWORD')
    port = int(os.environ.get('PORT', '9493'))

    if not host:
        logger.error("SWITCH_HOST environment variable is required")
        sys.exit(1)

    if not password:
        logger.error("SWITCH_PASSWORD environment variable is required")
        sys.exit(1)

    return host, password, port


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    global collector

    data, num_ports = collector.collect()

    if data is not None:
        update_metrics(collector.host, data, num_ports)
    else:
        set_switch_down(collector.host)

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/health')
def health():
    """Health check endpoint."""
    return Response("OK", mimetype='text/plain')


def main():
    global collector

    host, password, port = get_config()

    logger.info(f"Starting ProSafe Web Exporter")
    logger.info(f"Switch host: {host}")
    logger.info(f"Listening on port: {port}")

    collector = ProSafeCollector(host, password)

    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
