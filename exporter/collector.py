import hashlib
import hmac
import logging
import re

import requests

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password using HMAC-MD5 with Netgear's algorithm."""
    md5_key = "YOU_CAN_NOT_PASS"
    space = "\0"

    # Pad password to 2048 bytes
    repeat_count = 2048 // (len(password) + 1)
    remaining_space = 2048 - (repeat_count * (len(password) + 1))
    padded = (password + space) * repeat_count + space * remaining_space

    return hmac.new(
        md5_key.encode("utf-8"),
        padded.encode("utf-8"),
        hashlib.md5
    ).hexdigest()


class ProSafeCollector:
    """Collects metrics from a ProSafe Plus switch via web interface."""

    ENDPOINTS = {
        "port_statistics": "/config/monitoring_port_statistics.htm",
        "port_status": "/config/status_status.htm",
    }

    def __init__(self, host: str, password: str):
        self.host = host
        self.password = password
        self._session = None
        self._num_ports = None

    def _login(self) -> bool:
        """Login to the switch and establish session."""
        try:
            self._session = requests.Session()
            base_url = f"http://{self.host}"

            # Get login page to initialize session
            self._session.get(f"{base_url}/login.htm", timeout=5)

            # Hash password and login
            hashed = hash_password(self.password)
            response = self._session.post(
                f"{base_url}/login.htm",
                data={
                    "submitId": "pwdLogin",
                    "password": hashed,
                    "submitEnd": ""
                },
                headers={"Referer": f"{base_url}/login.htm"},
                timeout=5
            )

            # Check if we got a session cookie
            if self._session.cookies.get("SID"):
                logger.info(f"Logged into switch at {self.host}")
                return True

            logger.error("Login failed - no session cookie received")
            return False

        except Exception as e:
            logger.error(f"Login failed: {e}")
            self._session = None
            return False

    def _fetch_page(self, endpoint: str) -> str | None:
        """Fetch a page from the switch."""
        try:
            url = f"http://{self.host}{endpoint}"
            response = self._session.get(url, timeout=10)

            # Check for login redirect
            if "login" in response.text.lower()[:200]:
                logger.warning("Session expired, re-authenticating")
                if self._login():
                    response = self._session.get(url, timeout=10)
                else:
                    return None

            return response.text

        except Exception as e:
            logger.error(f"Failed to fetch {endpoint}: {e}")
            return None

    def _parse_port_statistics(self, html: str) -> dict:
        """Parse port statistics from JavaScript array in HTML."""
        data = {}

        # Extract StatisticsEntry array: StatisticsEntry[0] = '1?232204765?359217889?0';
        pattern = r"StatisticsEntry\[(\d+)\]\s*=\s*'(\d+)\?(\d+)\?(\d+)\?(\d+)'"
        matches = re.findall(pattern, html)

        for match in matches:
            _, port, rx_bytes, tx_bytes, crc_errors = match
            port_num = int(port)
            data[f"port_{port_num}_sum_rx_mbytes"] = int(rx_bytes) / 1048576
            data[f"port_{port_num}_sum_tx_mbytes"] = int(tx_bytes) / 1048576
            data[f"port_{port_num}_crc_errors"] = int(crc_errors)

        # Extract port count
        port_list_match = re.search(r"var portList\s*=\s*(\d+)", html)
        if port_list_match:
            self._num_ports = int(port_list_match.group(1))

        return data

    def _parse_port_status(self, html: str) -> dict:
        """Parse port status from JavaScript array in HTML."""
        data = {}

        # Extract portConfigEntry array: portConfigEntry[0] = '1?NAS?Up?Auto?1000M?Disable';
        # Format: port?name?Up/Down?speed_setting?actual_speed?flow_ctrl
        pattern = r"portConfigEntry\[(\d+)\]\s*=\s*'(\d+)\?([^?]*)\?([^?]+)\?([^?]+)\?([^?]+)\?([^']+)'"
        matches = re.findall(pattern, html)

        for match in matches:
            _, port, _, link_state, _, actual_speed, _ = match
            port_num = int(port)
            if link_state.lower() == "down":
                data[f"port_{port_num}_status"] = "off"
                data[f"port_{port_num}_connection_speed"] = 0
            else:
                data[f"port_{port_num}_status"] = "on"
                speed_match = re.search(r"(\d+)M", actual_speed)
                data[f"port_{port_num}_connection_speed"] = int(speed_match.group(1)) if speed_match else 0

        return data

    def collect(self) -> tuple[dict | None, int]:
        """
        Collect metrics from the switch.

        Returns:
            Tuple of (data dict or None if failed, number of ports)
        """
        # Login if needed
        if not self._session:
            if not self._login():
                return None, 0

        data = {"switch_ip": self.host}

        # Fetch port statistics
        stats_html = self._fetch_page(self.ENDPOINTS["port_statistics"])
        if stats_html:
            data.update(self._parse_port_statistics(stats_html))
        else:
            return None, 0

        # Fetch port status
        status_html = self._fetch_page(self.ENDPOINTS["port_status"])
        if status_html:
            data.update(self._parse_port_status(status_html))

        num_ports = self._num_ports or 16
        return data, num_ports
