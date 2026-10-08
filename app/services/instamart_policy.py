"""
Instamart Checkout Policy.
Enforces configurable limits such as maximum allowed checkout threshold per Swiggy guidelines.
"""

from typing import Tuple


class InstamartCheckoutPolicy:
    MAX_CHECKOUT_LIMIT_INR: float = 1000.0
    MIN_ORDER_LIMIT_INR: float = 99.0

    @classmethod
    def validate_checkout_amount(cls, amount: float) -> Tuple[bool, str]:
        if amount > cls.MAX_CHECKOUT_LIMIT_INR:
            return False, f"This Instamart order (₹{amount}) exceeds the allowed checkout limit of ₹{cls.MAX_CHECKOUT_LIMIT_INR}."
        return True, ""
