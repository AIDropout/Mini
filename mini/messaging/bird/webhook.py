"""This file is IMPORTANT. For managing our bird webhooks."""
import asyncio
from mini.messaging.bird.bird import BirdManager

class WebhookManager:
    def __init__(self):
        self.bird_provider = BirdManager()

    async def list_webhooks(self):
        try:
            webhooks = self.bird_provider._get_existing_webhooks()
            if webhooks and "results" in webhooks:
                print("\nExisting Webhooks: \n---")
                for webhook in webhooks["results"]:
                    print(f"Webhook ID: {webhook['id']}")
                    print(f"URL: {webhook['url']}")
                    print(f"Event: {webhook['event']}")
                    print(f"Service: {webhook['service']}")

                    channel_id = None
                    if 'eventFilters' in webhook:
                        for filter in webhook['eventFilters']:
                            if filter['key'] == 'channelId':
                                channel_id = filter['value']
                                break
                    print(f"Channel ID: {channel_id}")
                    print("---")
                print(f"Total webhooks: {len(webhooks['results'])}")
            else:
                print("No webhooks found.")
        except Exception as e:
            print(f"Error retrieving webhooks: {e}")

    async def delete_webhook(self, webhook_id):
        try:
            self.bird_provider._delete_webhook(webhook_id)
            print(f"Webhook with ID {webhook_id} deleted successfully.")
        except Exception as e:
            print(f"Error deleting webhook: {e}")

    async def add_webhook(self, channel_id):
        try:
            self.bird_provider.set_sender(channel_id)
            await self.bird_provider.register_webhook("sms.inbound", "https://app-kilu.onrender.com/rooms/respond")
            print(f"Webhook for event added successfully with Channel ID: {channel_id}")
        except Exception as e:
            print(f"Error adding webhook: {e}")

async def main():
    manager = WebhookManager()
    
    while True:
        print("\nWebhook Manager")
        print("1. List all webhooks")
        print("2. Delete webhook")
        print("3. Add webhook")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == '1':
            await manager.list_webhooks()
        elif choice == '2':
            webhook_id = input("Enter webhook ID to delete: ")
            await manager.delete_webhook(webhook_id)
        elif choice == '3':
            channel_id = input("Enter channel ID: ")
            await manager.add_webhook(channel_id)
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())