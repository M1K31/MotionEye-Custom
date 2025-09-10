# motionEye Security Guide

This document provides guidance on how to secure your motionEye installation.

## Securing the Web Interface with a Reverse Proxy

By default, the motionEye web interface is served over unencrypted HTTP. To secure it with HTTPS, you should place it behind a reverse proxy. This is a standard and highly recommended practice.

Below are example configurations for three popular reverse proxy servers.

**Prerequisites:**
*   You have a domain name or a dynamic DNS service pointing to your server.
*   You have installed one of the following reverse proxy servers.
*   In `motioneye.conf`, it is recommended to set `webcontrol_localhost true` so that the web interface is only accessible through the proxy.

---

### 1. Nginx

Nginx is a high-performance, open-source web server and reverse proxy.

**Example Configuration (`/etc/nginx/sites-available/motioneye`):**
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;

    # SSL Certificate paths (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**For more details, see the [Nginx Documentation](https://nginx.org/en/docs/).**

---

### 2. Apache

The Apache HTTP Server is another widely-used, free and open-source web server.

**Example Configuration (`/etc/apache2/sites-available/motioneye.conf`):**
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com

    # SSL Certificate paths (managed by Certbot)
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/your-domain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/your-domain.com/privkey.pem

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8765/
    ProxyPassReverse / http://127.0.0.1:8765/
</VirtualHost>
```

**For more details, see the [Apache Documentation](https://httpd.apache.org/docs/).**

---

### 3. Caddy

Caddy is a modern, powerful web server with automatic HTTPS. It is known for its simple configuration.

**Example Configuration (`Caddyfile`):**
```
your-domain.com {
    reverse_proxy 127.0.0.1:8765
}
```
Caddy will automatically provision and renew a TLS certificate for `your-domain.com`.

**For more details, see the [Caddy Documentation](https://caddyserver.com/docs/).**

---

## Securing MQTT with TLS

The Home Assistant integration can be configured to use an encrypted TLS connection to your MQTT broker. This is highly recommended if your broker is accessible over a network.

**To enable MQTT TLS:**
1.  In the motionEye web UI, open the main settings panel.
2.  Navigate to the "MQTT Integration" section.
3.  Enable the **"Enable TLS"** checkbox.
4.  If your MQTT broker uses a self-signed certificate or a custom Certificate Authority (CA), you must provide the path to the CA certificate file in the **"CA Certificate Path"** field. If you are using a standard, publicly trusted certificate, you can leave this field blank.
5.  Apply the settings. motionEye will restart and attempt to connect to your broker using a secure connection.
```
