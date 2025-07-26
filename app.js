// Global application state
let inventory = [];
let sales = [];
let currentEditingItem = null;

// Sample data from JSON
const sampleInventory = [
    {
        "id": "1",
        "name": "MacBook Pro 16\"",
        "sku": "MBP16-001",
        "category": "Electronics",
        "currentStock": 5,
        "minStock": 3,
        "unitPrice": 2499.99,
        "supplier": "Apple Inc.",
        "description": "16-inch MacBook Pro with M2 Pro chip",
        "lastUpdated": "2025-07-20"
    },
    {
        "id": "2", 
        "name": "iPhone 15 Pro",
        "sku": "IP15P-001",
        "category": "Electronics",
        "currentStock": 2,
        "minStock": 5,
        "unitPrice": 999.99,
        "supplier": "Apple Inc.",
        "description": "iPhone 15 Pro 128GB in Natural Titanium",
        "lastUpdated": "2025-07-20"
    },
    {
        "id": "3",
        "name": "iPad Air",
        "sku": "IPAD-A-001", 
        "category": "Electronics",
        "currentStock": 8,
        "minStock": 4,
        "unitPrice": 599.99,
        "supplier": "Apple Inc.",
        "description": "iPad Air 10.9-inch with M1 chip",
        "lastUpdated": "2025-07-20"
    },
    {
        "id": "4",
        "name": "Wireless Mouse",
        "sku": "MOUSE-001",
        "category": "Office Supplies",
        "currentStock": 15,
        "minStock": 10,
        "unitPrice": 29.99,
        "supplier": "Logitech",
        "description": "Wireless optical mouse with USB receiver",
        "lastUpdated": "2025-07-20"  
    },
    {
        "id": "5",
        "name": "A4 Copy Paper",
        "sku": "PAPER-A4-001",
        "category": "Office Supplies", 
        "currentStock": 3,
        "minStock": 10,
        "unitPrice": 8.99,
        "supplier": "Staples",
        "description": "500 sheets A4 white copy paper",
        "lastUpdated": "2025-07-20"
    }
];

const sampleSales = [
    {
        "id": "1",
        "productId": "1", 
        "quantity": 2,
        "salePrice": 2499.99,
        "timestamp": "2025-07-25T10:30:00",
        "customer": "TechCorp Ltd"
    },
    {
        "id": "2",
        "productId": "2",
        "quantity": 3, 
        "salePrice": 999.99,
        "timestamp": "2025-07-24T14:15:00",
        "customer": "Individual Customer"
    },
    {
        "id": "3",
        "productId": "4",
        "quantity": 5,
        "salePrice": 29.99,
        "timestamp": "2025-07-23T09:45:00", 
        "customer": "Office Solutions Inc"
    },
    {
        "id": "4",
        "productId": "3",
        "quantity": 1,
        "salePrice": 599.99,
        "timestamp": "2025-07-22T16:20:00",
        "customer": "Creative Agency"
    },
    {
        "id": "5",  
        "productId": "5",
        "quantity": 7,
        "salePrice": 8.99,
        "timestamp": "2025-07-21T11:10:00",
        "customer": "Small Business Co"
    }
];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeData();
    setupEventListeners();
    updateDashboard();
    renderInventory();
    renderSalesHistory();
    generateRecommendations();
    updateReports();
});

// Data Management
async function initializeData() {
    // Fetch inventory from backend (Supabase)
    try {
        const response = await fetch('http://127.0.0.1:5000/inventory');
        if (!response.ok) throw new Error('Failed to fetch inventory');
        inventory = await response.json();
    } catch (error) {
        showToast('Error loading inventory: ' + error.message, 'error');
        inventory = [];
    }
    // Sales still local for now
    const storedSales = localStorage.getItem('sales');
    if (!storedSales) {
        sales = [...sampleSales];
        saveSales();
    } else {
        sales = JSON.parse(storedSales);
    }
}

async function saveInventory() {
    // Save all inventory items to backend (Supabase)
    // For simplicity, only add new items (POST). For full sync, you would implement PUT/PATCH/DELETE as well.
    // Here, we assume add/edit always POSTs the current item.
    // (You may want to improve this for real-world use.)
    // This function is called after add/edit/delete.
    // We'll re-fetch inventory after any change.
    await initializeData();
    renderInventory();
    updateDashboard();
}

async function addOrUpdateInventoryItem(item, isEdit = false) {
    try {
        const response = await fetch('http://127.0.0.1:5000/inventory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(item)
        });
        if (!response.ok) throw new Error('Failed to save item');
        await saveInventory();
        showToast(isEdit ? 'Item updated successfully!' : 'Item added successfully!');
    } catch (error) {
        showToast('Error saving item: ' + error.message, 'error');
    }
}

function saveSales() {
    localStorage.setItem('sales', JSON.stringify(sales));
}

// Event Listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            switchSection(this.dataset.section);
        });
    });
    
    // Add item button
    document.getElementById('add-item-btn').addEventListener('click', openAddItemModal);
    
    // Modal close buttons
    document.getElementById('close-modal').addEventListener('click', closeItemModal);
    document.getElementById('cancel-item').addEventListener('click', closeItemModal);
    document.getElementById('close-sale-modal').addEventListener('click', closeSaleModal);
    document.getElementById('cancel-sale').addEventListener('click', closeSaleModal);
    
    // Form submissions
    document.getElementById('save-item').addEventListener('click', saveItem);
    document.getElementById('save-sale').addEventListener('click', recordSale);
    
    // Sale button
    document.getElementById('new-sale-btn').addEventListener('click', openSaleModal);
    
    // Search and filter
    document.getElementById('inventory-search').addEventListener('input', filterInventory);
    document.getElementById('category-filter').addEventListener('change', filterInventory);
    
    // Refresh recommendations
    document.getElementById('refresh-recommendations').addEventListener('click', generateRecommendations);
    
    // Modal backdrop click
    document.getElementById('item-modal').addEventListener('click', function(e) {
        if (e.target === this) closeItemModal();
    });
    document.getElementById('sale-modal').addEventListener('click', function(e) {
        if (e.target === this) closeSaleModal();
    });
    
    // Product selection price auto-fill
    setupProductSelection();
}

function setupProductSelection() {
    const productSelect = document.getElementById('sale-product');
    productSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption.dataset.price) {
            document.getElementById('sale-price').value = selectedOption.dataset.price;
        } else {
            document.getElementById('sale-price').value = '';
        }
    });
}

// Navigation
function switchSection(sectionName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
    
    // Update sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionName).classList.add('active');
    
    // Update content based on section
    if (sectionName === 'dashboard') {
        updateDashboard();
    } else if (sectionName === 'inventory') {
        renderInventory();
    } else if (sectionName === 'sales') {
        renderSalesHistory();
    } else if (sectionName === 'recommendations') {
        loadRecommendations();
    } else if (sectionName === 'reports') {
        updateReports();
    }
}

// Dashboard Functions
async function updateDashboard() {
    try {
        const response = await fetch('http://127.0.0.1:5000/dashboard');
        if (!response.ok) throw new Error('Failed to fetch dashboard data');
        const dashboardData = await response.json();
        
        document.getElementById('total-items').textContent = dashboardData.total_items || 0;
        document.getElementById('low-stock-items').textContent = dashboardData.low_stock_items || 0;
        document.getElementById('total-value').textContent = formatCurrency(dashboardData.total_value || 0);
        document.getElementById('total-sales').textContent = dashboardData.total_sales || 0;
        
        await renderRecentActivity();
    } catch (error) {
        showToast('Error loading dashboard: ' + error.message, 'error');
        // Fallback to local calculation
        const totalItems = inventory.reduce((sum, item) => sum + item.currentStock, 0);
        const lowStockItems = inventory.filter(item => item.currentStock <= item.minStock).length;
        const totalValue = inventory.reduce((sum, item) => sum + (item.currentStock * item.unitPrice), 0);
        const recentSales = sales.length;
        
        document.getElementById('total-items').textContent = totalItems;
        document.getElementById('low-stock-items').textContent = lowStockItems;
        document.getElementById('total-value').textContent = formatCurrency(totalValue);
        document.getElementById('total-sales').textContent = recentSales;
        
        await renderRecentActivity();
    }
}

async function renderRecentActivity() {
    try {
        const response = await fetch('http://127.0.0.1:5000/sales');
        if (!response.ok) throw new Error('Failed to fetch sales');
        const salesData = await response.json();
        
        const container = document.getElementById('recent-activity');
        const recentSales = salesData.slice(-5).reverse();
        
        if (recentSales.length === 0) {
            container.innerHTML = '<p class="text-secondary">No recent activity</p>';
            return;
        }
        
        const html = recentSales.map(sale => {
            const product = sale.inventory;
            const date = new Date(sale.timestamp);
            
            return `
                <div class="activity-item">
                    <div class="activity-icon">💰</div>
                    <div class="activity-content">
                        <h4>Sale: ${product ? product.name : 'Unknown Product'}</h4>
                        <p>Quantity: ${sale.quantity} • ${formatCurrency(sale.sale_price)}</p>
                    </div>
                    <div class="activity-time">${formatDate(date)}</div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading recent activity:', error);
        const container = document.getElementById('recent-activity');
        container.innerHTML = '<p class="text-secondary">Error loading recent activity</p>';
    }
}

// Inventory Functions
function renderInventory() {
    const container = document.getElementById('inventory-grid');
    const filteredInventory = getFilteredInventory();
    
    if (filteredInventory.length === 0) {
        container.innerHTML = '<p class="text-secondary">No inventory items found</p>';
        return;
    }
    
    const html = filteredInventory.map(item => {
        const stockStatus = getStockStatus(item);
        return `
            <div class="inventory-item">
                <div class="inventory-item-header">
                    <div>
                        <h3 class="inventory-item-title">${item.name}</h3>
                        <p class="inventory-item-sku">SKU: ${item.sku}</p>
                    </div>
                    <div class="inventory-item-actions">
                        <button class="btn-icon" onclick="editItem('${item.id}')" title="Edit">✏️</button>
                        <button class="btn-icon" onclick="deleteItem('${item.id}')" title="Delete">🗑️</button>
                    </div>
                </div>
                <div class="inventory-item-info">
                    <div class="info-item">
                        <span class="info-label">Category</span>
                        <span class="info-value">${item.category}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Price</span>
                        <span class="info-value">${formatCurrency(item.unitPrice)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Supplier</span>
                        <span class="info-value">${item.supplier}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Min Stock</span>
                        <span class="info-value">${item.minStock}</span>
                    </div>
                </div>
                <div class="stock-indicator ${stockStatus.class}">
                    <span>${stockStatus.icon}</span>
                    <span>${item.currentStock} in stock • ${stockStatus.text}</span>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

function getFilteredInventory() {
    const searchTerm = document.getElementById('inventory-search').value.toLowerCase();
    const categoryFilter = document.getElementById('category-filter').value;
    
    return inventory.filter(item => {
        const matchesSearch = item.name.toLowerCase().includes(searchTerm) || 
                            item.sku.toLowerCase().includes(searchTerm);
        const matchesCategory = !categoryFilter || item.category === categoryFilter;
        
        return matchesSearch && matchesCategory;
    });
}

function filterInventory() {
    renderInventory();
}

function getStockStatus(item) {
    if (item.currentStock === 0) {
        return { class: 'stock-out', icon: '❌', text: 'Out of Stock' };
    } else if (item.currentStock <= item.minStock) {
        return { class: 'stock-low', icon: '⚠️', text: 'Low Stock' };
    } else {
        return { class: 'stock-good', icon: '✅', text: 'Good Stock' };
    }
}

// Modal Functions
function openAddItemModal() {
    currentEditingItem = null;
    document.getElementById('modal-title').textContent = 'Add New Item';
    clearItemForm();
    document.getElementById('item-modal').classList.remove('hidden');
}

function editItem(itemId) {
    const item = inventory.find(i => i.id === itemId);
    if (!item) return;
    
    currentEditingItem = item;
    document.getElementById('modal-title').textContent = 'Edit Item';
    
    // Populate form
    document.getElementById('item-name').value = item.name;
    document.getElementById('item-sku').value = item.sku;
    document.getElementById('item-category').value = item.category;
    document.getElementById('item-stock').value = item.currentStock;
    document.getElementById('item-min-stock').value = item.minStock;
    document.getElementById('item-price').value = item.unitPrice;
    document.getElementById('item-supplier').value = item.supplier;
    document.getElementById('item-description').value = item.description || '';
    
    document.getElementById('item-modal').classList.remove('hidden');
}

function closeItemModal() {
    document.getElementById('item-modal').classList.add('hidden');
    clearItemForm();
    currentEditingItem = null;
}

function clearItemForm() {
    document.getElementById('item-form').reset();
}

function saveItem() {
    const formData = {
        name: document.getElementById('item-name').value,
        sku: document.getElementById('item-sku').value,
        category: document.getElementById('item-category').value,
        currentStock: parseInt(document.getElementById('item-stock').value),
        minStock: parseInt(document.getElementById('item-min-stock').value),
        unitPrice: parseFloat(document.getElementById('item-price').value),
        supplier: document.getElementById('item-supplier').value,
        description: document.getElementById('item-description').value,
        lastUpdated: new Date().toISOString().split('T')[0]
    };
    
    // Validation
    if (!formData.name || !formData.sku || !formData.category || formData.currentStock < 0 || formData.minStock < 0 || formData.unitPrice < 0) {
        showToast('Please fill in all required fields with valid values', 'error');
        return;
    }
    
    addOrUpdateInventoryItem(
        currentEditingItem ? { ...formData, id: currentEditingItem.id } : formData,
        !!currentEditingItem
    );
    closeItemModal();
}

function deleteItem(itemId) {
    if (confirm('Are you sure you want to delete this item?')) {
        // This function will be updated to call a backend endpoint for deletion
        // For now, it will just remove from local inventory and save
        inventory = inventory.filter(item => item.id !== itemId);
        saveInventory();
        renderInventory();
        updateDashboard();
        showToast('Item deleted successfully!');
    }
}

// Sales Functions
function openSaleModal() {
    populateProductDropdown();
    document.getElementById('sale-modal').classList.remove('hidden');
}

function closeSaleModal() {
    document.getElementById('sale-modal').classList.add('hidden');
    document.getElementById('sale-form').reset();
}

function populateProductDropdown() {
    const select = document.getElementById('sale-product');
    const availableProducts = inventory.filter(item => item.currentStock > 0);
    
    // Clear existing options
    select.innerHTML = '<option value="">Select Product</option>';
    
    // Add product options
    availableProducts.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = `${item.name} (${item.currentStock} available)`;
        option.setAttribute('data-price', item.unitPrice);
        select.appendChild(option);
    });
    
    // If no products available
    if (availableProducts.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No products available';
        option.disabled = true;
        select.appendChild(option);
    }
}

async function recordSale() {
    const productId = document.getElementById('sale-product').value;
    const quantity = parseInt(document.getElementById('sale-quantity').value);
    const salePrice = parseFloat(document.getElementById('sale-price').value);
    const customer = document.getElementById('sale-customer').value || 'Walk-in Customer';
    
    // Validation
    if (!productId || !quantity || !salePrice || quantity <= 0 || salePrice <= 0) {
        showToast('Please fill in all required fields with valid values', 'error');
        return;
    }
    
    try {
        const response = await fetch('http://127.0.0.1:5000/sales', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                productId,
                quantity,
                salePrice,
                customer
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to record sale');
        }
        
        const saleData = await response.json();
        
        // Refresh inventory and sales data
        await initializeData();
        renderInventory();
        renderSalesHistory();
        updateDashboard();
        closeSaleModal();
        
        showToast(`Sale recorded successfully! ${quantity} items sold.`);
    } catch (error) {
        showToast('Error recording sale: ' + error.message, 'error');
    }
}

async function renderSalesHistory() {
    try {
        const response = await fetch('http://127.0.0.1:5000/sales');
        if (!response.ok) throw new Error('Failed to fetch sales');
        const salesData = await response.json();
        
        const tbody = document.getElementById('sales-table-body');
        
        if (salesData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No sales recorded</td></tr>';
            return;
        }
        
        const html = salesData.slice(0, 20).map(sale => {
            const product = sale.inventory;
            const date = new Date(sale.timestamp);
            
            return `
                <tr>
                    <td>${formatDate(date)}</td>
                    <td>${product ? product.name : 'Unknown Product'}</td>
                    <td>${sale.quantity}</td>
                    <td>${formatCurrency(sale.sale_price)}</td>
                    <td>${sale.customer}</td>
                    <td>${formatCurrency(sale.total_amount)}</td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = html;
    } catch (error) {
        showToast('Error loading sales history: ' + error.message, 'error');
        // Fallback to local sales data
        const tbody = document.getElementById('sales-table-body');
        const recentSales = sales.slice(0, 20);
        
        if (recentSales.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No sales recorded</td></tr>';
            return;
        }
        
        const html = recentSales.map(sale => {
            const product = inventory.find(item => item.id === sale.productId);
            const date = new Date(sale.timestamp);
            const total = sale.quantity * sale.salePrice;
            
            return `
                <tr>
                    <td>${formatDate(date)}</td>
                    <td>${product ? product.name : 'Unknown Product'}</td>
                    <td>${sale.quantity}</td>
                    <td>${formatCurrency(sale.salePrice)}</td>
                    <td>${sale.customer}</td>
                    <td>${formatCurrency(total)}</td>
                </tr>
            `;
        }).join('');
        
        tbody.innerHTML = html;
    }
}

// AI Recommendations
async function generateRecommendations() {
    const container = document.getElementById('recommendations-container');
    container.innerHTML = `<div class="card"><div class="card__body"><p class="text-center">🔄 Generating ML-based recommendations...</p></div></div>`;
    try {
        const response = await fetch('http://127.0.0.1:5000/recommendations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) throw new Error('Failed to fetch recommendations');
        const recommendations = await response.json();
        renderRecommendations(recommendations);
    } catch (error) {
        container.innerHTML = `<div class="card"><div class="card__body"><p class="text-center text-error">❌ Error generating recommendations: ${error.message}</p></div></div>`;
    }
}

async function loadRecommendations() {
    const container = document.getElementById('recommendations-container');
    container.innerHTML = `<div class="card"><div class="card__body"><p class="text-center">🔄 Loading ML recommendations...</p></div></div>`;
    try {
        const response = await fetch('http://127.0.0.1:5000/recommendations');
        if (!response.ok) throw new Error('Failed to fetch recommendations');
        const recommendations = await response.json();
        renderRecommendations(recommendations);
    } catch (error) {
        container.innerHTML = `<div class="card"><div class="card__body"><p class="text-center text-error">❌ Error loading recommendations: ${error.message}</p></div></div>`;
    }
}

async function trainMLModel() {
    const container = document.getElementById('recommendations-container');
    container.innerHTML = `<div class="card"><div class="card__body"><p class="text-center">🤖 Training ML model...</p></div></div>`;
    try {
        const response = await fetch('http://127.0.0.1:5000/train-model', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to train model');
        }
        const result = await response.json();
        showToast('ML model trained successfully!', 'success');
        await loadRecommendations();
    } catch (error) {
        container.innerHTML = `<div class="card"><div class="card__body"><p class="text-center text-error">❌ Error training model: ${error.message}</p></div></div>`;
        showToast('Error training model: ' + error.message, 'error');
    }
}

async function showModelStatus() {
    try {
        const response = await fetch('http://127.0.0.1:5000/model-status');
        if (!response.ok) throw new Error('Failed to get model status');
        const status = await response.json();
        
        const container = document.getElementById('recommendations-container');
        container.innerHTML = `
            <div class="card">
                <div class="card__body">
                    <h3>🤖 ML Model Status</h3>
                    <div class="model-info">
                        <p><strong>Model Type:</strong> ${status.model_type}</p>
                        <p><strong>Is Trained:</strong> ${status.is_trained ? '✅ Yes' : '❌ No'}</p>
                        <p><strong>Model Loaded:</strong> ${status.model_loaded ? '✅ Yes' : '❌ No'}</p>
                        <p><strong>Prediction Horizon:</strong> ${status.prediction_horizon}</p>
                        <h4>Features Used:</h4>
                        <ul>
                            ${status.features.map(feature => `<li>${feature}</li>`).join('')}
                        </ul>
                        <div class="model-actions">
                            <button onclick="trainMLModel()" class="btn btn-primary">Train Model</button>
                            <button onclick="loadRecommendations()" class="btn btn-secondary">Load Recommendations</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        showToast('Error getting model status: ' + error.message, 'error');
    }
}

function renderRecommendations(recommendations) {
    const container = document.getElementById('recommendations-container');
    
    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = `
            <div class="card">
                <div class="card__body">
                    <p class="text-center">✅ All items are well stocked! No immediate reorders needed.</p>
                    <div class="text-center" style="margin-top: 1rem;">
                        <button onclick="showModelStatus()" class="btn btn-secondary">🤖 ML Model Status</button>
                        <button onclick="trainMLModel()" class="btn btn-primary">Train ML Model</button>
                    </div>
                </div>
            </div>
        `;
        return;
    }
    
    const html = recommendations.map(rec => {
        const item = rec.inventory || rec.item; // Handle both database and old format
        const itemName = item ? item.name : 'Unknown Product';
        const itemSku = item ? item.sku : 'Unknown SKU';
        const itemSupplier = item ? item.supplier : 'Unknown Supplier';
        const confidenceScore = rec.confidence_score || 0.5;
        const mlModelUsed = rec.ml_model_used || 'RandomForest';
        
        return `
            <div class="recommendation-item">
                <div class="recommendation-header">
                    <div>
                        <h3>${itemName}</h3>
                        <p class="text-secondary">SKU: ${itemSku} • Supplier: ${itemSupplier}</p>
                        <p class="text-secondary">🤖 ML Model: ${mlModelUsed} • Confidence: ${(confidenceScore * 100).toFixed(1)}%</p>
                    </div>
                    <span class="recommendation-priority priority-${rec.priority}">${rec.priority} Priority</span>
                </div>
                <div class="recommendation-details">
                    <div class="recommendation-metric">
                        <div class="metric-value">${rec.recommended_quantity || rec.recommendedQuantity}</div>
                        <div class="metric-label">Recommended Order</div>
                    </div>
                    <div class="recommendation-metric">
                        <div class="metric-value">${item ? (item.currentstock || item.currentStock) : 'N/A'}</div>
                        <div class="metric-label">Current Stock</div>
                    </div>
                    <div class="recommendation-metric">
                        <div class="metric-value">${rec.days_remaining || rec.daysRemaining}</div>
                        <div class="metric-label">Days Remaining</div>
                    </div>
                    <div class="recommendation-metric">
                        <div class="metric-value">${rec.sales_velocity || rec.salesVelocity}</div>
                        <div class="metric-label">Predicted Daily Demand</div>
                    </div>
                    <div class="recommendation-metric">
                        <div class="metric-value">${formatCurrency((rec.recommended_quantity || rec.recommendedQuantity) * (item ? (item.unitprice || item.unitPrice) : 0))}</div>
                        <div class="metric-label">Estimated Cost</div>
                    </div>
                </div>
                <div class="recommendation-reason">
                    <p><strong>ML Analysis:</strong> ${rec.reason || 'No reason provided'}</p>
                </div>
            </div>
        `;
    }).join('');
    
    // Add model status button
    const modelStatusButton = `
        <div class="text-center" style="margin-top: 1rem;">
            <button onclick="showModelStatus()" class="btn btn-secondary">🤖 ML Model Status</button>
            <button onclick="trainMLModel()" class="btn btn-primary">Train ML Model</button>
        </div>
    `;
    
    container.innerHTML = html + modelStatusButton;
}

// Reports Functions
function updateReports() {
    renderTopProducts();
    renderLowStockItems();
}

function renderTopProducts() {
    const container = document.getElementById('top-products-list');
    const productSales = {};
    
    // Calculate total sales by product
    sales.forEach(sale => {
        if (!productSales[sale.productId]) {
            productSales[sale.productId] = { quantity: 0, revenue: 0 };
        }
        productSales[sale.productId].quantity += sale.quantity;
        productSales[sale.productId].revenue += sale.quantity * sale.salePrice;
    });
    
    // Convert to array and sort by quantity sold
    const topProducts = Object.entries(productSales)
        .map(([productId, data]) => ({
            product: inventory.find(item => item.id === productId),
            ...data
        }))
        .filter(item => item.product)
        .sort((a, b) => b.quantity - a.quantity)
        .slice(0, 5);
    
    if (topProducts.length === 0) {
        container.innerHTML = '<p class="text-secondary">No sales data available</p>';
        return;
    }
    
    const html = topProducts.map(item => `
        <div class="product-item">
            <div class="item-info">
                <h4>${item.product.name}</h4>
                <p>${item.quantity} units sold</p>
            </div>
            <div class="item-value">${formatCurrency(item.revenue)}</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function renderLowStockItems() {
    const container = document.getElementById('low-stock-list');
    const lowStockItems = inventory
        .filter(item => item.currentStock <= item.minStock)
        .sort((a, b) => (a.currentStock / a.minStock) - (b.currentStock / b.minStock));
    
    if (lowStockItems.length === 0) {
        container.innerHTML = '<p class="text-secondary">All items are well stocked!</p>';
        return;
    }
    
    const html = lowStockItems.map(item => {
        const stockRatio = item.currentStock / item.minStock;
        let statusText = 'Low Stock';
        if (item.currentStock === 0) statusText = 'Out of Stock';
        
        return `
            <div class="stock-item">
                <div class="item-info">
                    <h4>${item.name}</h4>
                    <p>${item.currentStock} / ${item.minStock} min • ${statusText}</p>
                </div>
                <div class="item-value" style="color: ${item.currentStock === 0 ? 'var(--color-error)' : 'var(--color-warning)'}">
                    ${Math.round(stockRatio * 100)}%
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const messageElement = document.getElementById('toast-message');
    
    messageElement.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 300);
    }, 3000);
}