import os
import json
from re import T
import tempfile
from attr import has
from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent
)

app = Flask(__name__)

configuration = Configuration(access_token='access_token')
handler = WebhookHandler('line_secret')


@app.route("/", methods=['GET'])
def home():
    return "Hello, World!"
# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    is_image = False
    if isinstance(event.message, ImageMessageContent):
        ext = 'jpg'
        is_image = True
        
    if is_image:
        upload_path = './uploads'
        with ApiClient(configuration) as api_client:
            line_bot_blob_api = MessagingApiBlob(api_client)
            message_content = line_bot_blob_api.get_message_content(message_id=event.message.id)
            with tempfile.NamedTemporaryFile(dir=upload_path, prefix=ext + '-', delete=False) as tf:
                tf.write(message_content)
                tempfile_path = tf.name

        dist_path = tempfile_path + '.' + ext
        dist_name = os.path.basename(dist_path)
        os.rename(tempfile_path, dist_path)
    
    with ApiClient(configuration) as api_client:
        
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="你已成功上傳")]
            )
        )
        
        
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    with ApiClient(configuration) as api_client:
        print(event)
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text)]
            )
        )

if __name__ == "__main__":
    app.run( host='0.0.0.0', port=5000, debug=True)