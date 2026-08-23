import json
import random
import time
import uuid
from faker import Faker

fake = Faker('en_IN')
merchant_name = "Ganga Osian Square Property Management"
reasons = ['fraudulent', 'unrecognized', 'product_not_delivered', 'duplicate']

disputes = []
for i in range(50):
    amount = random.randint(5000, 75000) * 100 # Amount in paise (INR)
    
    dispute = {
        "entity": "event",
        "event": "payment.dispute.under_review",
        "contains": ["dispute"],
        "payload": {
            "dispute": {
                "entity": {
                    # Using Python's native uuid library here
                    "id": f"disp_{uuid.uuid4().hex[:14]}",
                    "entity": "dispute",
                    "payment_id": f"pay_{uuid.uuid4().hex[:14]}",
                    "amount": amount,
                    "currency": "INR",
                    "reason_code": random.choice(reasons),
                    "status": "under_review",
                    "created_at": int(time.time()),
                    "metadata": {
                        "customer_name": fake.name(),
                        "description": f"Commercial lease and maintenance - {fake.month_name()}"
                    }
                }
            }
        }
    }
    disputes.append(dispute)

with open('synthetic_disputes.json', 'w') as f:
    json.dump(disputes, f, indent=4)
    
print(f"Generated 50 synthetic disputes for {merchant_name}")