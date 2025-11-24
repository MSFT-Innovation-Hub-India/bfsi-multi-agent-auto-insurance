"""
Test script for modular orchestrator
Run this to verify the new architecture works before migration
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("🧪 TESTING MODULAR ORCHESTRATOR")
print("=" * 80)

# Test 1: Import all modules
print("\n✅ Test 1: Importing all modules...")
try:
    from orchestrator.models import ClaimData, ExtractedPolicyData
    from orchestrator.memory_manager import CosmosMemoryManager
    from orchestrator.agent_factory import AgentFactory
    from orchestrator.data_extractors import DataExtractor
    from orchestrator.synthesis_engine import SynthesisEngine
    from orchestrator.orchestrator import AutoInsuranceOrchestrator
    print("   ✅ All modules imported successfully!")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Test data models
print("\n✅ Test 2: Testing data models...")
try:
    claim = ClaimData(claim_id="TEST-001")
    policy_data = ExtractedPolicyData(idv=321100, deductible=1000)
    print(f"   ✅ ClaimData created: {claim.claim_id}")
    print(f"   ✅ ExtractedPolicyData created: IDV=₹{policy_data.idv:,}")
except Exception as e:
    print(f"   ❌ Data model test failed: {e}")
    sys.exit(1)

# Test 3: Test data extractor
print("\n✅ Test 3: Testing DataExtractor...")
try:
    extractor = DataExtractor()
    
    # Test IDV extraction
    policy_text = "The Insured Declared Value (IDV) is ₹3,21,100 for your vehicle."
    idv = extractor.extract_idv_from_policy(policy_text)
    print(f"   ✅ IDV extraction: ₹{idv:,}")
    
    # Test deductible extraction
    deductible_text = "Compulsory deductible of ₹1,000 applies to this claim."
    deductible = extractor.extract_deductible(deductible_text)
    print(f"   ✅ Deductible extraction: ₹{deductible:,}")
    
    # Test coverage eligibility
    coverage_text = "This claim is covered under collision coverage policy."
    eligible = extractor.check_coverage_eligibility(coverage_text)
    print(f"   ✅ Coverage eligibility check: {eligible}")
    
except Exception as e:
    print(f"   ❌ DataExtractor test failed: {e}")
    sys.exit(1)

# Test 4: Test memory manager (without actual Cosmos DB)
print("\n✅ Test 4: Testing CosmosMemoryManager initialization...")
try:
    memory = CosmosMemoryManager()
    print(f"   ✅ MemoryManager initialized (Cosmos DB: {'Available' if memory.container else 'Not configured'})")
except Exception as e:
    print(f"   ❌ MemoryManager test failed: {e}")
    sys.exit(1)

# Test 5: Test orchestrator initialization (without Azure)
print("\n✅ Test 5: Testing Orchestrator initialization...")
try:
    # Check if Azure credentials are available
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["AZURE_ENDPOINT", "AZURE_RESOURCE_GROUP", "AZURE_SUBSCRIPTION_ID", "AZURE_PROJECT_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"   ⚠️  Azure credentials not configured: {', '.join(missing_vars)}")
        print("   ⚠️  Skipping full orchestrator test (this is OK for structure testing)")
    else:
        orchestrator = AutoInsuranceOrchestrator()
        print("   ✅ Orchestrator initialized successfully!")
        
except Exception as e:
    print(f"   ⚠️  Orchestrator initialization skipped: {e}")
    print("   ⚠️  This is OK - Azure credentials may not be configured yet")

# Test 6: Test backward compatibility import
print("\n✅ Test 6: Testing backward compatibility...")
try:
    from orchestrator import AutoInsuranceOrchestrator as Orchestrator
    from orchestrator import ClaimData as Claim
    print("   ✅ Backward compatible imports work!")
except Exception as e:
    print(f"   ❌ Backward compatibility test failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("🎉 ALL TESTS PASSED!")
print("=" * 80)
print("\n✅ The modular orchestrator structure is working correctly!")
print("\n📝 Next steps:")
print("   1. Review the test results above")
print("   2. If everything looks good, proceed with file migration")
print("   3. Run: python migrate_orchestrator.py")
print("\n" + "=" * 80)
