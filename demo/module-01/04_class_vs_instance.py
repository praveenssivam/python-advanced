"""
04_class_vs_instance.py
========================
Demonstrates the difference between class-level attributes (shared
across all instances) and instance-level attributes (independent per
instance), using a BankAccount example.

Run:
    python module-01/04_class_vs_instance.py
"""


class BankAccount:
    """A simple bank account demonstrating class vs instance attributes.

    Class attribute  `bank_name`    — ONE value shared by ALL instances.
                                      Changing it on the class changes it everywhere.
    Instance attribute `balance`   — each BankAccount object has its OWN value.
    Class attribute `_total_accounts` — a shared counter, updated via the class,
                                        not via self, to avoid ambiguity.

    Flow for BankAccount("Alice", 500):
      1. __init__ called with owner="Alice", initial_deposit=500
      2. self.owner = "Alice"    → new instance attribute on THIS object
      3. self.balance = 500      → new instance attribute on THIS object
      4. BankAccount._total_accounts += 1   → mutates the CLASS attribute (shared)
      5. self.account_number = BankAccount._total_accounts  → stores the current count
    """

    # Class attribute — shared by ALL instances
    bank_name = "DemoBank"
    _total_accounts = 0  # tracks how many accounts have been created

    def __init__(self, owner: str, initial_deposit: float = 0.0):
        # Instance attributes — each account has its own copy
        self.owner = owner
        self.balance = initial_deposit

        # Modifying the class-level counter through the class, not self
        BankAccount._total_accounts += 1
        self.account_number = BankAccount._total_accounts

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient funds.")
        self.balance -= amount

    def statement(self) -> str:
        return (
            f"[{self.bank_name}] Account #{self.account_number} "
            f"— Owner: {self.owner}, Balance: ${self.balance:.2f}"
        )

    @classmethod
    def total_accounts(cls) -> int:
        """Class method — operates on the class, not a single instance."""
        return cls._total_accounts

    def __repr__(self) -> str:
        return f"BankAccount(owner={self.owner!r}, balance={self.balance:.2f})"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Class attribute is shared across instances
#
# A CLASS attribute lives on the class object itself.  When Python looks up
# `instance.attr`, it first checks the INSTANCE's `__dict__`, then the CLASS's
# `__dict__`.  If the attribute only exists on the class, all instances see
# the same value.
#
# Flow for  BankAccount.bank_name = "NationalDemoBank":
#   1. Python sets the attribute directly on the BankAccount class object
#   2. alice.bank_name  → not in alice.__dict__  → found in BankAccount.__dict__
#      → returns "NationalDemoBank"
#   3. bob.bank_name    → same resolution path  → also "NationalDemoBank"
# ══════════════════════════════════════════════════════════════════════════════

def demo_class_attribute_shared():
    print("=" * 50)
    print("SECTION 1: Class attribute is shared across instances")
    print("=" * 50)

    alice = BankAccount("Alice", 500)
    bob = BankAccount("Bob", 250)

    print(f"alice.bank_name = {alice.bank_name!r}")
    print(f"bob.bank_name   = {bob.bank_name!r}")
    print(f"BankAccount.bank_name = {BankAccount.bank_name!r}")
    print()

    # Changing the class attribute affects all instances
    BankAccount.bank_name = "NationalDemoBank"
    print("After BankAccount.bank_name = 'NationalDemoBank':")
    print(f"alice.bank_name = {alice.bank_name!r}")
    print(f"bob.bank_name   = {bob.bank_name!r}")
    print("Both see the updated value — they share the class attribute.")

    # Reset for remaining demos
    BankAccount.bank_name = "DemoBank"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Instance attributes are independent
#
# Instance attributes live in each OBJECT's own `__dict__`.
# Each call to __init__ creates fresh attributes for that specific object.
# Mutating one instance's attributes (deposit, withdraw) never affects another.
#
# Flow for  carol.deposit(500):
#   1. carol.deposit(500) → self=carol, amount=500
#   2. validate amount > 0 → passes
#   3. carol.balance += 500  → modifies carol.__dict__["balance"] only
#   4. dave.balance is unchanged
# ══════════════════════════════════════════════════════════════════════════════

def demo_instance_attribute_independent():
    print("\n" + "=" * 50)
    print("SECTION 2: Instance attributes are independent")
    print("=" * 50)

    carol = BankAccount("Carol", 1000)
    dave = BankAccount("Dave", 200)

    carol.deposit(500)
    dave.withdraw(50)

    print(carol.statement())
    print(dave.statement())
    print()
    print("Deposits and withdrawals on one account do not affect the other.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: @classmethod — operates on the class, not an instance
#
# @classmethod receives the CLASS as its first argument (named `cls` by convention).
# It can read and modify CLASS attributes but has no access to instance data.
# Useful for factory methods and counters that span all instances.
#
# Flow for  BankAccount.total_accounts():
#   1. cls = BankAccount  (the class itself, not an instance)
#   2. return cls._total_accounts  (the shared counter on the class)
# ══════════════════════════════════════════════════════════════════════════════

def demo_class_method_counter():
    print("\n" + "=" * 50)
    print("SECTION 3: Class method — shared state across instances")
    print("=" * 50)

    print(f"Total accounts created so far: {BankAccount.total_accounts()}")
    eve = BankAccount("Eve", 300)  # noqa: F841
    print(f"After creating one more: {BankAccount.total_accounts()}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Instance attribute SHADOWS class attribute
#
# Setting an attribute DIRECTLY ON AN INSTANCE creates a new entry in that
# instance's own `__dict__`.  From then on, Python finds this instance entry
# FIRST and never reaches the class attribute — effectively hiding it
# ("shadowing") for that specific instance only.
#
# Flow for  frank.bank_name = "FrankPersonalBank":
#   1. Python writes to frank.__dict__["bank_name"] = "FrankPersonalBank"
#   2. frank.bank_name  → found in frank.__dict__  → "FrankPersonalBank"
#   3. BankAccount.bank_name  → still "DemoBank"  (class attr unchanged)
#   4. Other instances (alice, bob) still see "DemoBank"  (not in their __dict__)
# ══════════════════════════════════════════════════════════════════════════════

def demo_instance_shadowing_class_attr():
    print("\n" + "=" * 50)
    print("SECTION 4: Instance attribute shadows class attribute")
    print("=" * 50)

    frank = BankAccount("Frank", 0)
    print(f"frank.bank_name before override: {frank.bank_name!r}")

    # Setting an attribute on the instance creates an instance-level entry
    # that shadows (hides) the class attribute for this instance only
    frank.bank_name = "FrankPersonalBank"
    print(f"frank.bank_name after  override: {frank.bank_name!r}")
    print(f"BankAccount.bank_name unchanged: {BankAccount.bank_name!r}")
    print("Other instances are unaffected — only frank has the override.")


def main():
    demo_class_attribute_shared()
    demo_instance_attribute_independent()
    demo_class_method_counter()
    demo_instance_shadowing_class_attr()


if __name__ == "__main__":
    main()
