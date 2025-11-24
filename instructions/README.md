# Agent Instructions

This directory contains all AI agent instruction prompts used in the vehicle insurance claims processing system.

## 📁 File Organization

### Standalone Agent Instructions
- **`policy_agent.txt`** - Main policy expert agent (used in agents/mainpolicy.py)
- **`inspection_agent.txt`** - Inspection assessment agent (used in agents/inspectionagent.py)
- **`bill_synthesis_agent.txt`** - Bill analysis agent (used in agents/billsynthesis.py)
- **`audit_agent.txt`** - Audit logging agent (used in agents/auditagent.py)

### Orchestrator Agent Instructions
These are used in orchestrator.py with memory context:

- **`policy_lookup_agent.txt`** - Policy lookup with car details extraction
- **`policy_coverage_agent.txt`** - Coverage analysis (no cost estimation)
- **`inspection_orchestrator_agent.txt`** - Inspection with policy memory context
- **`bill_reimbursement_orchestrator_agent.txt`** - Bill analysis with full memory context
- **`synthesis_agent.txt`** - Final decision synthesis

## 🔄 Usage

### In Standalone Agents
```python
from pathlib import Path

instructions_path = Path(__file__).parent.parent / "instructions"
with open(instructions_path / "policy_agent.txt", "r") as f:
    instructions = f.read()
```

### In Orchestrator with Context
```python
# Load template
with open("instructions/inspection_orchestrator_agent.txt", "r") as f:
    template = f.read()

# Replace placeholders with actual values
instructions = template.format(
    idv=extracted_policy_data.get('idv', 0),
    deductible=extracted_policy_data.get('deductible', 0),
    coverage_eligible=extracted_policy_data.get('coverage_eligible', 'Unknown')
)
```

## 📝 Template Variables

Some instruction files use template variables (placeholders):

### inspection_orchestrator_agent.txt
- `{idv}` - Vehicle IDV amount from policy
- `{deductible}` - Policy deductible amount
- `{coverage_eligible}` - Coverage eligibility status

### bill_reimbursement_orchestrator_agent.txt
- `{idv}` - Vehicle IDV amount
- `{deductible}` - Policy deductible amount  
- `{inspection_estimate}` - Estimated repair cost from inspection
- `{total_loss_status}` - Whether vehicle is total loss

## 🔧 Maintenance

When updating agent behavior:
1. Modify the appropriate instruction file
2. Test with actual claims
3. No code changes needed - instructions are loaded at runtime
4. Version control these files carefully

## 🎯 Best Practices

- Keep instructions clear and specific
- Use structured formats (bullet points, numbered lists)
- Include examples of expected output format
- Specify what data sources to use
- Define calculation methods explicitly
- Use consistent terminology across all agents
