"""
Keep-Alive Pinger for Render

Prevents Render free tier from spinning down by pinging the health endpoint every 5 minutes.
"""
import threading
import time
import os
import httpx


def start_keep_alive():
    """Start a background thread to ping the service and keep it alive."""
    url = os.environ.get('RENDER_EXTERNAL_URL')
    if not url:
        return
    
    health_url = f"{url}/health"
    
    def ping():
        print(f"Keep-alive pinger started. Target: {health_url}")
        while True:
            try:
                response = httpx.get(health_url, timeout=10)
                print(f"Keep-alive ping to {health_url}: {response.status_code}")
            except Exception as e:
                print(f"Keep-alive ping failed: {e}")
            time.sleep(300)  # Ping every 5 minutes
    
    thread = threading.Thread(target=ping)
    thread.daemon = True
    thread.start()
