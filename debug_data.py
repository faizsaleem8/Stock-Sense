from supabase import create_client, Client

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def analyze_data():
    print("=== DATA ANALYSIS ===")
    
    # Get inventory data
    inventory_response = supabase.table('inventory').select('*').execute()
    inventory = inventory_response.data
    print(f"Inventory items: {len(inventory)}")
    
    # Get sales data
    sales_response = supabase.table('sales').select('*').execute()
    sales = sales_response.data
    print(f"Sales records: {len(sales)}")
    
    if not sales:
        print("❌ No sales data found!")
        return
    
    # Analyze sales data
    print("\n=== SALES ANALYSIS ===")
    
    # Check dates
    from datetime import datetime
    dates = []
    for sale in sales:
        try:
            date = datetime.fromisoformat(sale['timestamp'].replace('Z', '+00:00'))
            dates.append(date.date())
        except Exception as e:
            print(f"Error parsing date: {sale['timestamp']} - {e}")
    
    unique_dates = set(dates)
    print(f"Sales span {len(unique_dates)} unique days: {sorted(unique_dates)}")
    
    # Check product IDs
    product_ids = set(sale['product_id'] for sale in sales)
    inventory_ids = set(item['id'] for item in inventory)
    
    print(f"Sales reference {len(product_ids)} unique products: {product_ids}")
    print(f"Inventory has {len(inventory_ids)} unique products: {inventory_ids}")
    
    # Check for matching products
    matching_products = product_ids.intersection(inventory_ids)
    print(f"Products with both inventory and sales: {len(matching_products)}")
    
    if not matching_products:
        print("❌ No products have both inventory and sales data!")
        return
    
    # Analyze sales per product
    print("\n=== SALES PER PRODUCT ===")
    for product_id in matching_products:
        product_sales = [s for s in sales if s['product_id'] == product_id]
        product_name = next((item['name'] for item in inventory if item['id'] == product_id), 'Unknown')
        
        print(f"\nProduct: {product_name} (ID: {product_id})")
        print(f"  Sales count: {len(product_sales)}")
        
        # Check date spread
        product_dates = []
        for sale in product_sales:
            try:
                date = datetime.fromisoformat(sale['timestamp'].replace('Z', '+00:00'))
                product_dates.append(date.date())
            except:
                pass
        
        unique_product_dates = set(product_dates)
        print(f"  Sales span {len(unique_product_dates)} days: {sorted(unique_product_dates)}")
        
        if len(unique_product_dates) < 2:
            print(f"  ⚠️  WARNING: Sales all on same day - need temporal spread for ML training")
        
        if len(product_sales) < 3:
            print(f"  ⚠️  WARNING: Only {len(product_sales)} sales - need at least 3 for training")

if __name__ == "__main__":
    analyze_data() 