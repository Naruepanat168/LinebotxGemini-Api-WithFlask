from flask import Flask, request, abort
from flask import Flask, request, render_template
from dotenv import load_dotenv, dotenv_values
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import os
import google.generativeai as genai # API Gemini

def create_generative_model():
   
    api_key = os.getenv('GOOGLE_API_KE')
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]

    return genai.GenerativeModel(model_name="gemini-pro",
                                generation_config=generation_config,
                                safety_settings=safety_settings)


app = Flask(__name__)

load_dotenv()
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN",None)
channel_secret = os.getenv("LINE_CHANNEL_SECRET",None)
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# โหลดโมเดล Gemini
model = create_generative_model()

# Webhook route for LINE Messaging API
@app.route('/webhook', methods=['POST'])
def webhook():
    # Get X-Line-Signature header and request body
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # Handle webhook events
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)  

    return 'Connection'


# Event handler for text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Extract message text from the event
    message_text = event.message.text

    convo = model.start_chat(history=[])
    convo.send_message(message_text)
    reponse = convo.last.text

    # Reply to the user with the same message
    reply_message = TextSendMessage(text=reponse)
    line_bot_api.reply_message(event.reply_token, reply_message)

if __name__ == '__main__':
    app.run(port=8000,debug=True)