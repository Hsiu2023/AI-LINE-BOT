from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
from dotenv import load_dotenv


app = Flask(__name__)

# 設置您的LINE Bot憑證
line_bot_api = LineBotApi('LINE_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('LINE_CHANNEL_SECRET')

# 設置Google Gemini API
genai.configure(api_key='GEMINI_API_KEY')
model = genai.GenerativeModel('gemini-pro')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    # 使用Google Gemini生成回應
    response = model.generate_content(user_message)
    
    # 發送回應給用戶
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response.text)
    )



    
@app.route("/index", methods=['GET'])
def index():
    return "Hello Flask"


if __name__ == "__main__":
    app.run()
