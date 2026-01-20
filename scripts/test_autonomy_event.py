import requests
import json
import base64
import uuid

def test_webhook():
    url = "http://127.0.0.1:8000/hooks/pubsub"
    
    # Mock Event Payload
    event_payload = {
        "source": "manual_test",
        "item_count": 5,
        "database_id": "db_internal_123"
    }
    
    # Encode as Pub/Sub expects
    data_str = json.dumps(event_payload)
    data_b64 = base64.b64encode(data_str.encode("utf-8")).decode("utf-8")
    
    # Pub/Sub Envelope
    envelope = {
        "message": {
            "data": data_b64,
            "messageId": str(uuid.uuid4()),
            "attributes": {
                "event_type": "notion.write"
            }
        }
    }
    
    print(f"📤 Sending Event to {url}...")
    try:
        response = requests.post(url, json=envelope)
        print(f"📥 Response Code: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook accepted event.")
        else:
            print("❌ Webhook failed.")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_webhook()
