import re
import uuid


class PaymentMethod:
    """Base class for different payment types."""

    def __init__(self, method_name: str):
        self.method_name = method_name

        # Stores a history of payments and refunds made by this method
        self.transaction_history = []

        # Marks whether the payment method passed its own validation rules
        self.is_valid = True

    def generate_receipt_id(self) -> str:
        """Generate a unique receipt ID for any payment."""
        return str(uuid.uuid4())

    def process_payment(self, amount: float) -> bool:
        """Abstract method to process payments."""
        raise NotImplementedError

    def refund(self, amount: float) -> str:
        # Creates a refund entry and saves it in the transaction history
        receipt = self.generate_receipt_id()
        self.transaction_history.append(
            {"type": "refund", "amount": amount, "receipt": receipt}
        )
        return f"Refund of ${amount:.2f} issued. Receipt ID: {receipt}"


class CreditCard(PaymentMethod):
    """Implements credit card payment."""

    def __init__(self, card_number: str, holder_name: str):
        super().__init__("Credit Card")
        self.card_number = card_number
        self.holder_name = holder_name

        # Validates the card number when the object is created
        self.is_valid = self.validate_card()

    def validate_card(self) -> bool:
        """
        Checks that the card number contains between 13 and 19 digits.
        """
        return bool(re.fullmatch(r"\d{13,19}", self.card_number))

    def process_payment(self, amount: float) -> bool:
        """Process a credit card payment with validation."""
        if not self.is_valid:
            print("Invalid credit card number. Payment cancelled.")
            return False

        print(f"Charging ${amount:.2f} to card ending in {self.card_number[-4:]}...")

        # Records the payment in the transaction history
        receipt = self.generate_receipt_id()
        self.transaction_history.append(
            {"type": "payment", "amount": amount, "receipt": receipt}
        )
        return True


class PayPal(PaymentMethod):
    """Implements PayPal payment."""

    def __init__(self, email: str):
        super().__init__("PayPal")
        self.email = email

        # Validates the PayPal email when the object is created
        self.is_valid = self.validate_email()

    def validate_email(self) -> bool:
        """
        Checks if the email fits a basic email pattern.
        """
        return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", self.email))

    def process_payment(self, amount: float) -> bool:
        """Process a PayPal payment with email validation."""
        if not self.is_valid:
            print("Invalid PayPal email. Payment cancelled.")
            return False

        print(f"Processing PayPal payment of ${amount:.2f} for {self.email}...")

        # Records the payment as a successful transaction
        receipt = self.generate_receipt_id()
        self.transaction_history.append(
            {"type": "payment", "amount": amount, "receipt": receipt}
        )
        return True
