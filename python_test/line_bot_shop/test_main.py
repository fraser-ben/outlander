import json
import hmac
import hashlib
import base64
import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app, channel_secret, user_carts, PRODUCTS, ORDERS_FILE

client = TestClient(app)

def generate_signature(body, secret):
    hash = hmac.new(secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(hash).decode('utf-8')

@pytest.fixture(autouse=True)
def clear_carts():
    user_carts.clear()

def test_callback_invalid_signature():
    response = client.post(
        "/callback",
        headers={"X-Line-Signature": "invalid_signature"},
        content="some body"
    )
    assert response.status_code == 400

@patch('main.MessagingApi')
@patch('linebot.v3.messaging.ApiClient.__enter__')
def test_handle_checkout(mock_api_client, mock_messaging_api_class):
    mock_instance = mock_messaging_api_class.return_value
    user_id = "U_CHECKOUT"
    
    # Pre-populate cart: A x2, B x1
    user_carts[user_id] = {'A': 2, 'B': 1}
    # Expected total: 150*2 + 160*1 = 460
    
    # Remove existing orders file if any for clean test
    if os.path.exists(ORDERS_FILE):
        os.remove(ORDERS_FILE)
    from main import init_orders_file
    init_orders_file()

    body = {
        "destination": "xxx",
        "events": [{
            "type": "postback",
            "postback": {"data": "action=checkout"},
            "source": {"type": "user", "userId": user_id},
            "replyToken": "token_checkout",
            "timestamp": 1,
            "mode": "active",
            "webhookEventId": "id_checkout",
            "deliveryContext": {"isRedelivery": False}
        }]
    }
    body_str = json.dumps(body)
    client.post("/callback", headers={"X-Line-Signature": generate_signature(body_str, channel_secret)}, content=body_str)
    
    # 1. Cart should be cleared
    assert user_id not in user_carts
    
    # 2. File should exist and contain the order
    assert os.path.exists(ORDERS_FILE)
    with open(ORDERS_FILE, mode='r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        assert len(lines) == 2 # Header + 1 row
        last_row = lines[-1]
        assert "U_CHECKOUT" in last_row
        assert "460" in last_row
        assert "Unfinished" in last_row
        assert "原味蘿蔔糕x2" in last_row
        assert "香菇蘿蔔糕x1" in last_row

    # 3. Confirmation message sent
    assert mock_instance.reply_message.called
    reply_text = mock_instance.reply_message.call_args[0][0].messages[0].text
    assert "訂單已成功送出" in reply_text
    assert "$460" in reply_text

@patch('main.MessagingApi')
@patch('linebot.v3.messaging.ApiClient.__enter__')
def test_handle_text_input_quantity(mock_api_client, mock_messaging_api_class):
    mock_instance = mock_messaging_api_class.return_value
    user_id = "U_TEXT"
    
    # User sends "A 5"
    body = {
        "destination": "xxx",
        "events": [{
            "type": "message",
            "message": {"type": "text", "id": "1", "text": "A 5"},
            "timestamp": 1,
            "source": {"type": "user", "userId": user_id},
            "replyToken": "token1",
            "mode": "active",
            "webhookEventId": "id1",
            "deliveryContext": {"isRedelivery": False}
        }]
    }
    body_str = json.dumps(body)
    client.post("/callback", headers={"X-Line-Signature": generate_signature(body_str, channel_secret)}, content=body_str)
    
    assert user_carts[user_id]['A'] == 5
    assert mock_instance.reply_message.called
    reply_msg = mock_instance.reply_message.call_args[0][0].messages[0]
    # In send_cart_summary, if cart not empty, it sends FlexMessage
    assert reply_msg.type == "flex"
    assert reply_msg.alt_text == "購物車摘要"

@patch('main.MessagingApi')
@patch('linebot.v3.messaging.ApiClient.__enter__')
def test_handle_decrement_quantity(mock_api_client, mock_messaging_api_class):
    mock_instance = mock_messaging_api_class.return_value
    user_id = "U_DEC"
    
    # Pre-populate cart: A x2
    user_carts[user_id] = {'A': 2}
    
    # Remove 1
    body = {
        "destination": "xxx",
        "events": [{
            "type": "postback",
            "postback": {"data": "action=remove&item=A"},
            "source": {"type": "user", "userId": user_id},
            "replyToken": "token2",
            "timestamp": 1,
            "mode": "active",
            "webhookEventId": "id2",
            "deliveryContext": {"isRedelivery": False}
        }]
    }
    body_str = json.dumps(body)
    client.post("/callback", headers={"X-Line-Signature": generate_signature(body_str, channel_secret)}, content=body_str)
    
    assert user_carts[user_id]['A'] == 1
    
    # Remove again (should delete entry)
    client.post("/callback", headers={"X-Line-Signature": generate_signature(body_str, channel_secret)}, content=body_str)
    assert 'A' not in user_carts[user_id]
