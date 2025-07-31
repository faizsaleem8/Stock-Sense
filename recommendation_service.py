from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from flask_cors import CORS
from supabase import create_client, Client
from ml_inventory_model import ml_model
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500", "http://localhost:5500"], supports_credentials=True)

def parse_naive_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt

def update_dashboard_stats():
    """Update dashboard statistics after any inventory/sales change"""
    try:
        # Get inventory stats
        inventory_response = supabase.table('inventory').select('*').execute()
        inventory = inventory_response.data
        
        total_items = sum(item.get('currentstock', 0) for item in inventory)
        low_stock_items = len([item for item in inventory if item.get('currentstock', 0) <= item.get('minstock', 0)])
        total_value = sum(item.get('currentstock', 0) * item.get('unitprice', 0) for item in inventory)
        
        # Get sales count
        sales_response = supabase.table('sales').select('*').execute()
        total_sales = len(sales_response.data)
        
        # Update dashboard stats
        stats_data = {
            'total_items': total_items,
            'low_stock_items': low_stock_items,
            'total_value': total_value,
            'total_sales': total_sales,
            'last_updated': datetime.now().isoformat()
        }
        
        # Clear old stats and insert new ones
        supabase.table('dashboard_stats').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        supabase.table('dashboard_stats').insert([stats_data]).execute()
        
        return stats_data
    except Exception as e:
        print(f"Error updating dashboard stats: {e}")
        return None

def generate_ai_recommendations():
    """Generate ML-based AI recommendations"""
    try:
        # Get inventory and sales data
        inventory_response = supabase.table('inventory').select('*').execute()
        sales_response = supabase.table('sales').select('*').execute()
        
        inventory = inventory_response.data
        sales = sales_response.data
        
        # Clear old recommendations
        supabase.table('ai_recommendations').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # Use ML model for recommendations
        ml_recommendations = ml_model.generate_ml_recommendations(inventory, sales)
        
        # Convert ML recommendations to database format
        recommendations = []
        for rec in ml_recommendations:
            recommendation_data = {
                'product_id': rec['product_id'],
                'priority': rec['priority'],
                'recommended_quantity': rec['recommended_quantity'],
                'days_remaining': rec['days_remaining'],
                'sales_velocity': rec['predicted_daily_demand'],
                'total_sold': 0,  # Will be calculated from sales data
                'reason': rec['reason'],
                'confidence_score': rec['confidence_score'],
                'ml_model_used': rec['ml_model_used']
            }
            
            supabase.table('ai_recommendations').insert([recommendation_data]).execute()
            recommendations.append(recommendation_data)
        
        return recommendations
    except Exception as e:
        print(f"Error generating AI recommendations: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.route('/train-model', methods=['POST', 'OPTIONS'])
def train_model():
    """Train the ML model on current data"""
    if request.method == 'OPTIONS':
        return '', 200
    try:
        # Get inventory and sales data
        inventory_response = supabase.table('inventory').select('*').execute()
        sales_response = supabase.table('sales').select('*').execute()
        inventory = inventory_response.data
        sales = sales_response.data
        print(f"Training model with {len(sales)} sales records and {len(inventory)} inventory items")
        # Only call the revised train_model:
        success = ml_model.train_model(sales, inventory)
        if success:
            return jsonify({
                'message': 'Model trained successfully',
                'model_info': {
                    'is_trained': ml_model.is_trained,
                    'model_type': 'RandomForest',
                    'features_used': 'Historical sales, time features, inventory levels',
                    'training_method': 'Unified'
                }
            })
        else:
            return jsonify({
                'error': 'Insufficient data for training. Need more sales history.',
                'details': {
                    'sales_count': len(sales),
                    'inventory_count': len(inventory),
                    'requirements': 'Need at least 3 training samples from sales data spanning multiple days'
                }
            }), 400

    except Exception as e:
        print(f"Error in train_model endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/model-status', methods=['GET', 'OPTIONS'])
def get_model_status():
    """Get ML model status and performance metrics"""
    if request.method == 'OPTIONS':
        return '', 200
    try:
        # Try to load existing model
        model_loaded = ml_model.load_model()
        
        return jsonify({
            'is_trained': ml_model.is_trained,
            'model_loaded': model_loaded,
            'model_type': 'RandomForest',
            'features': [
                'Last 7 days sales',
                'Average sale price',
                'Day of week',
                'Month',
                'Day of month',
                'Current stock',
                'Minimum stock',
                'Unit price'
            ],
            'prediction_horizon': '7 days',
            'model_path': ml_model.model_path
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/inventory', methods=['GET', 'OPTIONS'])
def get_inventory():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        response = supabase.table('inventory').select('*').execute()
        # Convert lowercase back to camelCase for frontend
        inventory_data = []
        for item in response.data:
            inventory_data.append({
                'id': item.get('id'),
                'name': item.get('name'),
                'sku': item.get('sku'),
                'category': item.get('category'),
                'currentStock': item.get('currentstock'),
                'minStock': item.get('minstock'),
                'unitPrice': item.get('unitprice'),
                'supplier': item.get('supplier'),
                'description': item.get('description'),
                'lastUpdated': item.get('lastupdated')
            })
        return jsonify(inventory_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/inventory', methods=['POST', 'OPTIONS'])
def add_inventory():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        
        # Validate required fields
        required_fields = ['name', 'sku', 'category', 'currentStock', 'minStock', 'unitPrice', 'supplier', 'lastUpdated']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            print(f"Validation error: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Remove id if present to let Supabase generate it
        if 'id' in data:
            del data['id']
            print("Removed id field")
        
        # Convert camelCase to lowercase for Supabase
        supabase_data = {
            'name': data['name'],
            'sku': data['sku'],
            'category': data['category'],
            'currentstock': int(data['currentStock']),
            'minstock': int(data['minStock']),
            'unitprice': float(data['unitPrice']),
            'supplier': data['supplier'],
            'description': data.get('description', ''),
            'lastupdated': data['lastUpdated']
        }
        
        print(f"Data to insert: {supabase_data}")
        response = supabase.table('inventory').insert([supabase_data]).execute()
        print(f"Supabase response: {response.data}")
        
        # Update dashboard stats after inventory change
        update_dashboard_stats()
        
        return jsonify(response.data)
    except Exception as e:
        print(f"Error in add_inventory: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/sales', methods=['GET', 'OPTIONS'])
def get_sales():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        response = supabase.table('sales').select('*, inventory(name, sku)').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sales', methods=['POST', 'OPTIONS'])
def add_sale():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        print(f"Received sale data: {data}")
        
        # Validate required fields
        required_fields = ['productId', 'quantity', 'salePrice', 'customer']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            return jsonify({'error': error_msg}), 400
        
        # Get product details
        product_response = supabase.table('inventory').select('*').eq('id', data['productId']).execute()
        if not product_response.data:
            return jsonify({'error': 'Product not found'}), 404
        
        product = product_response.data[0]
        
        # Check stock availability
        if product.get('currentstock', 0) < data['quantity']:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        # Calculate total amount
        total_amount = data['quantity'] * data['salePrice']
        
        # Create sale record
        sale_data = {
            'product_id': data['productId'],
            'quantity': data['quantity'],
            'sale_price': data['salePrice'],
            'total_amount': total_amount,
            'customer': data['customer'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Insert sale
        sale_response = supabase.table('sales').insert([sale_data]).execute()
        
        # Update inventory stock
        new_stock = product.get('currentstock', 0) - data['quantity']
        supabase.table('inventory').update({
            'currentstock': new_stock,
            'lastupdated': datetime.now().date().isoformat()
        }).eq('id', data['productId']).execute()
        
        # Update dashboard stats
        update_dashboard_stats()
        
        # Generate new AI recommendations
        generate_ai_recommendations()
        
        return jsonify(sale_response.data)
    except Exception as e:
        print(f"Error in add_sale: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard', methods=['GET', 'OPTIONS'])
def get_dashboard():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        # Get latest dashboard stats
        response = supabase.table('dashboard_stats').select('*').order('created_at', desc=True).limit(1).execute()
        
        if response.data:
            return jsonify(response.data[0])
        else:
            # Generate initial stats if none exist
            stats = update_dashboard_stats()
            return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations', methods=['GET', 'OPTIONS'])
def get_recommendations():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        response = supabase.table('ai_recommendations').select('*, inventory(name, sku, supplier)').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations', methods=['POST', 'OPTIONS'])
def generate_recommendations():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        recommendations = generate_ai_recommendations()
        return jsonify(recommendations)
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations', methods=['POST'])
def recommendations():
    data = request.get_json()
    inventory = data.get('inventory', [])
    sales = data.get('sales', [])
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    recommendations = []

    for item in inventory:
        # Calculate sales velocity (items sold per day over last 30 days)
        item_sales = [
            sale for sale in sales
            if sale['productId'] == item['id'] and parse_naive_datetime(sale['timestamp']) >= thirty_days_ago
        ]
        total_sold = sum(sale['quantity'] for sale in item_sales)
        sales_velocity = total_sold / 30 if total_sold > 0 else 0
        days_remaining = item['currentStock'] / sales_velocity if sales_velocity > 0 else float('inf')
        needs_reorder = item['currentStock'] <= item['minStock'] or days_remaining <= 7
        if needs_reorder:
            lead_time_days = 7
            safety_stock = item['minStock']
            demand_during_lead_time = sales_velocity * lead_time_days
            recommended_quantity = max(
                int(round(demand_during_lead_time + safety_stock - item['currentStock'])),
                item['minStock'] * 2
            )
            priority = 'low'
            if item['currentStock'] == 0:
                priority = 'high'
            elif item['currentStock'] <= item['minStock'] or days_remaining <= 3:
                priority = 'high'
            elif days_remaining <= 7:
                priority = 'medium'
            recommendations.append({
                'item': item,
                'priority': priority,
                'recommendedQuantity': recommended_quantity,
                'daysRemaining': max(0, int(days_remaining)),
                'salesVelocity': round(sales_velocity, 2),
                'totalSold': total_sold
            })
    # Sort by priority (high first) and then by days remaining
    priority_order = {'high': 3, 'medium': 2, 'low': 1}
    recommendations.sort(key=lambda x: (-priority_order[x['priority']], x['daysRemaining']))
    return jsonify(recommendations)

if __name__ == '__main__':
    app.run(debug=True) 