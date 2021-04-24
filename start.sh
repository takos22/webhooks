#!/bin/bash
source venv/bin/activate
python3 -m uvicorn webhook:app --forwarded-allow-ips='*' --proxy-headers --root-path /webhooks --uds /run/uvicorn/webhooks.sock
