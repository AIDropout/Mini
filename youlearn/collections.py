class Subscription(BaseModel):
    id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    tier: str = "free"

    def to_dict(self):
        data = self.model_dump()
        if 'created_at' in data and data['created_at'] is not None:
            data['created_at'] = data['created_at'].isoformat()
        return data


class Customer(BaseDocument):
    id: str = Field(alias="_id")
    user: Link[User]
    subscription: Optional[Subscription] = Field(default_factory=Subscription)
    metadata: Dict = {}

    class Settings:
        name = "customers"