from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from typing import List, Optional

from datetime import timezone

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _hash_password(plain: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """
    Creates a salted hash of the password.
    This is used to avoid storing the plain password.
    """
    salt = salt or os.urandom(16)
    digest = hashlib.sha256(salt + plain.encode("utf-8")).hexdigest()
    return salt.hex(), digest


class Person:
    """Base class for all people in the system."""

    def __init__(self, person_id: int, name: str, email: str):
        self.person_id = int(person_id)
        self.name = name.strip()

        # Validates the email before saving it
        if not EMAIL_RE.fullmatch(email):
            raise ValueError("Invalid email address")
        self.email = email.strip().lower()

        # Records the date and time when the person object is created
        self.created_at: datetime = datetime.now(timezone.utc)


        # Tracks the status of the person such as active or suspended
        self.status: str = "active"

    def display_info(self) -> str:
        return f"{self.name} ({self.email})"

    def change_email(self, new_email: str) -> None:
        # Updates the email only if it passes validation
        if not EMAIL_RE.fullmatch(new_email):
            raise ValueError("Invalid email address")
        self.email = new_email.strip().lower()

    def to_dict(self) -> dict:
        # Creates a simple version of the object that doesn't include private information
        return {
            "person_id": self.person_id,
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "created_at": self.created_at.isoformat() + "Z",
        }


class User(Person):
    """Represents a registered user who can shop."""

    def __init__(self, user_id: int, name: str, email: str, password: str):
        super().__init__(user_id, name, email)

        # Stores the password as a salted hash to protect the user's information
        salt_hex, digest_hex = _hash_password(password)
        self._pw_salt = salt_hex
        self._pw_digest = digest_hex

        # Stores past orders for the user
        self._orders: List["Order"] = []

        # Creates the cart only when needed instead of at initialization
        self._cart: Optional["ShoppingCart"] = None

        # Saves the last login time when the user logs in
        self.last_login_at: Optional[datetime] = None

    def verify_password(self, password: str) -> bool:
        # Checks if the entered password matches the stored salted hash
        salt = bytes.fromhex(self._pw_salt)
        _, digest = _hash_password(password, salt)
        return digest == self._pw_digest

    def set_password(self, new_password: str) -> None:
        # Updates the password after checking that it meets the basic length rule
        if len(new_password) < 6:
            raise ValueError("Password must be at least 6 characters")
        salt_hex, digest_hex = _hash_password(new_password)
        self._pw_salt, self._pw_digest = salt_hex, digest_hex

    def login(self, email: str, password: str) -> bool:
        # Logs the user in and records the time if the login is successful
        ok = (self.email == email.strip().lower()) and self.verify_password(password)
        if ok:
            self.last_login_at = datetime.utcnow()
        return ok

    def _ensure_cart(self) -> "ShoppingCart":
        # Creates the shopping cart only when the user first needs one
        if not self._cart:
            from .shopping import ShoppingCart
            self._cart = ShoppingCart(self)
        return self._cart

    def add_to_cart(self, candy: "Candy", quantity: int) -> None:
        # Doesn't allow adding an item with a nonpositive quantity
        if quantity <= 0:
            raise ValueError("Item must be in stock")
        self._ensure_cart().add_item(candy, quantity)

    def get_cart(self) -> Optional["ShoppingCart"]:
        return self._cart

    def checkout(self, payment_method: "PaymentMethod") -> "Order":
        # Doesn't allow checkout if the cart is empty
        if not self._cart or self._cart.is_empty():
            raise ValueError("Cart is empty")
        order = self._cart.create_order(payment_method)
        self._orders.append(order)
        self._cart.clear()
        return order

    def get_orders(self) -> List["Order"]:
        return list(self._orders)


class Staff(User):
    """Represents an employee with management abilities."""

    def __init__(self, user_id: int, name: str, email: str, password: str, position: str):
        super().__init__(user_id, name, email, password)
        self.position = position.strip()

    def update_inventory(self, candy: "Candy", new_quantity: int) -> None:
        # Protects against setting a negative inventory amount
        if new_quantity < 0:
            raise ValueError("Inventory quantity cannot be negative")
        candy.quantity = int(new_quantity)

    def view_sales_report(self, orders: List["Order"]) -> str:
        # Summarizes the orders to show count, total sales, and average value
        count = len(orders)
        total = sum(getattr(order, "total_amount", 0.0) for order in orders)
        avg = (total / count) if count else 0.0
        return f"Orders: {count} | Total sales: ${total:.2f} | Avg order: ${avg:.2f}"
