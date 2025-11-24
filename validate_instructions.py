"""
Validation script to test instruction file loading.
Ensures all instruction files exist and can be loaded properly.
"""

from pathlib import Path

# Define instructions directory
INSTRUCTIONS_DIR = Path(__file__).parent / "instructions"

# Expected instruction files
EXPECTED_FILES = [
    "policy_agent.txt",
    "policy_lookup_agent.txt",
    "policy_coverage_agent.txt",
    "inspection_agent.txt",
    "inspection_orchestrator_agent.txt",
    "bill_synthesis_agent.txt",
    "bill_reimbursement_orchestrator_agent.txt",
    "synthesis_agent.txt",
    "audit_agent.txt",
]

def validate_instructions():
    """Validate that all instruction files exist and can be loaded"""
    
    print("Validating Agent Instruction Files...")
    print("=" * 60)
    
    missing_files = []
    empty_files = []
    loaded_files = []
    
    for filename in EXPECTED_FILES:
        filepath = INSTRUCTIONS_DIR / filename
        
        # Check if file exists
        if not filepath.exists():
            missing_files.append(filename)
            print(f"[X] MISSING: {filename}")
            continue
        
        # Check if file can be read and is not empty
        try:
            with open(filepath, "r") as f:
                content = f.read()
            
            if not content or len(content.strip()) < 50:
                empty_files.append(filename)
                print(f"[!] EMPTY/SHORT: {filename} ({len(content)} chars)")
            else:
                loaded_files.append(filename)
                print(f"[OK] VALID: {filename} ({len(content)} chars, {content.count(chr(10))} lines)")
        
        except Exception as e:
            print(f"[X] ERROR READING: {filename} - {str(e)}")
    
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  [OK] Valid files: {len(loaded_files)}/{len(EXPECTED_FILES)}")
    print(f"  [X] Missing files: {len(missing_files)}")
    print(f"  [!] Empty/short files: {len(empty_files)}")
    
    # Test template variable files
    print("\nTesting Template Variable Files...")
    print("=" * 60)
    
    template_files = {
        "inspection_orchestrator_agent.txt": ["idv", "deductible", "coverage_eligible"],
        "bill_reimbursement_orchestrator_agent.txt": ["idv", "deductible", "inspection_estimate", "total_loss_status"],
    }
    
    for filename, expected_vars in template_files.items():
        filepath = INSTRUCTIONS_DIR / filename
        if filepath.exists():
            with open(filepath, "r") as f:
                content = f.read()
            
            found_vars = []
            missing_vars = []
            
            for var in expected_vars:
                placeholder = "{" + var + "}"
                if placeholder in content:
                    found_vars.append(var)
                else:
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"[!] {filename}: Missing variables: {missing_vars}")
            else:
                print(f"[OK] {filename}: All template variables found: {found_vars}")
    
    print("=" * 60)
    
    if missing_files or empty_files:
        print("\n[X] VALIDATION FAILED")
        return False
    else:
        print("\n[OK] VALIDATION PASSED - All instruction files are valid!")
        return True

if __name__ == "__main__":
    success = validate_instructions()
    exit(0 if success else 1)
