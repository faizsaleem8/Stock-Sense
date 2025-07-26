from supabase import create_client, Client
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_demo_data():
    """Create comprehensive demo data for ML training"""
    print("Creating comprehensive demo data...")
    
    # Clear existing sales data first
    print("Clearing existing sales data...")
    supabase.table('sales').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    
    # Get inventory items
    inventory_response = supabase.table('inventory').select('*').execute()
    inventory = inventory_response.data
    
    if not inventory:
        print("No inventory items found!")
        return
    
    # Create realistic sales patterns
    sales_data = []
    
    # Define product categories and their sales patterns
    product_patterns = {
        'Pepsi': {'base_demand': 5, 'volatility': 0.3, 'weekend_boost': 1.5},
        'Chupa chups': {'base_demand': 3, 'volatility': 0.4, 'weekend_boost': 1.2},
        'LG AC': {'base_demand': 1, 'volatility': 0.2, 'weekend_boost': 1.0},
        'fawfawfwaf': {'base_demand': 2, 'volatility': 0.5, 'weekend_boost': 1.3},
        'Hersheys': {'base_demand': 4, 'volatility': 0.3, 'weekend_boost': 1.4},
        'Rubics Cube': {'base_demand': 2, 'volatility': 0.4, 'weekend_boost': 1.1},
        'CleanPlus': {'base_demand': 3, 'volatility': 0.3, 'weekend_boost': 1.2},
        'Sourpunk': {'base_demand': 2, 'volatility': 0.4, 'weekend_boost': 1.3},
        'Chair': {'base_demand': 1, 'volatility': 0.2, 'weekend_boost': 1.0},
        'iphone': {'base_demand': 1, 'volatility': 0.1, 'weekend_boost': 1.1}
    }
    
    # Generate 60 days of sales data (2 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    for item in inventory:
        product_name = item['name']
        pattern = product_patterns.get(product_name, {'base_demand': 2, 'volatility': 0.3, 'weekend_boost': 1.2})
        
        print(f"Generating sales for: {product_name}")
        
        # Generate daily sales for 60 days
        for day_offset in range(60):
            sale_date = start_date + timedelta(days=day_offset)
            
            # Skip some days randomly (realistic pattern)
            if random.random() < 0.1:  # 10% chance of no sales on a day
                continue
            
            # Calculate base demand for this day
            base_demand = pattern['base_demand']
            
            # Add weekend boost
            if sale_date.weekday() >= 5:  # Weekend
                base_demand *= pattern['weekend_boost']
            
            # Add some randomness
            demand = max(0, int(base_demand * random.uniform(0.5, 1.5)))
            
            if demand > 0:
                # Generate 1-3 sales per day
                num_sales = random.randint(1, min(3, demand))
                
                for _ in range(num_sales):
                    quantity = random.randint(1, min(5, demand // num_sales))
                    
                    # Sale price with some variation
                    base_price = item.get('unitprice', 10)
                    sale_price = base_price * random.uniform(0.9, 1.1)
                    
                    # Random customer types
                    customers = ['Walk-in Customer', 'Online Order', 'Corporate Client', 'Retail Store', 'Individual Customer']
                    customer = random.choice(customers)
                    
                    # Random time during the day
                    hour = random.randint(9, 20)  # 9 AM to 8 PM
                    minute = random.randint(0, 59)
                    sale_datetime = sale_date.replace(hour=hour, minute=minute)
                    
                    sale_data = {
                        'product_id': item['id'],
                        'quantity': quantity,
                        'sale_price': round(sale_price, 2),
                        'total_amount': round(quantity * sale_price, 2),
                        'customer': customer,
                        'timestamp': sale_datetime.isoformat()
                    }
                    
                    sales_data.append(sale_data)
    
    # Insert all sales data
    if sales_data:
        print(f"Inserting {len(sales_data)} sales records...")
        
        # Insert in batches of 50 to avoid timeout
        batch_size = 50
        for i in range(0, len(sales_data), batch_size):
            batch = sales_data[i:i + batch_size]
            response = supabase.table('sales').insert(batch).execute()
            print(f"Inserted batch {i//batch_size + 1}/{(len(sales_data) + batch_size - 1)//batch_size}")
        
        print(f"Successfully created demo data with {len(sales_data)} sales records!")
        print("This data spans 60 days with realistic sales patterns for ML training.")
    else:
        print("No sales data generated!")

if __name__ == "__main__":
    create_demo_data() 