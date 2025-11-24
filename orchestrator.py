"""
Backward compatibility wrapper for orchestrator.py
This allows existing imports to continue working while using the modular architecture
"""

# Import everything from the modular orchestrator
from orchestrator.orchestrator import AutoInsuranceOrchestrator, main
from orchestrator.models import ClaimData
from orchestrator.memory_manager import CosmosMemoryManager

# Re-export for backward compatibility
__all__ = [
    'AutoInsuranceOrchestrator',
    'ClaimData', 
    'CosmosMemoryManager',
    'main'
]

# This file replaces the old 1416-line orchestrator.py
# All functionality is now split into:
# - orchestrator/orchestrator.py (main logic ~400 lines)
# - orchestrator/memory_manager.py (Cosmos DB ~150 lines)
# - orchestrator/agent_factory.py (agent creation ~100 lines)
# - orchestrator/data_extractors.py (text parsing ~150 lines)
# - orchestrator/synthesis_engine.py (final synthesis ~200 lines)
# - orchestrator/models.py (data classes ~50 lines)

# Allow running as script
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
