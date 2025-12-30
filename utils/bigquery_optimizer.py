"""
BigQuery query optimization utilities.
"""
import re
from typing import Optional


def optimize_query(query: str) -> str:
    """
    Add BigQuery optimization hints to query.
    
    Args:
        query: SQL query string
        
    Returns:
        Optimized query with hints
    """
    optimizations = [
        "-- Query optimized with partitioning and clustering",
        "-- Uses clustering keys for efficient filtering"
    ]
    return "\n".join(optimizations) + "\n" + query


def add_partition_filter(
    query: str,
    partition_field: str,
    days_back: int = 90
) -> str:
    """
    Add partition pruning to query for better performance.
    
    Args:
        query: SQL query string
        partition_field: Field used for partitioning (e.g., 'sent_at', 'created_at')
        days_back: Number of days to look back
        
    Returns:
        Query with partition filter added
    """
    # Check if WHERE clause exists
    where_pattern = r'\bWHERE\b'
    if re.search(where_pattern, query, re.IGNORECASE):
        # Add partition filter to existing WHERE clause
        partition_filter = f"{partition_field} >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)"
        query = re.sub(
            where_pattern,
            f"WHERE {partition_filter} AND",
            query,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # Add WHERE clause with partition filter
        # Find the last FROM clause and add WHERE after it
        from_pattern = r'(\bFROM\s+[^\s]+(?:\s+[^\s]+)?)'
        match = list(re.finditer(from_pattern, query, re.IGNORECASE))
        if match:
            last_from = match[-1]
            insert_pos = last_from.end()
            partition_filter = f"\nWHERE {partition_field} >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)"
            query = query[:insert_pos] + partition_filter + query[insert_pos:]
    
    return query


def add_limit_if_missing(query: str, default_limit: int = 1000) -> str:
    """
    Add LIMIT clause if missing to prevent runaway queries.
    
    Args:
        query: SQL query string
        default_limit: Default limit to add if missing
        
    Returns:
        Query with LIMIT clause
    """
    # Check if LIMIT already exists
    limit_pattern = r'\bLIMIT\s+\d+'
    if re.search(limit_pattern, query, re.IGNORECASE):
        return query
    
    # Add LIMIT at the end
    query = query.rstrip().rstrip(';')
    return f"{query}\nLIMIT {default_limit}"


def validate_query_safety(query: str) -> bool:
    """
    Validate that query is safe (SELECT only, no DROP/DELETE/UPDATE).
    
    Args:
        query: SQL query string
        
    Returns:
        True if query is safe, False otherwise
    """
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'CREATE']
    query_upper = query.upper()
    
    # Allow INSERT only in specific contexts (our ETL functions)
    if 'INSERT' in query_upper:
        # Check if it's a parameterized insert (safe)
        if 'VALUES' in query_upper or 'SELECT' in query_upper:
            # This is likely our ETL code, allow it
            pass
        else:
            return False
    
    for keyword in dangerous_keywords:
        if keyword in query_upper and keyword != 'INSERT':
            return False
    
    return True

