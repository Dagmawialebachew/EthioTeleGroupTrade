from typing import Tuple
from datetime import datetime

def calculate_price(created_year: int, created_month: int) -> Tuple[int, str]:
    """
    Calculates the group price based on creation date.
    created_month = 0 signifies the month was irrelevant/skipped (i.e., NOT 2024).
    """
    CURRENT_YEAR = datetime.now().year # 2025
    
    # 1. Very Old Groups (Pre-2016)
    if created_year < 2016:
        return 0, 'manual_review'
        
    # 2. Stable Old Groups (2016-2023)
    if 2016 <= created_year <= 2023:
        # Month is guaranteed to be 0 from the handler. Price is stable.
        return 1000, 'valid'

    # 3. CRITICAL YEAR (2024) - Requires specific month check
    if created_year == 2024:
        # If the month is 0, the user skipped the month selection for 2024.
        if created_month == 0:
             return 0, 'manual_review' # Should not happen with the current handler, but safe.
            
        # Pricing policy for 2024 (Example: only Jan-Apr are valid)
        if 1 <= created_month <= 4:
            return 300, 'valid'
        
        # May 2024 onwards is not valid
        return 0, 'not_valid'
        
    # 4. Current Year (2025) and Future Years
    if created_year >= CURRENT_YEAR: # 2025 and up
        # Month is guaranteed to be 0 from the handler.
        # Policy: 2025 groups are NOT valid, but maybe require review for future proofing.
        return 0, 'manual_review' 

    # Fallback (Should not be reached)
    return 0, 'manual_review'

def get_month_name(month: int, lang_data: dict) -> str:
    # Since created_month is now guaranteed to be an integer, we update the type hint.
    if month < 1 or month > 12:
        return ""
    return lang_data.get(f'month_{month}', str(month))