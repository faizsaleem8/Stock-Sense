import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
import joblib
import os

class InventoryMLModel:
    def __init__(self):
        self.demand_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = 'inventory_ml_model.pkl'

    def prepare_features(self, sales_data, inventory_data):
        # Set fixed current date for all time series (edit as needed)
        current_date = pd.to_datetime('2025-07-29').date()
        features = []
        targets = []

        print(f"Preparing features for {len(inventory_data)} inventory items (adaptive window size)...")
        for item in inventory_data:
            item_id = item["id"]
            item_sales = [s for s in sales_data if s["product_id"] == item_id]
            if not item_sales:
                continue
            df = pd.DataFrame(item_sales)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            first_day = df["timestamp"].dt.date.min()
            date_range = pd.date_range(start=first_day, end=current_date, freq="D")
            daily_sales = (
                df.groupby(df["timestamp"].dt.date)
                .agg({"quantity": "sum", "sale_price": "mean"})
                .reindex(date_range.date, fill_value=0)
                .reset_index()
            )
            # Robustly ensure first column is always named 'date'
            first_col = daily_sales.columns[0]
            if first_col != "date":
                daily_sales.rename(columns={first_col: "date"}, inplace=True)
            daily_sales["sale_price"] = daily_sales["sale_price"].replace(0, np.nan)
            daily_sales["sale_price"] = daily_sales["sale_price"].ffill().fillna(0)
            days_in_inventory = len(daily_sales)
            if days_in_inventory < 7:
                continue
            window_size = min(30, max(2, round(days_in_inventory / 5)))
            print(f"Product {item.get('name', str(item_id))}: {days_in_inventory} days in inventory, window size {window_size}")
            for i in range(len(daily_sales) - window_size):
                win = daily_sales.iloc[i : i + window_size]
                # Pad LEFT with zeros to always get length 30
                sales_window = win['quantity'].values
                pad_len = 30 - window_size
                padded_sales = np.pad(sales_window, (pad_len, 0), 'constant')
                feature_row = list(padded_sales)
                feature_row.append(win['sale_price'].mean())
                # Features for the prediction day
                target_idx = i + window_size
                target_day = pd.to_datetime(daily_sales["date"].iloc[target_idx])
                feature_row.append(target_day.weekday())
                feature_row.append(target_day.month)
                feature_row.append(target_day.day)
                feature_row.append(item.get("currentstock", 0))
                feature_row.append(item.get("minstock", 0))
                feature_row.append(item.get("unitprice", 0))
                feature_row.append(window_size)
                target = daily_sales["quantity"].iloc[target_idx]
                features.append(feature_row)
                targets.append(target)
            print(f"  - Generated {len(daily_sales) - window_size} training samples.")

        print(f"Total features generated: {len(features)}")
        return np.array(features), np.array(targets)

    def train_model(self, sales_data, inventory_data):
        """Train the ML model with adaptive, per-product window size."""
        try:
            print("Starting ML model training (adaptive window)...")
            features, targets = self.prepare_features(sales_data, inventory_data)
            print(f"Prepared features shape: {features.shape}")
            print(f"Prepared targets shape: {targets.shape}")
            if len(features) < 3:
                print("Insufficient data for training. Need at least 3 samples.")
                return False
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            self.demand_model.fit(X_train_scaled, y_train)
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

    def predict_demand(self, item, sales_history, days_ahead=7):
        """Predict demand for next N days for single item using adaptive window."""
        if not self.is_trained:
            return 0
        try:
            item_sales = [s for s in sales_history if s["product_id"] == item["id"]]
            if not item_sales:
                return 0
            df = pd.DataFrame(item_sales)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            first_day = df["timestamp"].dt.date.min()
            current_date = pd.to_datetime('2025-07-29').date()
            date_range = pd.date_range(start=first_day, end=current_date, freq="D")
            daily_sales = (
                df.groupby(df["timestamp"].dt.date)
                .agg({"quantity": "sum", "sale_price": "mean"})
                .reindex(date_range.date, fill_value=0)
                .reset_index()
            )
            # Robustly ensure first column is always named 'date'
            first_col = daily_sales.columns[0]
            if first_col != "date":
                daily_sales.rename(columns={first_col: "date"}, inplace=True)
            daily_sales["sale_price"] = daily_sales["sale_price"].replace(0, np.nan)
            daily_sales["sale_price"] = daily_sales["sale_price"].ffill().fillna(0)
            days_in_inventory = len(daily_sales)
            if days_in_inventory < 7:
                return 0
            window_size = min(30, max(2, round(days_in_inventory / 5)))
            if len(daily_sales) < window_size:
                return 0
            win = daily_sales.iloc[-window_size:]
            sales_window = win['quantity'].values
            padded_sales = np.pad(sales_window, (30 - window_size, 0), 'constant')
            features = list(padded_sales)
            features.append(win['sale_price'].mean())
            tomorrow = current_date + timedelta(days=1)
            features.append(tomorrow.weekday())
            features.append(tomorrow.month)
            features.append(tomorrow.day)
            features.append(item.get("currentstock", 0))
            features.append(item.get("minstock", 0))
            features.append(item.get("unitprice", 0))
            features.append(window_size)
            features_scaled = self.scaler.transform([features])
            predicted_demand = self.demand_model.predict(features_scaled)[0]
            return max(0, predicted_demand * days_ahead)
        except Exception as e:
            print(f"Error predicting demand: {e}")
            return 0

    def generate_ml_recommendations(self, inventory_data, sales_data):
        """Generate ML-based recommendations using trained model."""
        recommendations = []
        if not self.is_trained:
            print("Model not trained, cannot generate recommendations.")
            return recommendations
        for item in inventory_data:
            predicted_weekly_demand = self.predict_demand(item, sales_data, days_ahead=7)
            current_stock = item.get("currentstock", 0)
            min_stock = item.get("minstock", 0)
            daily_demand = predicted_weekly_demand / 7 if predicted_weekly_demand > 0 else 0
            days_remaining = current_stock / daily_demand if daily_demand > 0 else float("inf")
            needs_reorder = (current_stock <= min_stock or days_remaining <= 7)
            if needs_reorder:
                lead_time_days = 7
                safety_stock = min_stock
                demand_during_lead_time = daily_demand * lead_time_days
                recommended_quantity = max(
                    int(round(demand_during_lead_time + safety_stock - current_stock)), min_stock * 2
                )
                priority = "low"
                if current_stock == 0:
                    priority = "high"
                elif current_stock <= min_stock or days_remaining <= 3:
                    priority = "high"
                elif days_remaining <= 7:
                    priority = "medium"
                confidence = min(0.95, max(0.5, daily_demand / (daily_demand + 1)))
                days_remaining_int = 999 if days_remaining == float("inf") else max(0, int(days_remaining))
                recommendations.append({
                    "product_id": item["id"],
                    "priority": priority,
                    "recommended_quantity": recommended_quantity,
                    "days_remaining": days_remaining_int,
                    "predicted_daily_demand": round(daily_demand, 2),
                    "confidence_score": round(confidence, 2),
                    "ml_model_used": "RandomForest",
                    "reason": f"ML predicted {daily_demand:.1f} units/day demand. Stock will last {days_remaining_int} days."
                })
        return recommendations

    def save_model(self):
        try:
            model_data = {
                "demand_model": self.demand_model,
                "scaler": self.scaler,
                "is_trained": self.is_trained
            }
            joblib.dump(model_data, self.model_path)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {e}")

    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.demand_model = model_data["demand_model"]
                self.scaler = model_data["scaler"]
                self.is_trained = model_data["is_trained"]
                print("Model loaded successfully")
                return True
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

# Global ML model instance
ml_model = InventoryMLModel()
