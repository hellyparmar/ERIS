import socket
import time
import sys

def wait_for_port(port, host='localhost', timeout=60):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"✅ Port {port} is open!")
                return True
        except (socket.timeout, ConnectionRefusedError):
            if time.time() - start_time > timeout:
                print(f"❌ Timed out waiting for port {port}")
                return False
            print(f"⏳ Waiting for port {port}...")
            time.sleep(2)

if __name__ == "__main__":
    wait_for_port(8000)
