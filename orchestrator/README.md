# Modular Orchestrator Architecture

## 📦 Structure

```
orchestrator/
├── __init__.py              # Package exports
├── models.py                # Data classes (50 lines)
├── memory_manager.py        # Cosmos DB operations (150 lines)
├── agent_factory.py         # Agent creation (100 lines)
├── data_extractors.py       # Text parsing utilities (150 lines)
├── synthesis_engine.py      # Final synthesis logic (200 lines)
└── orchestrator.py          # Main coordinator (400 lines)
```

**Total: ~1050 lines** (down from 1416 lines in monolithic file)

## 🎯 Benefits

### 1. **Separation of Concerns**
- Each module has a single, clear responsibility
- Easy to understand and maintain
- Changes to one component don't affect others

### 2. **Testability**
- Each module can be tested independently
- Mock dependencies easily
- Unit tests are simpler and faster

### 3. **Reusability**
- `DataExtractor` can be used by other parts of the system
- `AgentFactory` can create agents for other workflows
- `MemoryManager` is a standalone service

### 4. **Team Collaboration**
- Different developers can work on different modules
- Reduces merge conflicts
- Clear ownership boundaries

### 5. **Performance**
- Only import what you need
- Faster loading times
- Better memory management

## 🔄 Backward Compatibility

The old `orchestrator.py` can be replaced with `orchestrator_new.py`:

```python
# Old import (still works)
from orchestrator import AutoInsuranceOrchestrator, ClaimData

# New import (recommended)
from orchestrator.orchestrator import AutoInsuranceOrchestrator
from orchestrator.models import ClaimData
```

## 📝 Module Descriptions

### **models.py**
Data structures for the entire system:
- `ClaimData` - Main claim container
- `ExtractedPolicyData` - Policy information
- `ExtractedInspectionData` - Inspection findings
- `ExtractedBillData` - Bill information

### **memory_manager.py**
Handles all Cosmos DB interactions:
- `store_agent_response()` - Save agent outputs
- `retrieve_previous_responses()` - Get historical data
- `get_latest_response()` - Get most recent agent output
- `get_all_agent_responses()` - Complete claim history

### **agent_factory.py**
Creates and configures AI agents:
- `create_policy_agent()` - Policy analysis agent
- `create_inspection_agent()` - Inspection agent
- `create_bill_agent()` - Bill analysis agent
- `delete_agent()` - Cleanup

### **data_extractors.py**
Parses text to extract structured data:
- `extract_idv_from_policy()` - Get vehicle value
- `extract_deductible()` - Get deductible amount
- `extract_cost_estimate()` - Get repair costs
- `extract_reimbursement_amount()` - Get final amount
- `check_coverage_eligibility()` - Coverage status
- `check_total_loss()` - Total loss determination

### **synthesis_engine.py**
Generates final recommendations:
- `synthesize_final_recommendation()` - Main synthesis
- `_fallback_synthesis()` - Rule-based fallback
- `_calculate_decision()` - Decision logic
- `_format_final_report()` - Report generation

### **orchestrator.py**
Main coordinator:
- `get_policy_basic_details()` - Step 0
- `execute_policy_analysis()` - Step 1
- `execute_inspection_analysis()` - Step 2
- `execute_bill_reimbursement_analysis()` - Step 3
- `synthesize_final_recommendation()` - Step 4
- `process_claim()` - Complete workflow

## 🧪 Testing Examples

```python
# Test data extractor independently
from orchestrator.data_extractors import DataExtractor

extractor = DataExtractor()
idv = extractor.extract_idv_from_policy(policy_text)
assert idv == 321100

# Test memory manager independently
from orchestrator.memory_manager import CosmosMemoryManager

memory = CosmosMemoryManager()
await memory.store_agent_response("CLM-001", "policy", "...", {...})

# Test synthesis engine independently
from orchestrator.synthesis_engine import SynthesisEngine
from orchestrator.models import ClaimData

engine = SynthesisEngine()
claim = ClaimData(claim_id="CLM-001", policy_analysis="...", ...)
result = await engine.synthesize_final_recommendation(claim)
```

## 🚀 Migration Guide

### Step 1: Backup
```bash
cp orchestrator.py orchestrator_old_backup.py
```

### Step 2: Replace
```bash
# Rename old file
mv orchestrator.py orchestrator_legacy.py

# Use new wrapper
mv orchestrator_new.py orchestrator.py
```

### Step 3: Test
```bash
python -m pytest tests/  # Run your tests
python orchestrator.py   # Run standalone
```

### Step 4: Update Imports (Optional)
```python
# Update to explicit imports for better IDE support
from orchestrator.orchestrator import AutoInsuranceOrchestrator
from orchestrator.models import ClaimData
from orchestrator.memory_manager import CosmosMemoryManager
```

## 📊 Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Lines per file | 1416 | 50-400 | 71% reduction |
| Cyclomatic complexity | High | Low | More maintainable |
| Test coverage | Hard | Easy | Testable modules |
| Load time | Slower | Faster | Lazy imports |
| Team velocity | Slower | Faster | Parallel work |

## 🎓 Best Practices

1. **Import only what you need**
   ```python
   from orchestrator.data_extractors import DataExtractor
   # vs importing entire orchestrator
   ```

2. **Use type hints**
   ```python
   def extract_idv(text: str) -> int:
       ...
   ```

3. **Keep modules focused**
   - Each module should do one thing well
   - If a module exceeds 300 lines, consider splitting

4. **Document public APIs**
   - Add docstrings to all public methods
   - Include usage examples

5. **Write unit tests**
   - Test each module independently
   - Mock external dependencies

## 🔧 Future Enhancements

- Add `orchestrator/validators.py` for input validation
- Add `orchestrator/formatters.py` for output formatting
- Add `orchestrator/exceptions.py` for custom exceptions
- Add `orchestrator/config.py` for configuration management
- Add `orchestrator/metrics.py` for performance tracking
