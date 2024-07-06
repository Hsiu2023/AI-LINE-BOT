# 載入模組
from os import getenv

from dotenv import load_dotenv
from google import generativeai as genai
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    TextMessage,
    ReplyMessageRequest,
    ShowLoadingAnimationRequest,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, UserSource

# 讀取 .env 檔案
load_dotenv()

# 讀取環境變數
line_channel_access_token = getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_channel_secret = getenv("LINE_CHANNEL_SECRET")
gemini_api_key = getenv("GEMINI_API_KEY")

# 建立 Flask 應用程式
app = Flask(__name__)

# 設定您的 LINE Bot 憑證
line_bot_configuration = Configuration(access_token=line_channel_access_token)
line_bot_webhook_handler = WebhookHandler(line_channel_secret)

# 設定 Google Gemini API
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-pro")


# 定義 Index 路由
@app.route("/index", methods=["GET"])
def index() -> str:
    # 回應 Hello Flask
    return "Hello Flask"


# 定義 Webhook Callback 路由
@app.route("/callback", methods=["POST"])
def callback() -> str:
    # 取得 LINE Bot Webhook 請求標頭
    signature = request.headers["X-Line-Signature"]
    # 取得 LINE Bot Webhook 請求內容
    body = request.get_data(as_text=True)
    # 處理 LINE Bot Webhook 事件
    try:
        line_bot_webhook_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    # 回應 OK
    return "OK"


# 處理 LINE Bot 訊息事件
@line_bot_webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent) -> None:
    # 確認事件訊息是否為文字訊息
    assert isinstance(event.message, TextMessageContent)
    # 使用 LINE Bot API 進行回應
    with ApiClient(line_bot_configuration) as api_client:
        # 建立 Messaging API 客戶端（Messaging API 是 LINE Bot API 的其中一種，用於接收傳送訊息）
        messaging_api_client = MessagingApi(api_client)
        # 取得使用者傳送過來的訊息
        user_message = event.message.text
        # 判斷訊息來源是否為使用者
        if event.source.type == "user":
            # 確認事件來源是否為使用者
            assert isinstance(event.source, UserSource)
            # 在使用者端顯示載入動畫，顯示 5 秒
            messaging_api_client.show_loading_animation(
                show_loading_animation_request=ShowLoadingAnimationRequest(
                    chatId=event.source.user_id,
                    loadingSeconds=5,
                )
            )
        # 使用 Google Gemini 生成回應
        response = model.generate_content(user_message)
        # 發送回應給使用者
        messaging_api_client.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=response.text)],
            )
        )


# 啟動 Flask 除錯應用程式
if __name__ == "__main__":
    app.run(debug=True)
