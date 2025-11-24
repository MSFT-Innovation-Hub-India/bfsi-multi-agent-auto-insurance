"""
Data models for claim orchestration
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClaimData:
    """Data structure to hold claim information throughout the orchestration process"""
    claim_id: str
    basic_policy_details: Optional[str] = None
    policy_analysis: Optional[str] = None
    inspection_results: Optional[str] = None
    bill_analysis: Optional[str] = None
    final_recommendation: Optional[str] = None


@dataclass
class ExtractedPolicyData:
    """Extracted policy information"""
    idv: int = 0
    deductible: int = 0
    coverage_eligible: bool = False


@dataclass
class ExtractedInspectionData:
    """Extracted inspection information"""
    repair_cost_estimate: int = 0
    total_loss_indicated: bool = False
    damage_authentic: bool = False


@dataclass
class ExtractedBillData:
    """Extracted bill information"""
    actual_bill_amount: int = 0
    reimbursement_amount: int = 0
    variance_from_estimate: int = 0
