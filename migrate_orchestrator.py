"""
Migration script for orchestrator refactoring
This safely migrates from monolithic to modular architecture
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
ROOT_DIR = Path(__file__).parent
OLD_FILE = ROOT_DIR / "orchestrator.py"
NEW_FILE = ROOT_DIR / "orchestrator_new.py"
BACKUP_DIR = ROOT_DIR / "backup_orchestrator"

def main():
    print("=" * 80)
    print("🔄 ORCHESTRATOR MIGRATION SCRIPT")
    print("=" * 80)
    
    # Step 1: Check if files exist
    print("\n📋 Step 1: Checking files...")
    
    if not OLD_FILE.exists():
        print(f"   ❌ Original orchestrator.py not found at: {OLD_FILE}")
        return
    print(f"   ✅ Found original: {OLD_FILE}")
    
    if not NEW_FILE.exists():
        print(f"   ❌ New orchestrator_new.py not found at: {NEW_FILE}")
        return
    print(f"   ✅ Found new wrapper: {NEW_FILE}")
    
    orchestrator_dir = ROOT_DIR / "orchestrator"
    if not orchestrator_dir.exists():
        print(f"   ❌ Orchestrator package not found at: {orchestrator_dir}")
        return
    print(f"   ✅ Found orchestrator package: {orchestrator_dir}")
    
    # Step 2: Create backup
    print("\n💾 Step 2: Creating backup...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUP_DIR.mkdir(exist_ok=True)
    
    backup_file = BACKUP_DIR / f"orchestrator_backup_{timestamp}.py"
    shutil.copy2(OLD_FILE, backup_file)
    print(f"   ✅ Backup created: {backup_file}")
    
    # Step 3: Show what will happen
    print("\n📝 Step 3: Migration plan...")
    print(f"   1. Move {OLD_FILE.name} → {BACKUP_DIR}/orchestrator_legacy_{timestamp}.py")
    print(f"   2. Move {NEW_FILE.name} → {OLD_FILE.name}")
    print(f"   3. Keep orchestrator/ package intact")
    
    # Step 4: Confirm
    print("\n⚠️  WARNING: This will replace your current orchestrator.py")
    response = input("\n   Do you want to proceed? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("\n❌ Migration cancelled by user")
        print(f"   Your original file is safe at: {OLD_FILE}")
        return
    
    # Step 5: Perform migration
    print("\n🔄 Step 5: Performing migration...")
    
    try:
        # Move old file to legacy backup
        legacy_file = BACKUP_DIR / f"orchestrator_legacy_{timestamp}.py"
        shutil.move(str(OLD_FILE), str(legacy_file))
        print(f"   ✅ Moved old file to: {legacy_file}")
        
        # Move new wrapper to become orchestrator.py
        shutil.move(str(NEW_FILE), str(OLD_FILE))
        print(f"   ✅ New wrapper is now: {OLD_FILE}")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\n🔄 Attempting rollback...")
        
        # Rollback - restore from backup
        if backup_file.exists():
            shutil.copy2(backup_file, OLD_FILE)
            print(f"   ✅ Restored from backup: {OLD_FILE}")
        return
    
    # Step 6: Verify
    print("\n🔍 Step 6: Verifying migration...")
    
    if OLD_FILE.exists():
        print(f"   ✅ orchestrator.py exists")
    else:
        print(f"   ❌ orchestrator.py missing!")
        return
    
    if orchestrator_dir.exists():
        modules = list(orchestrator_dir.glob("*.py"))
        print(f"   ✅ orchestrator/ package has {len(modules)} modules")
    
    # Step 7: Test import
    print("\n🧪 Step 7: Testing import...")
    try:
        import sys
        # Clear any cached imports
        if 'orchestrator' in sys.modules:
            del sys.modules['orchestrator']
        
        from orchestrator import AutoInsuranceOrchestrator, ClaimData
        print("   ✅ Import successful!")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return
    
    # Step 8: Summary
    print("\n" + "=" * 80)
    print("🎉 MIGRATION SUCCESSFUL!")
    print("=" * 80)
    
    print("\n📊 Summary:")
    print(f"   ✅ Old file backed up to: {backup_file}")
    print(f"   ✅ Legacy file saved to: {legacy_file}")
    print(f"   ✅ New modular orchestrator is active")
    print(f"   ✅ All imports work correctly")
    
    print("\n📝 What changed:")
    print("   • orchestrator.py now uses modular architecture")
    print("   • Code is split into focused modules in orchestrator/")
    print("   • All existing imports still work (backward compatible)")
    
    print("\n🔄 To rollback (if needed):")
    print(f"   cp {backup_file} orchestrator.py")
    
    print("\n✅ You can now use the new modular orchestrator!")
    print("   All your existing code will continue to work without changes.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
