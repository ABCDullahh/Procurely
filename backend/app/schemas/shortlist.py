"""Shortlist schemas for API request/response."""

from datetime import datetime

from pydantic import BaseModel, Field


class ShortlistItemBase(BaseModel):
    """Base schema for shortlist items."""

    notes: str | None = None


class ShortlistItemCreate(ShortlistItemBase):
    """Schema for adding vendor to shortlist."""

    pass


class ShortlistItemUpdate(BaseModel):
    """Schema for updating shortlist item notes."""

    notes: str | None = None


class ShortlistItemResponse(ShortlistItemBase):
    """Response schema for shortlist item."""

    id: int
    shortlist_id: int
    vendor_id: int
    position: int
    created_at: datetime

    # Note: vendor details will be included separately or expanded

    class Config:
        from_attributes = True


class ShortlistBase(BaseModel):
    """Base schema for shortlist."""

    name: str = Field(..., min_length=1, max_length=255)
    request_id: int | None = None


class ShortlistCreate(ShortlistBase):
    """Schema for creating shortlist."""

    pass


class ShortlistUpdate(BaseModel):
    """Schema for updating shortlist."""

    name: str = Field(..., min_length=1, max_length=255)


class ShortlistResponse(ShortlistBase):
    """Response schema for shortlist."""

    id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    item_count: int = 0

    class Config:
        from_attributes = True


class ShortlistDetailResponse(ShortlistResponse):
    """Response schema for shortlist with items."""

    items: list[ShortlistItemResponse] = []


class ShortlistListResponse(BaseModel):
    """Response for listing shortlists."""

    shortlists: list[ShortlistResponse]
    total: int


class ReorderRequest(BaseModel):
    """Request schema for reordering items."""

    item_ids: list[int] = Field(..., description="Ordered list of item IDs")


class VendorInShortlist(BaseModel):
    """Vendor info within shortlist item."""

    id: int
    name: str
    website: str | None = None
    logo_url: str | None = None
    overall_score: float | None = None
    fit_score: float | None = None
    trust_score: float | None = None


class ShortlistItemWithVendor(ShortlistItemResponse):
    """Shortlist item with expanded vendor details."""

    vendor: VendorInShortlist


class ShortlistDetailWithVendors(ShortlistResponse):
    """Shortlist detail with vendor info for each item."""

    items: list[ShortlistItemWithVendor] = []
