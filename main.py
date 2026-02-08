import os, sys, platform
from config_utils import parse_vless, build_config_json, apply_config
from config_utils import enable_apt_proxy, disable_apt_proxy

XRAY_INSTALL_CMD = "bash <(curl -Ls https://github.com/XTLS/Xray-install/raw/main/install-release.sh)"


def ensure_root():
    if platform.system() != "Windows":
        # روی لینوکس فقط چک کن
        if os.geteuid() != 0:
            print("❌ Run with sudo please.")
            sys.exit(1)
    else:
        # روی ویندوز، فقط هشدار بده ولی ادامه بده
        print("⚠️ Running on Windows: root check skipped")
        

def install_dependencies():
    """
    نصب ابزارهای پایه و Xray
    """
    print("📦 Installing basic dependencies...")
    os.system("apt update")
    os.system("apt install -y curl gnupg ca-certificates lsb-release software-properties-common")
    print("✅ Base dependencies installed.")

    # نصب Xray اگر نصب نشده باشد
    print("📦 Checking Xray...")
    ret = os.system("systemctl status xray > /dev/null 2>&1")
    if ret != 0:
        print("📥 Installing Xray...")
        os.system(XRAY_INSTALL_CMD)
        print("✅ Xray installed.")
    else:
        print("✅ Xray already installed.")

def menu():
    print("""
1 - set VLESS config
2 - test connection
3 - apt tunnel (enable proxy)
4 - apt detunnel (disable proxy)
q - quit
""")

def test_connection():
    os.system("curl --socks5 127.0.0.1:10808 https://ifconfig.me")

if __name__ == "__main__":
    ensure_root()
    install_dependencies()  # نصب خودکار پیش از منو

    while True:
        menu()
        cmd = input("Command: ").strip()
        match cmd:
            case "1":
                link = input("VLESS link:\n").strip()
                try:
                    cfg = parse_vless(link)
                    json_conf = build_config_json(cfg)
                    apply_config(json_conf)
                    print("✅ Config set successfully.")
                except Exception as e:
                    print("❌ Error:", e)
            case "2":
                test_connection()
            case "3":
                enable_apt_proxy()
            case "4":
                disable_apt_proxy()
            case "q":
                break
            case _:
                print("❌ Invalid command.")