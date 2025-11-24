"""
Vertex AI initialization helper with warning suppression.
Suppresses pkg_resources deprecation warnings from google-cloud-aiplatform.
"""
import warnings
import os
from typing import Optional
from google.cloud import aiplatform

# Suppress pkg_resources deprecation warnings globally
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.aiplatform.initializer")
warnings.filterwarnings("ignore", message=".*pkg_resources.*deprecated.*")
warnings.filterwarnings("ignore", message=".*setuptools.*")


def init_vertex_ai(project_id: str, location: Optional[str] = None) -> None:
    """
    Initialize Vertex AI with deprecation warnings suppressed.
    
    Args:
        project_id: GCP project ID
        location: GCP region (optional)
    """
    # Suppress warnings during initialization
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*pkg_resources.*")
        warnings.filterwarnings("ignore", message=".*setuptools.*")
        
        if location:
            aiplatform.init(project=project_id, location=location)
        else:
            aiplatform.init(project=project_id)

