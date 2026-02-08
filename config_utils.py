import os, json, urllib.parse as urlparse

XRAY_CONFIG_PATH = "/usr/local/etc/xray/config.json"
APT_PROXY_PATH = "/etc/apt/apt.conf.d/99proxy"


def parse_vless(link: str) -> dict:
    """Parse VLESS link and return config dict."""
    if not link.startswith("vless://"):
        raise ValueError("This is not vless:// link.")

    link = link[8:]
    if "#" in link:
        link, _ = link.split("#", 1)

    userinfo, rest = link.split("@")
    uuid = userinfo

    if "?" in rest:
        hostport, query = rest.split("?", 1)
        params = dict(urlparse.parse_qsl(query))
    else:
        hostport = rest
        params = {}

    address, port = hostport.split(":")
    port = int(port)

    return {
        "uuid": uuid,
        "address": address,
        "port": port,
        "network": params.get("type", "tcp"),
        "security": params.get("security", "none"),
        "encryption": params.get("encryption", "none"),
        "host": params.get("host", ""),
        "path": params.get("path", "/"),
        "headerType": params.get("headerType", "none"),
    }


def build_stream_settings(cfg: dict) -> dict:
    """Generate streamSettings section for Xray config."""
    stream = {
        "network": cfg["network"],
        "security": cfg["security"]
    }

    if cfg["network"] == "tcp":
        if cfg["headerType"] == "http":
            stream["tcpSettings"] = {
                "header": {
                    "type": "http",
                    "request": {
                        "method": "GET",
                        "path": ["/"],
                        "headers": {
                            "Host": [cfg["host"]],
                            "User-Agent": ["Mozilla/5.0"],
                            "Accept-Encoding": ["gzip, deflate"],
                            "Connection": ["keep-alive"]
                        }
                    }
                }
            }

    elif cfg["network"] == "ws":
        stream["wsSettings"] = {
            "path": cfg["path"],
            "headers": {
                "Host": cfg["host"]
            }
        }

    else:
        raise ValueError(f"Can not support this network: {cfg['network']}")

    return stream


def build_config_json(cfg: dict) -> str:
    """Generate final Xray JSON config."""
    stream_settings = build_stream_settings(cfg)

    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [
            {
                "listen": "127.0.0.1",
                "port": 10808,
                "protocol": "socks",
                "settings": {"udp": True}
            }
        ],
        "outbounds": [
            {
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": cfg["address"],
                            "port": cfg["port"],
                            "users": [
                                {
                                    "id": cfg["uuid"],
                                    "encryption": cfg["encryption"]
                                }
                            ]
                        }
                    ]
                },
                "streamSettings": stream_settings
            }
        ]
    }

    return json.dumps(config, indent=2)


def apply_config(json_conf: str):
    """Write config to disk and restart Xray."""
    os.makedirs(os.path.dirname(XRAY_CONFIG_PATH), exist_ok=True)
    with open(XRAY_CONFIG_PATH, "w") as f:
        f.write(json_conf)
    os.system("systemctl restart xray")
    os.system("systemctl status xray --no-pager")


def enable_apt_proxy():
    with open(APT_PROXY_PATH, "w") as f:
        f.write(
            'Acquire::http::Proxy "socks5h://127.0.0.1:10808";\n'
            'Acquire::https::Proxy "socks5h://127.0.0.1:10808";\n'
        )
    os.system("apt update")


def disable_apt_proxy():
    if os.path.exists(APT_PROXY_PATH):
        os.remove(APT_PROXY_PATH)
    os.system("apt update")