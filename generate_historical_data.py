from supabase import create_client, Client
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_historical_sales():
    """Generate historical sales data for the past 30 days"""
    print("Generating historical sales data...")
    
    # Get inventory items
    inventory_response = supabase.table('inventory').select('*').execute()
    inventory = inventory_response.data
    
    if not inventory:
        print("No inventory items found!")
        return
    
    # Generate sales for the past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    historical_sales = []
    
    for item in inventory:
        print(f"Generating sales for: {item['name']}")
        
        # Generate 2-5 sales per product over 30 days
        num_sales = random.randint(2, 5)
        
        for _ in range(num_sales):
            # Random date within the past 30 days
            random_days = random.randint(0, 30)
            sale_date = end_date - timedelta(days=random_days)
            
            # Random quantity (1-5 units)
            quantity = random.randint(1, 5)
            
            # Sale price (slightly varied from unit price)
            base_price = item.get('unitprice', 10)
            sale_price = base_price * random.uniform(0.9, 1.1)
            
            # Random customer
            customers = ['Walk-in Customer', 'Online Order', 'Corporate Client', 'Retail Store', 'Individual Customer']
            customer = random.choice(customers)
            
            sale_data = {
                'product_id': item['id'],
                'quantity': quantity,
                'sale_price': round(sale_price, 2),
                'total_amount': round(quantity * sale_price, 2),
                'customer': customer,
                'timestamp': sale_date.isoformat()
            }
            
            historical_sales.append(sale_data)
    
    # Insert historical sales
    if historical_sales:
        print(f"Inserting {len(historical_sales)} historical sales...")
        response = supabase.table('sales').insert(historical_sales).execute()
        print(f"Successfully inserted {len(response.data)} historical sales!")
    else:
        print("No historical sales to insert.")

if __name__ == "__main__":
    generate_historical_sales() 