from typing import Optional, List
from pydantic import BaseModel


class NormalizedAddress(BaseModel):
    id: str
    label: str
    display_text: str
    phone_number: Optional[str] = None
    is_default: bool = False


class AddressListResponse(BaseModel):
    addresses: List[NormalizedAddress]
    total: int
    default_address_id: Optional[str] = None
