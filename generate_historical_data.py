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
    """
    Generate realistic historical sales data for the ML model's July 2025 window
    """
    print("Generating historical sales data...")

    inventory_response = supabase.table('inventory').select('*').execute()
    inventory = inventory_response.data

    if not inventory:
        print("No inventory items found!")
        return

    # ML code expects sales between 2025-06-29 and 2025-07-29
    end_date = datetime(2025, 7, 29, 12, 0, 0)
    start_date = end_date - timedelta(days=30)
    historical_sales = []

    for item in inventory:
        print(f"Generating sales for: {item['name']}")
        base_price = item.get('unitprice', 10)

        # 15–31 sales, spread by date per product
        days_with_sales = sorted(random.sample(range(31), random.randint(15, 31)))
        for offset in days_with_sales:
            sale_date = end_date - timedelta(days=offset)
            quantity = random.randint(1, 5)
            sale_price = base_price * random.uniform(0.9, 1.1)
            customer = random.choice([
                'Walk-in Customer', 'Online Order',
                'Corporate Client', 'Retail Store', 'Individual Customer'
            ])
            sale_data = {
                'product_id': item['id'],
                'quantity': quantity,
                'sale_price': round(sale_price, 2),
                'total_amount': round(quantity * sale_price, 2),
                'customer': customer,
                'timestamp': sale_date.isoformat()
            }
            historical_sales.append(sale_data)

    if historical_sales:
        print(f"Inserting {len(historical_sales)} historical sales...")
        response = supabase.table('sales').insert(historical_sales).execute()
        num_inserted = len(getattr(response, 'data', []))
        print(f"Successfully inserted {num_inserted} historical sales!")
    else:
        print("No historical sales to insert.")

if __name__ == "__main__":
    generate_historical_sales()
