import os
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent
import json
from dotenv import load_dotenv
import re
import csv
from datetime import datetime
import uuid

load_dotenv()

app = FastAPI()

# Configuration
channel_secret = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# Mock Database
PRODUCTS = {
    "A": {"name": "原味蘿蔔糕", "price": 150},
    "B": {"name": "香菇蘿蔔糕", "price": 160},
    "C": {"name": "港式蘿蔔糕", "price": 180},
    "E": {"name": "干貝蘿蔔糕", "price": 260},
}
# user_carts: { user_id: { item_id: quantity } }
user_carts = {}
CARTS_FILE = "carts.json"

def load_carts():
    global user_carts
    if os.path.exists(CARTS_FILE):
        try:
            with open(CARTS_FILE, 'r', encoding='utf-8') as f:
                user_carts = json.load(f)
        except Exception as e:
            print(f"Error loading carts: {e}", flush=True)
            user_carts = {}
    else:
        user_carts = {}

def save_carts():
    try:
        with open(CARTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_carts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving carts: {e}", flush=True)

load_carts()

ORDERS_FILE = "orders.csv"

def init_orders_file():
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Order_ID", "Timestamp", "User_ID", "Items", "Total_Price", "Status"])

init_orders_file()

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    body = await request.body()
    body_text = body.decode('utf-8')
    
    # 1. Verify Signature
    try:
        handler.parser.parse(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Process Events
    try:
        data = json.loads(body_text)
        for event_dict in data.get('events', []):
            process_event(event_dict)
    except Exception as e:
        print(f"DEBUG: Error in callback processing: {e}", flush=True)

    return 'OK'

def process_event(event):
    source = event.get('source', {})
    user_id = source.get('userId')
    if not user_id:
        return

    event_type = event.get('type')
    reply_token = event.get('replyToken')

    if event_type == "message":
        message = event.get('message', {})
        if message.get('type') == "text":
            text = message.get('text', '').upper().strip()
            print(f"DEBUG: Received text message: {message.get('text')}", flush=True)
            if text == "SHOP":
                send_shop_menu(reply_token)
            elif text == "CART":
                send_cart_summary(reply_token, user_id)
            else:
                match = re.match(r'^([ABCE])\s*(\d+)$', text)
                if match:
                    item_id = match.group(1)
                    quantity = int(match.group(2))
                    update_cart(user_id, item_id, quantity)
                    send_cart_summary(reply_token, user_id, f"✅ 已加入 {quantity} 份 {PRODUCTS[item_id]['name']}")
    
    elif event_type == "postback":
        postback = event.get('postback', {})
        data = postback.get('data', '')
        params = dict(item.split('=') for item in data.split('&'))
        action = params.get('action')
        item_id = params.get('item')

        if action == 'add':
            update_cart(user_id, item_id, 1)
            send_cart_summary(reply_token, user_id)
        elif action == 'remove':
            update_cart(user_id, item_id, -1)
            send_cart_summary(reply_token, user_id)
        elif action == 'checkout':
            handle_checkout(reply_token, user_id)
        elif action == 'clear':
            if user_id in user_carts:
                del user_carts[user_id]
                save_carts()
            send_cart_summary(reply_token, user_id, "🛒 購物車已清空")

def update_cart(user_id, item_id, delta):
    if user_id not in user_carts:
        user_carts[user_id] = {}
    
    current_qty = user_carts[user_id].get(item_id, 0)
    new_qty = max(0, current_qty + delta)
    
    if new_qty <= 0:
        if item_id in user_carts[user_id]:
            del user_carts[user_id][item_id]
    else:
        user_carts[user_id][item_id] = new_qty
    
    save_carts()


def send_shop_menu(reply_token):
    flex_contents = {
        "type": "carousel",
        "contents": [
            create_product_bubble(item_id, info) 
            for item_id, info in PRODUCTS.items()
        ]
    }
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="商品菜單", contents=FlexContainer.from_dict(flex_contents))]
            )
        )

def create_product_bubble(item_id, info):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": info["name"], "weight": "bold", "size": "xl"},
                {"type": "text", "text": f"${info['price']}", "size": "md", "color": "#999999"},
                {"type": "text", "text": f"輸入 '{item_id} 數量' 即可快速加入", "size": "xs", "color": "#aaaaaa", "margin": "md"}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "加入購物車 (+1)",
                        "data": f"action=add&item={item_id}"
                    },
                    "style": "primary"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "減少數量 (-1)",
                        "data": f"action=remove&item={item_id}"
                    },
                    "style": "secondary"
                }
            ]
        }
    }

def send_cart_summary(reply_token, user_id, prefix_text=""):
    cart = user_carts.get(user_id, {})
    if not cart:
        summary_text = prefix_text + ("\n\n" if prefix_text else "") + "您的購物車目前是空的。"
        messages = [TextMessage(text=summary_text)]
    else:
        items_summary = []
        total_price = 0
        for item_id, quantity in cart.items():
            product = PRODUCTS[item_id]
            subtotal = product['price'] * quantity
            total_price += subtotal
            items_summary.append(f"({item_id}) {product['name']} x{quantity}: ${subtotal}")
        
        summary_body = (prefix_text + ("\n\n" if prefix_text else "")) + "🛒 購物車明細:\n" + "\n".join(items_summary) + f"\n\n總計: ${total_price}"
        
        flex_contents = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "購物車明細", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": summary_body, "wrap": True, "margin": "md"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "💳 結帳 (Checkout)",
                            "data": "action=checkout"
                        },
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "🗑️ 清空購物車",
                            "data": "action=clear"
                        },
                        "style": "secondary"
                    }
                ]
            }
        }
        messages = [FlexMessage(alt_text="購物車摘要", contents=FlexContainer.from_dict(flex_contents))]
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=messages
            )
        )

def handle_checkout(reply_token, user_id):
    cart = user_carts.get(user_id, {})
    if not cart:
        return

    order_id = str(uuid.uuid4())[:8].upper()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    items_list = []
    total_price = 0
    for item_id, quantity in cart.items():
        product = PRODUCTS[item_id]
        total_price += product['price'] * quantity
        items_list.append(f"{product['name']}x{quantity}")
    
    items_str = ", ".join(items_list)
    
    # Save to CSV
    with open(ORDERS_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([order_id, timestamp, user_id, items_str, total_price, "Unfinished"])
    
    # Clear Cart
    if user_id in user_carts:
        del user_carts[user_id]
        save_carts()
    
    # Reply confirmation
    summary_text = f"🎉 訂單已成功送出！\n\n訂單編號：#{order_id}\n時間：{timestamp}\n總計：${total_price}\n\n我們將盡快為您處理，謝謝！"
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=summary_text)]
            )
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
