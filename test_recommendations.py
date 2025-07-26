from supabase import create_client, Client
from ml_inventory_model import ml_model
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_recommendations():
    print("=== TESTING RECOMMENDATIONS ===")
    
    # Get data
    inventory_response = supabase.table('inventory').select('*').execute()
    inventory = inventory_response.data
    print(f"Inventory items: {len(inventory)}")
    
    sales_response = supabase.table('sales').select('*').execute()
    sales = sales_response.data
    print(f"Sales records: {len(sales)}")
    
    # Check if model is trained
    print(f"Model is trained: {ml_model.is_trained}")
    
    # Try to generate recommendations
    try:
        print("\nGenerating recommendations...")
        recommendations = ml_model.generate_ml_recommendations(inventory, sales)
        print(f"Generated {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations):
            product_name = next((item['name'] for item in inventory if item['id'] == rec['product_id']), 'Unknown')
            print(f"\nRecommendation {i+1}:")
            print(f"  Product: {product_name}")
            print(f"  Priority: {rec['priority']}")
            print(f"  Recommended Quantity: {rec['recommended_quantity']}")
            print(f"  Days Remaining: {rec['days_remaining']}")
            print(f"  Predicted Daily Demand: {rec['predicted_daily_demand']}")
            print(f"  Confidence Score: {rec['confidence_score']}")
            print(f"  Reason: {rec['reason']}")
            
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recommendations() 