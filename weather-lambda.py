import json
import boto3
import datetime
import os
import urllib3
import random

sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
http = urllib3.PoolManager()

# Motivational quotes list
QUOTES = [
    "🌟 Keep smiling, every day is a new beginning!",
    "💪 Stay positive and make today amazing!",
    "🌈 Sunshine mixed with a little bit of rain makes a beautiful day.",
    "☀️ Take a deep breath and enjoy the moment!",
    "🌻 Keep going, the best is yet to come!"
]

def lambda_handler(event, context):
    try:
        # Environment variables
        API_KEY = os.environ['OPENWEATHER_API_KEY']
        CITY = os.environ['CITY']
        WEATHER_URL = os.environ['OPENWEATHER_URL']
        TABLE_NAME = os.environ['DYNAMODB_TABLE']
        SNS_TOPIC = os.environ['SNS_TOPIC_ARN']

        table = dynamodb.Table(TABLE_NAME)

        # IST time
        utc_now = datetime.datetime.utcnow()
        ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
        ist_time = ist_now.strftime("%Y-%m-%d %H:%M:%S")

        # Weather API call
        url = f"{WEATHER_URL}?q={CITY}&appid={API_KEY}&units=metric"
        response = http.request("GET", url)
        data = json.loads(response.data.decode("utf-8"))

        # Take first forecast for simplicity
        forecast = data['list'][0]
        temperature = forecast['main']['temp']
        humidity = forecast['main']['humidity']
        condition = forecast['weather'][0]['description'].title()
        forecast_time = forecast['dt_txt']

        # Weather tips
        tips = ""
        if temperature >= 35:
            tips += "☀️ It's hot! Wear sunscreen & stay hydrated. "
        elif temperature <= 20:
            tips += "🧥 It's cool! Wear warm clothes. "
        if "rain" in condition.lower():
            tips += "☔ Carry an umbrella. "
        if "cloud" in condition.lower() and 20 < temperature < 35:
            tips += "🌤 Pleasant weather, enjoy your day! "

        # Pick a random motivational quote
        quote = random.choice(QUOTES)

        # Compose final message
        message = f"""
🌤 Weather Forecast Alert
📍 City: {CITY}
🌡 Temperature: {temperature}°C
💧 Humidity: {humidity}%
🌥 Condition: {condition}
⏰ Forecast For: {forecast_time}
🇮🇳 Triggered At (IST): {ist_time}

💡 Tips: {tips}

💬 Motivational Quote: {quote}

- From Shivam Garud : https://shivam-garud.vercel.app/
"""

        # Send SNS email
        sns.publish(
            TopicArn=SNS_TOPIC,
            Subject=f"Weather Forecast Alert - {CITY}",
            Message=message
        )

        # Save to DynamoDB
        table.put_item(
            Item={
                "id": str(int(datetime.datetime.utcnow().timestamp())),
                "city": CITY,
                "temperature": str(temperature),
                "humidity": str(humidity),
                "condition": condition,
                "forecast_time": forecast_time,
                "triggered_ist": ist_time,
                "tips": tips,
                "quote": quote
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps("✅ Simple weather alert sent & saved successfully")
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps(f"❌ Lambda failed: {str(e)}")
        }
