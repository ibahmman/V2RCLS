# 🎯 راهنمای راه‌اندازی VLESS Proxy روی سرور لینوکسی

## هدف

اتصال یک سرور Ubuntu به یک کانفیگ VLESS به‌صورت کلاینت برای استفاده در:

* apt
* curl
* docker

بدون تغییر کل شبکه و بدون ریسک قطع SSH.

---

# 🧩 معماری

```
[ Ubuntu Server ]
        │
        │ (SOCKS5 : 127.0.0.1:10808)
        ▼
     Xray Client
        │
        ▼
   VLESS Server
        │
        ▼
     Internet
```

---

# 1️⃣ نصب ابزارها

## نصب پیش‌نیازها

```bash
apt update
apt install -y curl ca-certificates gnupg
```

## نصب Xray

```bash
bash <(curl -Ls https://github.com/XTLS/Xray-install/raw/main/install-release.sh)
```

## بررسی

```bash
xray version
systemctl status xray
```

---

# 2️⃣ ساخت کانفیگ

## ساختار لینک VLESS

```
vless://UUID@host:port?type=ws&security=tls&path=/ws&host=example.com
```

## پارامترهای مهم

| پارامتر    | توضیح       |
| ---------- | ----------- |
| UUID       | شناسه کاربر |
| host:port  | آدرس سرور   |
| type       | tcp / ws    |
| security   | tls / none  |
| path       | مسیر ws     |
| host       | هدر Host    |
| headerType | http        |

---

## مسیر فایل کانفیگ

```
/usr/local/etc/xray/config.json
```

---

## نمونه‌ها

### TCP ساده

```json
"streamSettings": {
  "network": "tcp",
  "security": "none"
}
```

### TCP + HTTP

```json
"tcpSettings": {
  "header": {
    "type": "http",
    "request": {
      "headers": {
        "Host": ["example.com"]
      }
    }
  }
}
```

### WebSocket

```json
"streamSettings": {
  "network": "ws",
  "security": "none",
  "wsSettings": {
    "path": "/ws",
    "headers": {
      "Host": "example.com"
    }
  }
}
```

### WebSocket + TLS

```json
"streamSettings": {
  "network": "ws",
  "security": "tls",
  "wsSettings": {
    "path": "/ws",
    "headers": {
      "Host": "example.com"
    }
  }
}
```

---

# 3️⃣ اجرای سرویس

```bash
systemctl restart xray
systemctl status xray
```

---

# 4️⃣ تست اتصال

```bash
curl --socks5 127.0.0.1:10808 https://ifconfig.me
```

اگر IP تغییر کرد، اتصال برقرار است.

---

# 5️⃣ تونل کردن apt

## فعال‌سازی

```bash
nano /etc/apt/apt.conf.d/99proxy
```

محتوا:

```conf
Acquire::http::Proxy "socks5h://127.0.0.1:10808";
Acquire::https::Proxy "socks5h://127.0.0.1:10808";
```

## تست

```bash
apt update
```

---

# 6️⃣ غیرفعال‌سازی

```bash
rm /etc/apt/apt.conf.d/99proxy
apt update
```

---

# 🧠 الگوریتم دیتکت کانفیگ

```
if type == ws:
    → wsSettings
elif type == tcp and headerType == http:
    → tcp + http header
else:
    → tcp ساده
```

---

# ⚠️ نکات مهم

## مزایا

* بدون تغییر routing کل سیستم
* بدون قطع SSH
* ساده و قابل کنترل

## محدودیت‌ها

* فقط برنامه‌های proxy-aware
* کل سیستم از VPN عبور نمی‌کند

## خطاهای رایج

| مشکل            | علت                    |
| --------------- | ---------------------- |
| وصل نمی‌شود     | اشتباه در host یا path |
| TLS خطا         | دامنه اشتباه           |
| apt کار نمی‌کند | socks5h اشتباه         |

---

# 🚀 جمع‌بندی

مراحل:

1. نصب Xray
2. ساخت config از VLESS
3. اجرای سرویس
4. تست اتصال
5. اعمال proxy روی apt
