from strands import tool
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SUPPLIERS_TABLE, REGION

dynamodb = boto3.resource("dynamodb", region_name=REGION)


def _sanitize(obj):
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    return obj


@tool
def supplier_lookup_tool(category: str, region: str = None) -> dict:
    """
    Queries DynamoDB to find active suppliers matching the given component category.
    Optionally filters by region. Returns list of matching suppliers with their
    ratings and certifications.

    Args:
        category: Component category to search (e.g. brake_systems, sensors)
        region:   Optional supplier location filter (e.g. Chennai, Pune)

    Returns:
        dict with suppliers list and count
    """
    if not category:
        return {"status": "error", "message": "category parameter is required"}

    table = dynamodb.Table(SUPPLIERS_TABLE)
    filter_expr = Attr("status").eq("active") & Attr("category").eq(category)
    if region:
        filter_expr = filter_expr & Attr("region").eq(region)

    try:
        response  = table.scan(FilterExpression=filter_expr)
        suppliers = response.get("Items", [])
    except Exception as e:
        raise RuntimeError(f"DynamoDB scan failed: {e}")

    return {
        "status": "success",
        "count":     len(suppliers),
        "suppliers": _sanitize(suppliers),
        "category":  category,
    }
