from enum import Enum


class SubscriptionStatus(Enum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"

    @classmethod
    def from_string(cls, status: str):
        try:
            return cls(status.lower())
        except ValueError:
            raise ValueError(f"'{status}' is not a valid SubscriptionStatus")

    def __str__(self):
        return self.value
