from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_table_structure():
    try:
        # Try to get table info
        response = supabase.table('inventory').select('*').limit(1).execute()
        print("Table exists and is accessible!")
        
        # Try to insert a test record to see what columns are expected
        test_data = {
            'name': 'Test Product',
            'sku': 'TEST-001',
            'category': 'Electronics',
            'currentstock': 10,  # Try different variations
            'minstock': 2,
            'unitprice': 99.99,
            'supplier': 'Test Supplier',
            'description': 'A test product',
            'lastupdated': '2024-01-15'
        }
        
        print("Attempting to insert test data...")
        result = supabase.table('inventory').insert([test_data]).execute()
        print("Success! Test data inserted.")
        print(f"Inserted data: {result.data}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nLet's try to see what columns actually exist...")
        
        # Try different column name variations
        variations = [
            {'currentstock': 10, 'minstock': 2, 'unitprice': 99.99, 'lastupdated': '2024-01-15'},
            {'current_stock': 10, 'min_stock': 2, 'unit_price': 99.99, 'last_updated': '2024-01-15'},
            {'currentStock': 10, 'minStock': 2, 'unitPrice': 99.99, 'lastUpdated': '2024-01-15'},
            {'current_stock': 10, 'min_stock': 2, 'unit_price': 99.99, 'last_updated': '2024-01-15'}
        ]
        
        for i, variation in enumerate(variations):
            try:
                test_data = {
                    'name': f'Test Product {i}',
                    'sku': f'TEST-{i:03d}',
                    'category': 'Electronics',
                    'supplier': 'Test Supplier',
                    'description': f'A test product {i}',
                    **variation
                }
                result = supabase.table('inventory').insert([test_data]).execute()
                print(f"Success with variation {i}: {variation}")
                print(f"Inserted data: {result.data}")
                break
            except Exception as e:
                print(f"Variation {i} failed: {e}")

if __name__ == "__main__":
    check_table_structure() 