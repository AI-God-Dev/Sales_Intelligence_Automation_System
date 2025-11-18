"""
Root main.py wrapper for Cloud Functions Gen2 deployment
This file satisfies Gen2 requirements but actual functions are in cloud_functions/*/main.py
"""
# For Gen2, we need main.py but functions-framework will use the entry-point parameter
# This file exists to satisfy the requirement
# Actual function entry points are specified via --entry-point flag

# Import all functions so they can be discovered by functions-framework
from cloud_functions.gmail_sync.main import gmail_sync
from cloud_functions.salesforce_sync.main import salesforce_sync
from cloud_functions.dialpad_sync.main import dialpad_sync
from cloud_functions.hubspot_sync.main import hubspot_sync
from cloud_functions.entity_resolution.main import entity_resolution

# Export functions for functions-framework discovery
__all__ = [
    'gmail_sync',
    'salesforce_sync',
    'dialpad_sync',
    'hubspot_sync',
    'entity_resolution'
]