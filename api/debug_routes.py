
import sys
import os

# Add root to python path
sys.path.insert(0, os.getcwd())

from api.main import app

print("Inspecting app.routes:")
found = False
for route in app.routes:
    if hasattr(route, "path"):
        print(f"Route: {route.path}")
        if "customer" in route.path:
            found = True

if found:
    print("\nSUCCESS: Customer routes found!")
else:
    print("\nFAILURE: Customer routes NOT found.")
