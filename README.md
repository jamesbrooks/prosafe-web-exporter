# ProSafe Web Exporter

Prometheus exporter for NETGEAR ProSafe Plus switches via web interface - no host networking required.

## Why?

Existing exporters ([dalance/prosafe_exporter](https://github.com/dalance/prosafe_exporter), [tillsteinbach/prosafe_exporter_python](https://github.com/tillsteinbach/prosafe_exporter_python)) require host networking for the ProSafe UDP discovery protocol. This exporter connects directly to the switch's web interface, making it Docker-friendly.

## Supported Switches

Tested on GS116Ev2. Should work with JGS516PE, JGS524Ev2, and similar models that use the same web interface.

## Metrics

| Metric | Description | Labels |
|--------|-------------|--------|
| `prosafe_up` | Switch is reachable (1/0) | `switch` |
| `prosafe_receive_bytes_total` | Incoming transfer in bytes | `switch`, `port` |
| `prosafe_transmit_bytes_total` | Outgoing transfer in bytes | `switch`, `port` |
| `prosafe_link_speed_mbps` | Link speed in Mbps | `switch`, `port` |
| `prosafe_port_up` | Port is connected (1/0) | `switch`, `port` |
| `prosafe_crc_errors_total` | CRC errors | `switch`, `port` |
| `prosafe_build_info` | Exporter version | `version` |

## Quick Start

```yaml
services:
  prosafe-exporter:
    image: jamesbrooks/prosafe-web-exporter:latest
    container_name: prosafe-exporter
    restart: unless-stopped
    ports:
      - "9493:9493"
    environment:
      - SWITCH_HOST=10.1.1.2
      - SWITCH_PASSWORD=your_password
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SWITCH_HOST` | Yes | - | Switch IP address |
| `SWITCH_PASSWORD` | Yes | - | Switch password |
| `PORT` | No | 9493 | HTTP server port |

## Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'prosafe'
    static_configs:
      - targets: ['prosafe-exporter:9493']
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/metrics` | Prometheus metrics |
| `/health` | Health check |

## Building

```bash
./build.sh
```
