from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Literal, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    lead_time_days: int

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0)
    expected_delivery_date: str
    notes: Optional[str] = None

class RestockRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    forecasted_demand: int
    trend: str
    unit_cost: float
    lead_time_days: int
    suggested_quantity: int
    recommended_quantity: int
    line_total: float

class RestockRecommendationsResponse(BaseModel):
    budget: float
    full_restock_cost: float
    recommended_total: float
    remaining_budget: float
    items: List[RestockRecommendation]

class RestockOrderItemRequest(BaseModel):
    sku: str
    quantity: int = Field(gt=0)

class CreateRestockOrderRequest(BaseModel):
    budget: float = Field(ge=0)
    items: List[RestockOrderItemRequest] = Field(min_length=1)

class RestockOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockOrderItem]
    total_cost: float
    budget: float
    status: str
    submitted_date: str
    lead_time_days: int
    expected_delivery: str

# Field names match what TasksModal.vue sends and reads (camelCase dueDate)
class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    priority: Literal["high", "medium", "low"] = "medium"
    dueDate: str

class Task(CreateTaskRequest):
    id: str
    status: Literal["pending", "completed"]

# In-memory store for submitted restock orders (lost on restart, like the rest of the mock data)
restock_orders: list = []

# In-memory task store; newest first, matching how the client prepends new tasks
tasks: list = []
next_task_id = 1

# Sort weight per forecast trend: rising demand is restocked first
TREND_PRIORITY = {"increasing": 0, "stable": 1, "decreasing": 2}

def build_restock_candidates(warehouse: Optional[str] = None, category: Optional[str] = None) -> list:
    """Join demand forecasts to inventory by SKU and compute each item's suggested quantity."""
    forecasts_by_sku = {f["item_sku"]: f for f in demand_forecasts}
    candidates = []
    for item in apply_filters(inventory_items, warehouse, category):
        forecast = forecasts_by_sku.get(item["sku"])
        if not forecast:
            continue
        # Target stock = forecast demand for the period plus the reorder point as a
        # safety buffer, so after the period's demand is met stock is still at the
        # reorder threshold. Order whatever on-hand stock falls short of that target.
        suggested = max(0, forecast["forecasted_demand"] + item["reorder_point"] - item["quantity_on_hand"])
        candidates.append({
            "sku": item["sku"],
            "name": item["name"],
            "category": item["category"],
            "warehouse": item["warehouse"],
            "quantity_on_hand": item["quantity_on_hand"],
            "reorder_point": item["reorder_point"],
            "forecasted_demand": forecast["forecasted_demand"],
            "trend": forecast["trend"],
            "unit_cost": item["unit_cost"],
            "lead_time_days": forecast["lead_time_days"],
            "suggested_quantity": suggested,
        })
    return candidates

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/restocking/recommendations", response_model=RestockRecommendationsResponse)
def get_restock_recommendations(
    budget: float,
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Recommend restock quantities from the demand forecast, filled up to a budget."""
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative")

    candidates = build_restock_candidates(warehouse, category)

    # Rank by trend first (increasing > stable > decreasing), then by how short the
    # item is relative to its forecast demand (suggested / forecast), largest first.
    def rank_key(c):
        shortfall_ratio = c["suggested_quantity"] / c["forecasted_demand"] if c["forecasted_demand"] else 0
        return (TREND_PRIORITY.get(c["trend"].lower(), len(TREND_PRIORITY)), -shortfall_ratio)
    candidates.sort(key=rank_key)

    # Greedy fill: give each ranked item as many units as the remaining budget allows
    # (a partial fill is fine). An item that doesn't fit doesn't stop the loop, because
    # cheaper items further down the list may still fit in what is left.
    # Money is tracked in integer cents: repeatedly subtracting float line totals drifts
    # (e.g. 18.9899999 left for an 18.99 item), which would make floor() drop a unit.
    remaining_cents = round(budget * 100)
    full_restock_cost = 0.0
    for c in candidates:
        full_restock_cost += c["suggested_quantity"] * c["unit_cost"]
        cost_cents = round(c["unit_cost"] * 100)
        affordable = remaining_cents // cost_cents if cost_cents > 0 else c["suggested_quantity"]
        qty = min(c["suggested_quantity"], affordable)
        c["recommended_quantity"] = qty
        c["line_total"] = round(qty * c["unit_cost"], 2)
        remaining_cents -= qty * cost_cents

    recommended_total = round(sum(c["line_total"] for c in candidates), 2)
    return {
        "budget": budget,
        "full_restock_cost": round(full_restock_cost, 2),
        "recommended_total": recommended_total,
        "remaining_budget": round(budget - recommended_total, 2),
        "items": candidates,
    }

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restock order. Prices are taken from inventory, never from the client."""
    inventory_by_sku = {item["sku"]: item for item in inventory_items}
    lead_by_sku = {f["item_sku"]: f["lead_time_days"] for f in demand_forecasts}

    order_items = []
    for req_item in request.items:
        item = inventory_by_sku.get(req_item.sku)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {req_item.sku} not found")
        # Reprice from the server-side unit_cost so a client can't submit its own prices
        order_items.append({
            "sku": item["sku"],
            "name": item["name"],
            "quantity": req_item.quantity,
            "unit_cost": item["unit_cost"],
            "line_total": round(req_item.quantity * item["unit_cost"], 2),
            "lead_time_days": lead_by_sku.get(item["sku"], 0),
        })

    total_cost = round(sum(i["line_total"] for i in order_items), 2)
    # Compare in cents so an order that exactly matches the budget isn't rejected by float noise
    if round(total_cost * 100) > round(request.budget * 100):
        raise HTTPException(
            status_code=400,
            detail=f"Order total {total_cost:.2f} exceeds budget {request.budget:.2f}"
        )

    submitted = datetime.now().replace(microsecond=0)
    # The order is complete only when its slowest item arrives, so the order's lead
    # time is the maximum across its items rather than an average.
    lead_time_days = max(i["lead_time_days"] for i in order_items)
    n = len(restock_orders) + 1
    order = {
        "id": str(n),
        "order_number": f"RST-{submitted.year}-{n:04d}",
        "items": order_items,
        "total_cost": total_cost,
        "budget": request.budget,
        "status": "Submitted",
        "submitted_date": submitted.isoformat(),
        "lead_time_days": lead_time_days,
        "expected_delivery": (submitted + timedelta(days=lead_time_days)).isoformat(),
    }
    restock_orders.append(order)
    return order

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """List submitted restock orders, newest first.

    Global filters are not applied: these are supplier purchase orders, not customer orders.
    """
    return list(reversed(restock_orders))

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a supplier purchase order to cover a backlog item's shortfall."""
    if not any(b["id"] == request.backlog_item_id for b in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")
    # One PO per backlog item: the dashboard shows a single Create/View PO button per row
    # and GET /api/purchase-orders/{backlog_item_id} looks up exactly one PO.
    if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
        raise HTTPException(status_code=409, detail=f"Backlog item {request.backlog_item_id} already has a purchase order")

    # Derive the next id from the max existing number rather than len(), so ids stay
    # unique even if purchase_orders.json is seeded with non-contiguous entries.
    next_n = max((int(po["id"].split("-")[-1]) for po in purchase_orders), default=0) + 1
    po = {
        "id": f"PO-{next_n:04d}",
        **request.model_dump(),
        "status": "pending",
        "created_date": datetime.now().replace(microsecond=0).isoformat(),
    }
    # Appending to the shared list also makes /api/backlog report has_purchase_order=True
    purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order raised for a backlog item."""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")
    return po

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """List user-created tasks (the client merges these with its built-in mock tasks)."""
    return tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a task. New tasks start as pending."""
    global next_task_id
    # Prefixed string ids so they can never collide with the client's mock tasks,
    # which use plain integer ids (1, 2, 3...) and are merged into the same list.
    task = {"id": f"task-{next_task_id}", **request.model_dump(), "status": "pending"}
    next_task_id += 1
    tasks.insert(0, task)
    return task

def find_task(task_id: str) -> dict:
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed (the client sends no body)."""
    task = find_task(task_id)
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task."""
    task = find_task(task_id)
    tasks.remove(task)
    return {"message": f"Task {task_id} deleted"}

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
