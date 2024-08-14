# services/service_providers.py

from database import DatabaseManager
from auth.tier_permissions_auth import TierPermissions

class Service:
    def __init__(self, database_manager: DatabaseManager, tier_permissions: TierPermissions):
        self.database_manager = database_manager
        self.tier_permissions = tier_permissions

    # The Service class might include some common utility methods or properties
    # that are shared across different service classes.
    
    # For example:
    async def get_user(self, user_id: str):
        return await self.database_manager.get_user(user_id)
    
    def check_permission(self, user_id: str, action: str):
        return self.tier_permissions.check_permission(user_id, action)

    # Other common methods that might be useful across different services...

from fastapi import Depends
from zootopia.service.payment import PaymentService, CheckoutManager, CustomerManager, SubscriptionManager
from zootopia.service.database import DatabaseManager

def get_payment_service():
    database_manager = DatabaseManager()
    checkout_manager = CheckoutManager()
    customer_manager = CustomerManager()
    subscription_manager = SubscriptionManager()
    
    return PaymentService(
        database_manager,
        checkout_manager,
        customer_manager,
        subscription_manager
    )

payment_service_dependency = Depends(get_payment_service)


database = DatabaseManager()