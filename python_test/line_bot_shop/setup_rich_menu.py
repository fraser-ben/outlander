from PIL import Image, ImageDraw, ImageFont
import os
import sys
from dotenv import load_dotenv
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuRequest,
    RichMenuSize,
    RichMenuArea,
    RichMenuBounds,
    MessageAction
)

load_dotenv()

def generate_image():
    """Generates a high-quality 2500x843 PNG background for the Rich Menu with 2 buttons."""
    width, height = 2500, 843
    img = Image.new("RGB", (width, height), "#0B0F19")
    draw = ImageDraw.Draw(img)
    
    # Button 1 (Shop): Dark blue/indigo card
    draw.rectangle([30, 30, 1220, 813], fill="#1E293B", outline="#6366F1", width=8)
    
    # Button 2 (Cart): Dark grey/emerald card
    draw.rectangle([1280, 30, 2470, 813], fill="#111827", outline="#10B981", width=8)
    
    # Font Configuration (Using standard fonts)
    font_path_zh = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
    font_path_en = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    try:
        font_title = ImageFont.truetype(font_path_zh, 80)
    except IOError:
        print("Warning: Chinese font not found, using default.")
        font_title = ImageFont.load_default()
        
    try:
        font_subtitle = ImageFont.truetype(font_path_en, 50)
    except IOError:
        print("Warning: English font not found, using default.")
        font_subtitle = ImageFont.load_default()
        
    # Draw Left Button Text (Shop Menu)
    draw.text((625, 320), "商品菜單", fill="#FFFFFF", font=font_title, anchor="mm")
    draw.text((625, 470), "SHOP MENU", fill="#A5B4FC", font=font_subtitle, anchor="mm")
    
    # Draw Right Button Text (My Cart)
    draw.text((1875, 320), "我的購物車", fill="#FFFFFF", font=font_title, anchor="mm")
    draw.text((1875, 470), "MY CART", fill="#A7F3D0", font=font_subtitle, anchor="mm")
    
    img.save("rich_menu.png")
    print("Generated rich_menu.png successfully!")

def setup_rich_menu():
    """Registers the Rich Menu layout and image with the LINE Messaging API."""
    channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    if not channel_access_token or channel_access_token.startswith('your_'):
        print("Error: LINE_CHANNEL_ACCESS_TOKEN is not configured or holds a placeholder in the .env file.")
        sys.exit(1)

    configuration = Configuration(access_token=channel_access_token)
    
    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)
        
        # 1. Define interactive coordinates mapping
        areas = [
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=1250, height=843),
                action=MessageAction(label="進入商店", text="SHOP")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1250, y=0, width=1250, height=843),
                action=MessageAction(label="我的購物車", text="CART")
            )
        ]
        
        # 2. Build the Rich Menu metadata object
        rich_menu_request = RichMenuRequest(
            size=RichMenuSize(width=2500, height=843),
            selected=True,
            name="Shop Rich Menu",
            chat_bar_text="選單 / Menu",
            areas=areas
        )
        
        # 3. Create the Rich Menu on LINE platform
        print("Creating rich menu on LINE platform...")
        response = api.create_rich_menu(rich_menu_request=rich_menu_request)
        rich_menu_id = response.rich_menu_id
        print(f"Created Rich Menu ID: {rich_menu_id}")
        
        # 4. Upload the generated background image using the Blob API
        print("Uploading rich_menu.png to LINE servers...")
        blob_api = MessagingApiBlob(api_client)
        with open("rich_menu.png", "rb") as f:
            blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_id,
                body=f.read(),
                _headers={"Content-Type": "image/png"}
            )
        print("Uploaded image successfully!")
        
        # 5. Make it the default menu for all users
        print("Setting rich menu as default for all users...")
        api.set_default_rich_menu(rich_menu_id=rich_menu_id)
        print("Rich Menu successfully activated globally!")

if __name__ == "__main__":
    generate_image()
    setup_rich_menu()
