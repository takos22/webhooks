#!/bin/bash
source venv/bin/activate
python3 -m uvicorn --forwarded-allow-ips='*' --proxy-headers --root-path /webhooks --uds /run/uvicorn/webhooks.sock
