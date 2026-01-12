from prometheus_client import Gauge, Info

from exporter import __version__

# Switch-level metrics
prosafe_up = Gauge(
    'prosafe_up',
    'Switch is reachable',
    ['switch']
)

# Port-level metrics
prosafe_receive_bytes_total = Gauge(
    'prosafe_receive_bytes_total',
    'Incoming transfer in bytes',
    ['switch', 'port']
)

prosafe_transmit_bytes_total = Gauge(
    'prosafe_transmit_bytes_total',
    'Outgoing transfer in bytes',
    ['switch', 'port']
)

prosafe_link_speed_mbps = Gauge(
    'prosafe_link_speed_mbps',
    'Link speed in Mbps',
    ['switch', 'port']
)

prosafe_port_up = Gauge(
    'prosafe_port_up',
    'Port is connected',
    ['switch', 'port']
)

prosafe_crc_errors_total = Gauge(
    'prosafe_crc_errors_total',
    'CRC errors',
    ['switch', 'port']
)

# Build info
prosafe_build_info = Info(
    'prosafe_build',
    'Exporter build information'
)

# Set build info once at import
prosafe_build_info.info({'version': __version__})


BYTES_PER_MB = 1048576  # 1024 * 1024


def update_metrics(switch_host: str, data: dict, num_ports: int) -> None:
    """Update all Prometheus metrics from switch data."""
    prosafe_up.labels(switch=switch_host).set(1)

    for port in range(1, num_ports + 1):
        port_label = str(port)

        # RX bytes (convert MB to bytes)
        rx_mb = data.get(f'port_{port}_sum_rx_mbytes', 0) or 0
        prosafe_receive_bytes_total.labels(
            switch=switch_host, port=port_label
        ).set(rx_mb * BYTES_PER_MB)

        # TX bytes (convert MB to bytes)
        tx_mb = data.get(f'port_{port}_sum_tx_mbytes', 0) or 0
        prosafe_transmit_bytes_total.labels(
            switch=switch_host, port=port_label
        ).set(tx_mb * BYTES_PER_MB)

        # Link speed
        speed = data.get(f'port_{port}_connection_speed', 0) or 0
        prosafe_link_speed_mbps.labels(
            switch=switch_host, port=port_label
        ).set(speed)

        # Port up/down
        status = data.get(f'port_{port}_status', 'off')
        prosafe_port_up.labels(
            switch=switch_host, port=port_label
        ).set(1 if status == 'on' else 0)

        # CRC errors (may not be present for all ports)
        crc = data.get(f'port_{port}_crc_errors', 0) or 0
        prosafe_crc_errors_total.labels(
            switch=switch_host, port=port_label
        ).set(crc)


def set_switch_down(switch_host: str) -> None:
    """Mark switch as unreachable."""
    prosafe_up.labels(switch=switch_host).set(0)
