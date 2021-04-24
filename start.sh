#!/bin/bash
source venv/bin/activate
python3 -m uvicorn webhook:app --forwarded-allow-ips='*' --proxy-headers --uds /run/uvicorn/webhooks.sock
