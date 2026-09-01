
import requests
import sys
import os
from datetime import datetime
import time
import random

# Add current directory to path to import generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from generate_petpooja_data import PetpoojaRestaurantDataGenerator

def simulate_orders(num_orders=50):
    print(f"🚀 Starting simulation: Generating {num_orders} new live orders...")
    
    generator = PetpoojaRestaurantDataGenerator()
    base_url = "http://localhost:8000/api/petpooja"
    
    count = 0
    start_time = time.time()
    
    for i in range(num_orders):
        # Generate a random valid timestamp for today
        now = datetime.now()
        
        # Generate simulated order data using the existing generator class
        # We use a dummy ID and timestamp because the API will assign real ones
        mock_order = generator.generate_order(i, now)
        
        payload = {
            "order_type": mock_order["order_type"],
            "table_number": mock_order["table_number"],
            "items": mock_order["items"]
        }
        
        try:
            response = requests.post(f"{base_url}/orders/create", json=payload)
            if response.status_code == 200:
                count += 1
                sys.stdout.write(f"\r✅ Created Order {count}/{num_orders}: {response.json()['order']['order_id']} ({mock_order['order_type']})")
                sys.stdout.flush()
            else:
                print(f"\n❌ Failed to create order: {response.text}")
        except Exception as e:
            print(f"\n❌ Error connecting to API: {e}")
            break
            
        # Small delay to mimic real-time influx (optional, but faster for demo prep)
        # time.sleep(0.05) 
        
    duration = time.time() - start_time
    print(f"\n\n✨ Simulation Complete!")
    print(f"📊 Added {count} new orders in {duration:.2f} seconds.")
    print(f"💰 Total simulated revenue has been updated in the dashboard.")

if __name__ == "__main__":
    simulate_orders()
