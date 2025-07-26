# Smart Inventory Manager

Smart Inventory Manager is a web-based inventory management system with AI-powered purchase recommendations. It uses Flask, Supabase, and a machine learning model to help you track inventory, record sales, and get smart restocking suggestions.

## Features

- **Inventory Management:** Add, edit, and delete inventory items.
- **Sales Tracking:** Record sales and view sales history.
- **Dashboard:** See key stats like total items, low stock alerts, inventory value, and recent sales.
- **AI Recommendations:** Get machine learning-based reorder suggestions to optimize stock levels.
- **Reports:** View top-selling products and low stock items.
- **Modern UI:** Responsive frontend with a clean design.

## Tech Stack

- **Backend:** Python, Flask, Flask-CORS, Supabase
- **Frontend:** HTML, CSS, JavaScript
- **ML:** scikit-learn, pandas, numpy, joblib

## Setup Instructions

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd Stock-Sense
   ```

2. **Install Python dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure Supabase:**
   - Create a `.env` file (already present) with your Supabase URL and API key:
     ```
     SUPABASE_URL=your_supabase_url
     SUPABASE_KEY=your_supabase_key
     ```

4. **Run the backend server:**
   ```sh
   python recommendation_service.py
   ```
   The server will start at `http://127.0.0.1:5000`.

5. **Open the frontend:**
   - Open `index.html` in your browser (you may use a local server for best results).

6. **(Optional) Generate Demo Data:**
   - To populate with demo sales data, run:
     ```sh
     python create_demo_data.py
     ```

## Project Structure

- `recommendation_service.py` — Flask backend API
- `ml_inventory_model.py` — Machine learning model logic
- `app.js` — Frontend JavaScript
- `index.html` — Main frontend page
- `style.css` — Stylesheet
- `test_recommendations.py` — Test script for recommendations
- `create_demo_data.py`, `generate_historical_data.py`, `debug_data.py`, `check_table.py` — Utility scripts
- `requirements.txt` — Python dependencies
- `.env` — Supabase credentials (not committed to git)

## Usage

- Access the dashboard, manage inventory, record sales, and view AI recommendations via the web UI.
- Use the "AI Recommendations" section to get smart reorder suggestions.
- Train or retrain the ML model as needed from the recommendations page.

## License

MIT License

---

*Made with ❤️ for smarter inventory management!*
