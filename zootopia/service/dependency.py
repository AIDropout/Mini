# # services/service_providers.p

# from fastapi import Depends
# from zootopia.manager.payment import CheckoutManager, CustomerManager, SubscriptionManager
# from .payment_service import PaymentService
# from zootopia.manager.database import DatabaseManager

# def get_payment_service():
#     database_manager = DatabaseManager()
#     checkout_manager = CheckoutManager()
#     customer_manager = CustomerManager()
#     subscription_manager = SubscriptionManager()
    
#     return PaymentService(
#         database_manager,
#         checkout_manager,
#         customer_manager,
#         subscription_manager
#     )

# payment_service_dependency = Depends(get_payment_service)