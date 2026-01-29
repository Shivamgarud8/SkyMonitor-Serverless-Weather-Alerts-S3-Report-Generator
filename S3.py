import boto3
import datetime
import os
import random

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Motivational quotes
QUOTES = [
    "🌟 Keep smiling, every day is a new beginning!",
    "💪 Stay positive and make today amazing!",
    "🌈 Sunshine mixed with a little bit of rain makes a beautiful day.",
    "☀️ Take a deep breath and enjoy the moment!",
    "🌻 Keep going, the best is yet to come!"
]

def generate_marathi_tip(temp, condition):
    tips = ""
    commentary = ""
    
    if temp >= 35:
        tips += "☀️ खूप गरम आहे! सनस्क्रीन लावा, भरपूर पाणी प्या. "
        commentary += "Dupati खूप गरम आहे. "
    elif temp <= 20:
        tips += "🧥 थंडी आहे! गरम कपडे घालावे. "
        commentary += "Dupati आरामात ठेवावी. "
    
    if "rain" in condition.lower():
        tips += "☔ पावसाची शक्यता आहे, छत्री सोबत ठेवा. "
        commentary += "सापधाऊ पाऊस आला आहे. "
    elif "cloud" in condition.lower() and 20 < temp < 35:
        tips += "🌤 हलके वातावरण, दिवस आनंददायी आहे. "
        commentary += "हवामान हलके ढगाळ आहे. "
    elif "clear" in condition.lower() and temp > 20:
        tips += "☀️ सूर्यप्रकाशाने दिवस गरम राहील. "
        commentary += "सूर्यप्रकाशाची तीव्रता वाढली आहे. "
    
    return tips, commentary

def lambda_handler(event, context):
    try:
        # Environment variables
        TABLE_NAME = os.environ['DYNAMODB_TABLE']
        S3_BUCKET = os.environ['S3_BUCKET_NAME']
        CITY = os.environ['CITY']
        
        table = dynamodb.Table(TABLE_NAME)
        
        # Get yesterday's date
        yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Fetch yesterday's weather data from DynamoDB
        response = table.scan(
            FilterExpression="begins_with(forecast_time, :y)",
            ExpressionAttributeValues={":y": yesterday}
        )
        items = sorted(response.get('Items', []), key=lambda x: x['forecast_time'])
        
        if not items:
            return {
                "statusCode": 200,
                "body": "No data for yesterday."
            }
        
        # Generate report
        report_lines = []
        report_lines.append(f"📢 शुभ प्रभात! दिनांक: {yesterday}")
        report_lines.append(f"शहर: {CITY}")
        report_lines.append("-" * 50)
        
        for forecast in items:
            temp = float(forecast.get('temperature', 0))
            humidity = forecast.get('humidity', 'NA')
            condition = forecast.get('condition', 'NA')
            forecast_time = forecast.get('forecast_time', 'NA')
            
            tips, commentary = generate_marathi_tip(temp, condition)
            quote = random.choice(QUOTES)
            
            time_str = datetime.datetime.strptime(forecast_time, "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p")
            
            report_lines.append(f"⏰ वेळ: {time_str}")
            report_lines.append(f"🌡 तापमान: {temp}°C  💧 आर्द्रता: {humidity}%")
            report_lines.append(f"🌥 परिस्थिती: {condition}")
            report_lines.append(f"💡 सूचना: {tips.strip()}")
            report_lines.append(f"🗞 अहवाल: {commentary.strip()}")
            report_lines.append(f"💬 प्रेरणादायी वाक्य: {quote}")
            report_lines.append("-" * 50)
        
        report_lines.append("हवामान अहवाल Shubharam News Channel शैलीत तयार केला आहे.")
        report_lines.append("Report by Shivam Garud: https://shivam-garud.vercel.app/")
        
        report_text = "\n".join(report_lines)
        
        # Upload to S3
        s3_key = f"Marathi_Weather_Report_{yesterday}.txt"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=report_text.encode('utf-8')
        )
        
        return {
            "statusCode": 200,
            "body": f"✅ Marathi weather report generated and uploaded to S3: {s3_key}"
        }
    
    except Exception as e:
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "body": f"❌ Lambda failed: {str(e)}"
        }
