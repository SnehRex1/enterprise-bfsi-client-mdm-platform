"""
Pytest configuration for the MDM project.

Adds the project root to Python's import path so tests can
import project modules such as:

    from src.quality.contract_validator import ...
"""

import sys
from pathlib import Path

# Project root:
# D:\Download 3\Data Engineering\MDM Project\enterprise-bfsi-client-mdm-platform
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Add project root to Python's import path if it isn't already there.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))