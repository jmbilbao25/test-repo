import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, BackgroundTasks

app = FastAPI(
    title="Async Banking Analytics & Fraud Detection API",
    version="1.0.0"
)


# Pydantic schema for incoming transaction payloads
class Transaction(BaseModel):
    transaction_id: str = Field(..., example="tx_106")
    account_id: str = Field(..., example="acc_1")
    amount: float = Field(..., gt=0, example=150.00)
    category: str = Field(..., example="groceries")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# In-memory transaction database (simulating a database table)
db_transactions: List[Dict] = [
    {"transaction_id": "tx_101", "account_id": "acc_1", "amount": 120.50, "category": "groceries",
     "timestamp": "2026-08-14T10:00:00Z"},
    {"transaction_id": "tx_102", "account_id": "acc_1", "amount": 45.00, "category": "dining",
     "timestamp": "2026-08-14T11:30:00Z"},
    {"transaction_id": "tx_103", "account_id": "acc_1", "amount": 310.00, "category": "electronics",
     "timestamp": "2026-08-14T12:15:00Z"},
    {"transaction_id": "tx_104", "account_id": "acc_2", "amount": 15.00, "category": "transport",
     "timestamp": "2026-08-14T08:20:00Z"},
    {"transaction_id": "tx_105", "account_id": "acc_3", "amount": 2200.00, "category": "travel",
     "timestamp": "2026-08-14T09:45:00Z"},
]


# ---------------------------------------------------------
# ASYNC I/O SIMULATIONS (AsyncIO)
# ---------------------------------------------------------

async def simulate_mainframe_check(account_id: str) -> bool:
    """
    Simulates an outbound network call to a legacy core-banking
    mainframe system (150ms latency).
    """

    await asyncio.sleep(0.15)
    # Assume all test accounts starting with 'acc_' are valid
    return account_id.startswith("acc_")


async def log_fraud_alert_async(transaction_id: str, score: float):
    """
    Simulates firing an asynchronous Webhook/Event to a fraud operations center.
    """

    await asyncio.sleep(0.05)
    print(f"⚠️ [ALERT] High anomaly score on TX {transaction_id}: Z-Score = {score:.2f}")


# ---------------------------------------------------------
# COMPUTATIONAL ENGINES (NumPy & Pandas)
# ---------------------------------------------------------

def run_numpy_fraud_detection(new_amount: float, existing_amounts: List[float], threshold: float = 2.0) -> Dict:
    """
    Calculates transaction Z-Score using NumPy vectorization.
    """

    if len(existing_amounts) < 2:
        return {"is_anomaly": False, "z_score": 0.0, "mean_spend": new_amount, "std_dev": 0.0}

    arr = np.array(existing_amounts, dtype=np.float64)
    mean = float(np.mean(arr))
    std = float(np.std(arr))

    if std == 0:
        z_score = 0.0
    else:
        z_score = float((new_amount - mean) / std)

    return {
        "is_anomaly": abs(z_score) > threshold,
        "z_score": round(z_score, 2),
        "mean_spend": round(mean, 2),
        "std_dev": round(std, 2)
    }


def run_pandas_account_analytics(account_id: str) -> Dict:
    """
    Generates account-level summary metrics using Pandas.
    """

    df = pd.DataFrame(db_transactions)
    acc_df = df[df["account_id"] == account_id]

    if acc_df.empty:
        raise HTTPException(status_code=404, detail=f"Account '{account_id}' not found.")

    total_spent = float(acc_df["amount"].sum())
    avg_transaction = float(acc_df["amount"].mean())
    category_breakdown = acc_df.groupby("category")["amount"].sum().to_dict()
    tx_count = int(acc_df["amount"].count())

    return {
        "account_id": account_id,
        "metrics": {
            "total_spent": round(total_spent, 2),
            "avg_transaction": round(avg_transaction, 2),
            "total_transactions": tx_count,
        },
        "spend_by_category": category_breakdown
    }


# ---------------------------------------------------------
# API ENDPOINTS (FastAPI)
# ---------------------------------------------------------

@app.post("/v1/transactions", status_code=201)
async def process_transaction(tx: Transaction, background_tasks: BackgroundTasks):
    """
    In-flight transaction processing:
    1. Async mainframe validation.
    2. Vectorized Z-Score calculation via NumPy.
    3. Background fraud alert dispatch.
    """

    # 1. Async network validation check
    is_valid = await simulate_mainframe_check(tx.account_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid account ID")

    # 2. Extract historic amounts for account
    history = [t["amount"] for t in db_transactions if t["account_id"] == tx.account_id]

    # 3. Perform NumPy anomaly check
    fraud_eval = run_numpy_fraud_detection(tx.amount, history)

    # 4. Offload alert to non-blocking background task if suspicious
    if fraud_eval["is_anomaly"]:
        background_tasks.add_task(log_fraud_alert_async, tx.transaction_id, fraud_eval["z_score"])
    # 5. Persist transaction
    new_record = tx.model_dump()
    db_transactions.append(new_record)

    return {
        "status": "APPROVED",
        "transaction_id": tx.transaction_id,
        "fraud_assessment": fraud_eval
    }


@app.get("/v1/accounts/{account_id}/summary")
async def get_account_summary(account_id: str):
    """Returns Pandas-aggregated spend analytics for an account."""
    await asyncio.sleep(0.02)  # Simulate fast async cache lookup
    return run_pandas_account_analytics(account_id)


@app.get("/v1/analytics/batch-risk-matrix")
async def batch_risk_matrix():
    """
    Executes concurrent async mainframe checks across accounts
    and calculates portfolio-wide percentile risk via NumPy.
    """

    df = pd.DataFrame(db_transactions)
    unique_accounts = df["account_id"].unique().tolist()

    # Concurrent AsyncIO gather across all accounts
    tasks = [simulate_mainframe_check(acc) for acc in unique_accounts]
    await asyncio.gather(*tasks)

    # Vectorized portfolio analysis
    amounts = df["amount"].to_numpy()
    p95_threshold = float(np.percentile(amounts, 95))

    return {
        "accounts_checked": len(unique_accounts),
        "portfolio_p95_threshold": round(p95_threshold, 2),
        "portfolio_total_volume": round(float(np.sum(amounts)), 2),
        "high_value_transactions": df[df["amount"] >= p95_threshold].to_dict(orient="records")
    }
