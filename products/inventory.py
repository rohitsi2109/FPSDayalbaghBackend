"""
Central inventory service.

Every change to `Product.stock` in the codebase should go through this module
so that (a) stock can never be driven negative by a race, and (b) an audit row
is written to `StockMovement` for every mutation.

Two usage patterns:

* `apply_delta(product, delta, ...)` — the caller ALREADY holds a row lock on
  `product` (obtained via `select_for_update()` inside an open transaction) or
  otherwise guarantees serialized access. Mutates the in-memory instance and
  records the movement.

* `adjust_stock(product_id, delta, ...)` / `set_stock(product_id, qty, ...)` —
  standalone helpers that open their own transaction, lock the row, apply the
  change and record it. Use these when you don't already hold a lock.
"""

from django.db import transaction

from .models import Product, StockMovement

# Re-exported so callers don't need to import the model just for the choices.
Reason = StockMovement.Reason


class InsufficientStock(Exception):
    """Raised when a decrement would drive stock below zero."""

    def __init__(self, product, available, requested):
        self.product = product
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock for {getattr(product, 'name', product)}: "
            f"have {available}, need {requested}."
        )


def _resolve_user(user):
    """Only persist a real, authenticated user as the actor."""
    if user is not None and getattr(user, "is_authenticated", False):
        return user
    return None


def apply_delta(product, delta, *, reason, user=None, reference="", note="", save=True):
    """
    Apply a signed change to a locked product's stock and write a ledger row.

    The caller MUST hold a row lock on `product` (or otherwise serialize access)
    to make the read-modify-write safe against concurrent mutations. Returns the
    mutated product. Raises InsufficientStock if the result would be negative.
    """
    delta = int(delta)
    new_balance = product.stock + delta
    if new_balance < 0:
        raise InsufficientStock(product, product.stock, -delta)

    product.stock = new_balance
    if save:
        product.save(update_fields=["stock"])

    StockMovement.objects.create(
        product=product,
        delta=delta,
        balance_after=new_balance,
        reason=reason,
        reference=reference or "",
        note=note or "",
        created_by=_resolve_user(user),
    )
    return product


def reserve(product, qty, *, save=True):
    """
    Hold `qty` units against a locked product for a not-yet-confirmed order.

    Reservations reduce what NEW customers can order (`available = stock -
    reserved`) without touching physical `stock`; no ledger row is written until
    the reservation is committed. The caller MUST hold a row lock on `product`.
    Raises InsufficientStock if fewer than `qty` units are available.
    """
    qty = int(qty)
    if qty <= 0:
        return product
    if product.available < qty:
        raise InsufficientStock(product, product.available, qty)
    product.reserved += qty
    if save:
        product.save(update_fields=["reserved"])
    return product


def release(product, qty, *, save=True):
    """
    Release `qty` reserved units back to availability (cancel/edit/expire).

    Clamped at zero so a double-release can never make `reserved` negative. The
    caller MUST hold a row lock on `product`. Physical `stock` is untouched.
    """
    qty = int(qty)
    if qty <= 0:
        return product
    product.reserved = max(0, product.reserved - qty)
    if save:
        product.save(update_fields=["reserved"])
    return product


def commit_reservation(product, qty, *, user=None, reference="", note=""):
    """
    Convert a reservation into a real sale on a locked product.

    Releases `qty` from `reserved` and decrements physical `stock` by the same
    amount, writing a single SALE ledger row. Used when an admin confirms a
    PENDING order. The caller MUST hold a row lock on `product`.
    """
    qty = int(qty)
    if qty <= 0:
        return product
    release(product, qty, save=False)
    apply_delta(
        product, -qty, reason=Reason.SALE, user=user,
        reference=reference, note=note, save=False,
    )
    product.save(update_fields=["stock", "reserved"])
    return product


@transaction.atomic
def adjust_stock(product_id, delta, *, reason, user=None, reference="", note=""):
    """Lock the product row, apply a signed delta, record the movement."""
    product = Product.objects.select_for_update().get(pk=product_id)
    return apply_delta(
        product, delta, reason=reason, user=user, reference=reference, note=note
    )


@transaction.atomic
def set_stock(product_id, new_qty, *, reason, user=None, reference="", note=""):
    """
    Lock the product row and set stock to an absolute value, recording the delta.
    No-ops (and writes no movement) when the value is unchanged.
    """
    product = Product.objects.select_for_update().get(pk=product_id)
    delta = int(new_qty) - product.stock
    if delta == 0:
        return product
    return apply_delta(
        product, delta, reason=reason, user=user, reference=reference, note=note
    )
