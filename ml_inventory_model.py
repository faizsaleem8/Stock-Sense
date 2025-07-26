import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import joblib
import os

class InventoryMLModel:
    def __init__(self):
        self.demand_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.seasonal_model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = 'inventory_ml_model.pkl'
        
    def prepare_features(self, sales_data, inventory_data):
        """Prepare features for ML model"""
        features = []
        targets = []
        
        print(f"Preparing features for {len(inventory_data)} inventory items...")
        
        for item in inventory_data:
            item_id = item['id']
            item_sales = [s for s in sales_data if s['product_id'] == item_id]
            
            print(f"Product {item.get('name', 'Unknown')}: {len(item_sales)} sales records")
            
            if len(item_sales) < 3:  # Need minimum data for training
                print(f"  - Skipping: insufficient sales data (need at least 3, got {len(item_sales)})")
                continue
                
            # Create time series features
            df = pd.DataFrame(item_sales)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Aggregate by day
            daily_sales = df.groupby(df['timestamp'].dt.date).agg({
                'quantity': 'sum',
                'sale_price': 'mean'
            }).reset_index()
            
            print(f"  - Daily sales data: {len(daily_sales)} days")
            
            # Create features
            for i in range(len(daily_sales) - 7):  # Use 7 days to predict next day
                feature_row = []
                
                # Historical sales features
                feature_row.extend(daily_sales['quantity'].iloc[i:i+7].values)
                feature_row.append(daily_sales['sale_price'].iloc[i:i+7].mean())
                
                # Time-based features
                current_date = daily_sales['timestamp'].iloc[i+7]
                feature_row.append(current_date.weekday())  # Day of week
                feature_row.append(current_date.month)      # Month
                feature_row.append(current_date.day)        # Day of month
                
                # Inventory features
                feature_row.append(item.get('currentstock', 0))
                feature_row.append(item.get('minstock', 0))
                feature_row.append(item.get('unitprice', 0))
                
                # Target: next day's sales
                target = daily_sales['quantity'].iloc[i+7] if i+7 < len(daily_sales) else 0
                
                features.append(feature_row)
                targets.append(target)
            
            print(f"  - Generated {len(daily_sales) - 7} training samples")
        
        print(f"Total features generated: {len(features)}")
        return np.array(features), np.array(targets)
    
    def train_model(self, sales_data, inventory_data):
        """Train the ML model on historical data"""
        try:
            print(f"Starting ML model training...")
            print(f"Total sales records: {len(sales_data)}")
            print(f"Total inventory items: {len(inventory_data)}")
            
            features, targets = self.prepare_features(sales_data, inventory_data)
            
            print(f"Prepared features shape: {features.shape if hasattr(features, 'shape') else len(features)}")
            print(f"Prepared targets shape: {targets.shape if hasattr(targets, 'shape') else len(targets)}")
            
            if len(features) < 10:  # Need sufficient data
                print(f"Insufficient data for training. Only {len(features)} data points available. Need at least 10.")
                print("This usually means:")
                print("- Not enough sales history for individual products")
                print("- Sales data doesn't span enough days")
                print("- Products need at least 7+ days of sales data")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            
            print(f"Training set size: {len(X_train)}")
            print(f"Test set size: {len(X_test)}")
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train demand prediction model
            self.demand_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_score = self.demand_model.score(X_train_scaled, y_train)
            test_score = self.demand_model.score(X_test_scaled, y_test)
            
            print(f"Model trained successfully!")
            print(f"Training R² score: {train_score:.3f}")
            print(f"Test R² score: {test_score:.3f}")
            
            self.is_trained = True
            self.save_model()
            return True
            
        except Exception as e:
            print(f"Error training model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def train_model_simple(self, sales_data, inventory_data):
        """Simpler training method that works with less data"""
        try:
            print(f"Starting simple ML model training...")
            print(f"Total sales records: {len(sales_data)}")
            print(f"Total inventory items: {len(inventory_data)}")
            
            features = []
            targets = []
            
            for item in inventory_data:
                item_id = item['id']
                item_sales = [s for s in sales_data if s['product_id'] == item_id]
                
                print(f"Product {item.get('name', 'Unknown')}: {len(item_sales)} sales records")
                
                if len(item_sales) < 2:  # Reduced minimum requirement
                    print(f"  - Skipping: insufficient sales data (need at least 2, got {len(item_sales)})")
                    continue
                
                # Create simpler features
                df = pd.DataFrame(item_sales)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                
                # Aggregate by day
                daily_sales = df.groupby(df['timestamp'].dt.date).agg({
                    'quantity': 'sum',
                    'sale_price': 'mean'
                }).reset_index()
                
                print(f"  - Daily sales data: {len(daily_sales)} days")
                
                # Use all available data points
                for i in range(len(daily_sales) - 1):  # Use any day to predict next day
                    feature_row = []
                    
                    # Use available historical data (pad with zeros if needed)
                    historical_sales = daily_sales['quantity'].iloc[max(0, i-6):i+1].values
                    if len(historical_sales) < 7:
                        historical_sales = np.pad(historical_sales, (7 - len(historical_sales), 0), 'constant')
                    
                    feature_row.extend(historical_sales)
                    feature_row.append(daily_sales['sale_price'].iloc[max(0, i-6):i+1].mean())
                    
                    # Time-based features
                    current_date = daily_sales['timestamp'].iloc[i+1]
                    feature_row.append(current_date.weekday())
                    feature_row.append(current_date.month)
                    feature_row.append(current_date.day)
                    
                    # Inventory features
                    feature_row.append(item.get('currentstock', 0))
                    feature_row.append(item.get('minstock', 0))
                    feature_row.append(item.get('unitprice', 0))
                    
                    # Target: next day's sales
                    target = daily_sales['quantity'].iloc[i+1]
                    
                    features.append(feature_row)
                    targets.append(target)
                
                print(f"  - Generated {len(daily_sales) - 1} training samples")
            
            features = np.array(features)
            targets = np.array(targets)
            
            print(f"Total features generated: {len(features)}")
            
            if len(features) < 5:  # Reduced minimum requirement
                print(f"Insufficient data for training. Only {len(features)} data points available. Need at least 5.")
                return False
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            
            print(f"Training set size: {len(X_train)}")
            print(f"Test set size: {len(X_test)}")
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train demand prediction model
            self.demand_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_score = self.demand_model.score(X_train_scaled, y_train)
            test_score = self.demand_model.score(X_test_scaled, y_test)
            
            print(f"Simple model trained successfully!")
            print(f"Training R² score: {train_score:.3f}")
            print(f"Test R² score: {test_score:.3f}")
            
            self.is_trained = True
            self.save_model()
            return True
            
        except Exception as e:
            print(f"Error training simple model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict_demand(self, item, sales_history, days_ahead=7):
        """Predict demand for next N days"""
        if not self.is_trained:
            return 0
        
        try:
            # Prepare features for prediction
            item_sales = [s for s in sales_history if s['product_id'] == item['id']]
            
            if len(item_sales) < 7:
                return 0  # Not enough data
            
            # Get recent sales data
            df = pd.DataFrame(item_sales)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Get last 7 days of sales
            recent_sales = df.groupby(df['timestamp'].dt.date)['quantity'].sum().tail(7).values
            
            if len(recent_sales) < 7:
                recent_sales = np.pad(recent_sales, (7 - len(recent_sales), 0), 'constant')
            
            # Create feature vector
            features = []
            features.extend(recent_sales)
            features.append(df['sale_price'].mean())
            
            # Time features
            tomorrow = datetime.now() + timedelta(days=1)
            features.append(tomorrow.weekday())
            features.append(tomorrow.month)
            features.append(tomorrow.day)
            
            # Inventory features
            features.append(item.get('currentstock', 0))
            features.append(item.get('minstock', 0))
            features.append(item.get('unitprice', 0))
            
            # Make prediction
            features_scaled = self.scaler.transform([features])
            predicted_demand = self.demand_model.predict(features_scaled)[0]
            
            return max(0, predicted_demand * days_ahead)  # Predict for N days
            
        except Exception as e:
            print(f"Error predicting demand: {e}")
            return 0
    
    def generate_ml_recommendations(self, inventory_data, sales_data):
        """Generate ML-based recommendations"""
        recommendations = []
        
        # Train model if not trained
        if not self.is_trained:
            self.train_model(sales_data, inventory_data)
        
        for item in inventory_data:
            # Predict demand
            predicted_demand = self.predict_demand(item, sales_data, days_ahead=7)
            
            current_stock = item.get('currentstock', 0)
            min_stock = item.get('minstock', 0)
            
            # Calculate days of stock remaining
            daily_demand = predicted_demand / 7 if predicted_demand > 0 else 0
            days_remaining = current_stock / daily_demand if daily_demand > 0 else float('inf')
            
            # Determine if reorder is needed
            needs_reorder = (current_stock <= min_stock or days_remaining <= 7)
            
            if needs_reorder:
                # Calculate recommended order quantity using ML predictions
                lead_time_days = 7
                safety_stock = min_stock
                demand_during_lead_time = daily_demand * lead_time_days
                
                # ML-based recommendation
                recommended_quantity = max(
                    int(round(demand_during_lead_time + safety_stock - current_stock)),
                    min_stock * 2
                )
                
                # Determine priority based on ML predictions
                priority = 'low'
                if current_stock == 0:
                    priority = 'high'
                elif current_stock <= min_stock or days_remaining <= 3:
                    priority = 'high'
                elif days_remaining <= 7:
                    priority = 'medium'
                
                # Calculate confidence score based on model performance
                confidence = min(0.95, max(0.5, daily_demand / (daily_demand + 1)))
                
                # Handle infinity case for days_remaining
                days_remaining_int = 999 if days_remaining == float('inf') else max(0, int(days_remaining))
                
                recommendation = {
                    'product_id': item['id'],
                    'priority': priority,
                    'recommended_quantity': recommended_quantity,
                    'days_remaining': days_remaining_int,
                    'predicted_daily_demand': round(daily_demand, 2),
                    'confidence_score': round(confidence, 2),
                    'ml_model_used': 'RandomForest',
                    'reason': f"ML predicted {daily_demand:.1f} units/day demand. Stock will last {days_remaining_int} days."
                }
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def save_model(self):
        """Save the trained model"""
        try:
            model_data = {
                'demand_model': self.demand_model,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }
            joblib.dump(model_data, self.model_path)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self):
        """Load a previously trained model"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.demand_model = model_data['demand_model']
                self.scaler = model_data['scaler']
                self.is_trained = model_data['is_trained']
                print("Model loaded successfully")
                return True
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

# Global ML model instance
ml_model = InventoryMLModel() 