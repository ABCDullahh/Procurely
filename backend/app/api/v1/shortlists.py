"""Shortlist API endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.models import Shortlist, ShortlistItem, Vendor, VendorAsset, VendorMetrics
from app.schemas.shortlist import (
    ReorderRequest,
    ShortlistCreate,
    ShortlistDetailWithVendors,
    ShortlistItemCreate,
    ShortlistItemUpdate,
    ShortlistItemWithVendor,
    ShortlistListResponse,
    ShortlistResponse,
    ShortlistUpdate,
    VendorInShortlist,
)

router = APIRouter(prefix="/shortlists", tags=["shortlists"])


def get_vendor_logo_url(db: Session, vendor_id: int) -> str | None:
    """Get the primary logo URL for a vendor from assets."""
    asset = (
        db.query(VendorAsset)
        .filter(VendorAsset.vendor_id == vendor_id, VendorAsset.asset_type == "LOGO")
        .order_by(VendorAsset.priority.desc())
        .first()
    )
    return asset.asset_url if asset else None




def get_shortlist_or_404(
    shortlist_id: int, db: Session, current_user_id: int
) -> Shortlist:
    """Get shortlist by ID or raise 404, with RBAC check."""
    shortlist = (
        db.query(Shortlist)
        .filter(Shortlist.id == shortlist_id)
        .first()
    )
    if not shortlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist not found",
        )
    if shortlist.created_by_user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return shortlist


@router.get("", response_model=ShortlistListResponse)
def list_shortlists(
    db: DbSession,
    current_user: CurrentUser,
    request_id: int | None = Query(None, description="Filter by request ID"),
) -> ShortlistListResponse:
    """List user's shortlists."""
    query = db.query(Shortlist).filter(
        Shortlist.created_by_user_id == current_user.id
    )
    if request_id:
        query = query.filter(Shortlist.request_id == request_id)

    shortlists = query.order_by(Shortlist.updated_at.desc()).all()

    # Get item counts
    results = []
    for s in shortlists:
        item_count = db.query(func.count(ShortlistItem.id)).filter(
            ShortlistItem.shortlist_id == s.id
        ).scalar() or 0
        results.append(
            ShortlistResponse(
                id=s.id,
                name=s.name,
                request_id=s.request_id,
                created_by_user_id=s.created_by_user_id,
                created_at=s.created_at,
                updated_at=s.updated_at,
                item_count=item_count,
            )
        )

    return ShortlistListResponse(shortlists=results, total=len(results))


@router.post("", response_model=ShortlistResponse, status_code=status.HTTP_201_CREATED)
def create_shortlist(
    data: ShortlistCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ShortlistResponse:
    """Create a new shortlist."""
    shortlist = Shortlist(
        name=data.name,
        request_id=data.request_id,
        created_by_user_id=current_user.id,
    )
    db.add(shortlist)
    db.commit()
    db.refresh(shortlist)

    return ShortlistResponse(
        id=shortlist.id,
        name=shortlist.name,
        request_id=shortlist.request_id,
        created_by_user_id=shortlist.created_by_user_id,
        created_at=shortlist.created_at,
        updated_at=shortlist.updated_at,
        item_count=0,
    )


@router.get("/{shortlist_id}", response_model=ShortlistDetailWithVendors)
def get_shortlist(
    shortlist_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ShortlistDetailWithVendors:
    """Get shortlist with items and vendor details."""
    shortlist = get_shortlist_or_404(shortlist_id, db, current_user.id)

    # Get items with vendors
    items_query = (
        db.query(ShortlistItem)
        .filter(ShortlistItem.shortlist_id == shortlist_id)
        .order_by(ShortlistItem.position)
        .all()
    )

    items_with_vendors = []
    for item in items_query:
        vendor = db.query(Vendor).filter(Vendor.id == item.vendor_id).first()
        metrics = (
            db.query(VendorMetrics)
            .filter(VendorMetrics.vendor_id == item.vendor_id)
            .first()
        )

        vendor_info = VendorInShortlist(
            id=vendor.id,
            name=vendor.name,
            website=vendor.website,
            logo_url=get_vendor_logo_url(db, vendor.id),
            overall_score=metrics.overall_score if metrics else None,
            fit_score=metrics.fit_score if metrics else None,
            trust_score=metrics.trust_score if metrics else None,
        ) if vendor else None

        items_with_vendors.append(
            ShortlistItemWithVendor(
                id=item.id,
                shortlist_id=item.shortlist_id,
                vendor_id=item.vendor_id,
                notes=item.notes,
                position=item.position,
                created_at=item.created_at,
                vendor=vendor_info,
            )
        )

    return ShortlistDetailWithVendors(
        id=shortlist.id,
        name=shortlist.name,
        request_id=shortlist.request_id,
        created_by_user_id=shortlist.created_by_user_id,
        created_at=shortlist.created_at,
        updated_at=shortlist.updated_at,
        item_count=len(items_with_vendors),
        items=items_with_vendors,
    )


@router.put("/{shortlist_id}", response_model=ShortlistResponse)
def update_shortlist(
    shortlist_id: int,
    data: ShortlistUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ShortlistResponse:
    """Rename a shortlist."""
    shortlist = get_shortlist_or_404(shortlist_id, db, current_user.id)
    shortlist.name = data.name
    db.commit()
    db.refresh(shortlist)

    item_count = db.query(func.count(ShortlistItem.id)).filter(
        ShortlistItem.shortlist_id == shortlist.id
    ).scalar() or 0

    return ShortlistResponse(
        id=shortlist.id,
        name=shortlist.name,
        request_id=shortlist.request_id,
        created_by_user_id=shortlist.created_by_user_id,
        created_at=shortlist.created_at,
        updated_at=shortlist.updated_at,
        item_count=item_count,
    )


@router.delete("/{shortlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shortlist(
    shortlist_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a shortlist."""
    shortlist = get_shortlist_or_404(shortlist_id, db, current_user.id)
    db.delete(shortlist)
    db.commit()


@router.post(
    "/{shortlist_id}/vendors/{vendor_id}",
    response_model=ShortlistItemWithVendor,
    status_code=status.HTTP_201_CREATED,
)
def add_vendor_to_shortlist(
    shortlist_id: int,
    vendor_id: int,
    data: ShortlistItemCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ShortlistItemWithVendor:
    """Add a vendor to shortlist."""
    get_shortlist_or_404(shortlist_id, db, current_user.id)  # RBAC check

    # Check if vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    # Check for duplicate
    existing = (
        db.query(ShortlistItem)
        .filter(
            ShortlistItem.shortlist_id == shortlist_id,
            ShortlistItem.vendor_id == vendor_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor already in shortlist",
        )

    # Get max position
    max_pos = (
        db.query(func.max(ShortlistItem.position))
        .filter(ShortlistItem.shortlist_id == shortlist_id)
        .scalar() or -1
    )

    item = ShortlistItem(
        shortlist_id=shortlist_id,
        vendor_id=vendor_id,
        notes=data.notes,
        position=max_pos + 1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    metrics = (
        db.query(VendorMetrics)
        .filter(VendorMetrics.vendor_id == vendor_id)
        .first()
    )

    return ShortlistItemWithVendor(
        id=item.id,
        shortlist_id=item.shortlist_id,
        vendor_id=item.vendor_id,
        notes=item.notes,
        position=item.position,
        created_at=item.created_at,
        vendor=VendorInShortlist(
            id=vendor.id,
            name=vendor.name,
            website=vendor.website,
            logo_url=get_vendor_logo_url(db, vendor.id),
            overall_score=metrics.overall_score if metrics else None,
            fit_score=metrics.fit_score if metrics else None,
            trust_score=metrics.trust_score if metrics else None,
        ),
    )


@router.delete(
    "/{shortlist_id}/vendors/{vendor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_vendor_from_shortlist(
    shortlist_id: int,
    vendor_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Remove a vendor from shortlist."""
    get_shortlist_or_404(shortlist_id, db, current_user.id)  # RBAC check

    item = (
        db.query(ShortlistItem)
        .filter(
            ShortlistItem.shortlist_id == shortlist_id,
            ShortlistItem.vendor_id == vendor_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not in shortlist",
        )

    db.delete(item)
    db.commit()


@router.put("/{shortlist_id}/reorder", response_model=ShortlistDetailWithVendors)
def reorder_shortlist(
    shortlist_id: int,
    data: ReorderRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ShortlistDetailWithVendors:
    """Reorder items in shortlist."""
    get_shortlist_or_404(shortlist_id, db, current_user.id)  # RBAC check

    # Validate all items belong to this shortlist
    items = (
        db.query(ShortlistItem)
        .filter(ShortlistItem.shortlist_id == shortlist_id)
        .all()
    )
    item_id_set = {item.id for item in items}

    if set(data.item_ids) != item_id_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="item_ids must contain all and only items in this shortlist",
        )

    # Update positions
    for pos, item_id in enumerate(data.item_ids):
        db.query(ShortlistItem).filter(ShortlistItem.id == item_id).update(
            {"position": pos}
        )
    db.commit()

    # Return updated shortlist
    return get_shortlist(shortlist_id, db, current_user)


@router.put(
    "/{shortlist_id}/vendors/{vendor_id}/notes",
    response_model=ShortlistItemWithVendor,
)
def update_item_notes(
    shortlist_id: int,
    vendor_id: int,
    data: ShortlistItemUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ShortlistItemWithVendor:
    """Update notes for a vendor in shortlist."""
    get_shortlist_or_404(shortlist_id, db, current_user.id)  # RBAC check

    item = (
        db.query(ShortlistItem)
        .filter(
            ShortlistItem.shortlist_id == shortlist_id,
            ShortlistItem.vendor_id == vendor_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not in shortlist",
        )

    item.notes = data.notes
    db.commit()
    db.refresh(item)

    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    metrics = (
        db.query(VendorMetrics)
        .filter(VendorMetrics.vendor_id == vendor_id)
        .first()
    )

    return ShortlistItemWithVendor(
        id=item.id,
        shortlist_id=item.shortlist_id,
        vendor_id=item.vendor_id,
        notes=item.notes,
        position=item.position,
        created_at=item.created_at,
        vendor=VendorInShortlist(
            id=vendor.id,
            name=vendor.name,
            website=vendor.website,
            logo_url=get_vendor_logo_url(db, vendor.id) if vendor else None,
            overall_score=metrics.overall_score if metrics else None,
            fit_score=metrics.fit_score if metrics else None,
            trust_score=metrics.trust_score if metrics else None,
        ) if vendor else None,
    )
