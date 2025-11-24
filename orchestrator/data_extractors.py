"""
Data extraction utilities
Parses text responses to extract structured data
"""

from typing import Tuple


class DataExtractor:
    """Utility class for extracting structured data from text responses"""
    
    @staticmethod
    def extract_idv_from_policy(policy_text: str) -> int:
        """Extract IDV (Insured Declared Value) from policy agent's response"""
        lines = policy_text.split('\n')
        
        # Look for IDV in specific lines
        for line in lines:
            line_lower = line.lower()
            if ('idv' in line_lower or 'declared value' in line_lower) and '₹' in line:
                numbers = ''.join(c for c in line if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 100000 <= value <= 5000000:  # Reasonable IDV range
                            return value
                    except:
                        continue
        
        # Fallback: look for any reasonable amount
        if '₹' in policy_text:
            parts = policy_text.split('₹')
            for i in range(1, len(parts)):
                amount_text = parts[i][:20]
                numbers = ''.join(c for c in amount_text if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 100000 <= value <= 5000000:
                            return value
                    except:
                        continue
        
        print("[WARNING] Warning: IDV not found in policy agent response")
        return 0
    
    @staticmethod
    def extract_deductible(policy_text: str) -> int:
        """Extract deductible amount from policy agent's response"""
        lines = policy_text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if ('deductible' in line_lower or 'compulsory' in line_lower) and '₹' in line:
                numbers = ''.join(c for c in line if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 500 <= value <= 50000:  # Typical deductible range
                            return value
                    except:
                        continue
        
        # Look for common deductible amounts
        if "1000" in policy_text or "1,000" in policy_text:
            return 1000
        elif "2000" in policy_text or "2,000" in policy_text:
            return 2000
        elif "5000" in policy_text or "5,000" in policy_text:
            return 5000
        
        print("[WARNING] Warning: Deductible not found in policy agent response")
        return 0
    
    @staticmethod
    def extract_cost_estimate(text: str) -> int:
        """Extract cost estimate from text analysis"""
        lines = text.split('\n')
        
        # Look for cost-related lines
        for line in lines:
            line_lower = line.lower()
            if ('total' in line_lower or 'cost' in line_lower or 
                'repair' in line_lower or 'bill' in line_lower) and '₹' in line:
                numbers = ''.join(c for c in line if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 10000 <= value <= 5000000:
                            return value
                    except:
                        continue
        
        # Fallback: find largest reasonable amount
        if '₹' in text:
            parts = text.split('₹')
            max_amount = 0
            for i in range(1, len(parts)):
                amount_text = parts[i][:20]
                numbers = ''.join(c for c in amount_text if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 10000 <= value <= 5000000 and value > max_amount:
                            max_amount = value
                    except:
                        continue
            if max_amount > 0:
                return max_amount
        
        print("[WARNING] Warning: Repair cost not found in agent responses")
        return 0
    
    @staticmethod
    def extract_reimbursement_amount(text: str) -> int:
        """Extract specific reimbursement amount from bill analysis text"""
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if ('reimbursement' in line_lower or 'approved' in line_lower or 
                'payable' in line_lower) and '₹' in line:
                numbers = ''.join(c for c in line if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 10000 <= value <= 5000000:
                            return value
                    except:
                        continue
        
        # Fallback
        if '₹' in text:
            parts = text.split('₹')
            for i in range(1, len(parts)):
                amount_text = parts[i][:20]
                numbers = ''.join(c for c in amount_text if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 10000 <= value <= 5000000:
                            return value
                    except:
                        continue
        
        return 0
    
    @staticmethod
    def check_coverage_eligibility(policy_text: str) -> bool:
        """Check if the claim is eligible for coverage"""
        policy_lower = policy_text.lower()
        coverage_keywords = [
            "collision coverage", "policy covers", "coverage applies",
            "covered under", "own damage", "eligible", "reimbursement", "coverage"
        ]
        return any(keyword in policy_lower for keyword in coverage_keywords)
    
    @staticmethod
    def check_total_loss(text: str) -> bool:
        """Check if total loss is indicated"""
        text_lower = text.lower()
        return "total loss" in text_lower and "do not qualify" not in text_lower
    
    @staticmethod
    def check_damage_authentic(text: str) -> bool:
        """Check if damage is authentic"""
        text_lower = text.lower()
        return "authentic" in text_lower or "consistent" in text_lower
