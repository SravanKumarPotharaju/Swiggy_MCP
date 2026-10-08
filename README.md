# SmartFlow

An agentic food ordering and order-tracking automation platform powered by FastAPI, MCP (Model Context Protocol), Redis, and LangGraph.

> 📖 **Full System Architecture & Feature Matrix:** See [SMARTFLOW_FEATURES_AND_ARCHITECTURE.md](file:///Users/auto/Desktop/SmartFlow/SMARTFLOW_FEATURES_AND_ARCHITECTURE.md) for complete details on all features, design choices, and system workflows.

## Project Structure

```
smartflow/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── addresses.py
│   │   ├── restaurants.py
│   │   ├── cart.py
│   │   ├── payment.py
│   │   ├── orders.py
│   │   └── tracking.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── mcp/
│   │   ├── client.py
│   │   ├── tools.py
│   │   └── schemas.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── food_service.py
│   │   ├── payment_service.py
│   │   ├── order_service.py
│   │   └── tracking_service.py
│   │
│   ├── workers/
│   │   ├── tracking_worker.py
│   │   └── notification_worker.py
│   │
│   └── models/
│       └── schemas.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup & Installation

1. Activate your virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Access API Documentation:
   - Interactive Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

# Swiggy_MCP
