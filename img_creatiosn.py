import boto3
from PIL import Image, ImageDraw, ImageFont
import io

BUCKET_NAME = "my-weather-reports-marathi"
INPUT_FOLDER = "input/"
OUTPUT_FOLDER = "output/"
BACKGROUND_IMG = "assets/background.jpg"

s3 = boto3.client("s3")

def read_weather_file(key):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    content = obj["Body"].read().decode("utf-8")
    data = {}
    for line in content.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data

def create_weather_image(data):
    bg_obj = s3.get_object(Bucket=BUCKET_NAME, Key=BACKGROUND_IMG)
    bg = Image.open(io.BytesIO(bg_obj["Body"].read())).convert("RGBA")

    overlay = Image.new("RGBA", bg.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)
    panel_color = (255,255,255,120)
    draw.rounded_rectangle((80,180,bg.width-80,520), 30, fill=panel_color)
    draw.rounded_rectangle((80,560,bg.width-80,900), 30, fill=panel_color)

    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
    text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)

    # Header
    draw.text((80,50), "शुभ प्रभात!", font=title_font, fill="#FFD700")
    draw.text((80,120), f"दिनांक: {data['DATE']} | शहर: {data['CITY']}", font=text_font, fill="white")

    # Day
    y = 210
    draw.text((110,y), f"🕒 वेळ: {data['TIME1']}", font=text_font, fill="black"); y+=50
    draw.text((110,y), f"🌡 तापमान: {data['TEMP1']}°C   💧 आर्द्रता: {data['HUMIDITY1']}%", font=text_font, fill="black"); y+=50
    draw.text((110,y), f"🌥 परिस्थिती: {data['CONDITION1']}", font=text_font, fill="black"); y+=50
    draw.text((110,y), f"💬 {data['QUOTE1']}", font=text_font, fill="black")

    # Night
    y = 590
    draw.text((110,y), f"🕘 वेळ: {data['TIME2']}", font=text_font, fill="black"); y+=50
    draw.text((110,y), f"🌡 तापमान: {data['TEMP2']}°C   💧 आर्द्रता: {data['HUMIDITY2']}%", font=text_font, fill="black"); y+=50
    draw.text((110,y), f"🌥 परिस्थिती: {data['CONDITION2']}", font=text_font, fill="black"); y+=50
    draw.text((110,y), f"💬 {data['QUOTE2']}", font=text_font, fill="black")

    draw.text((bg.width//2-250, bg.height-60), "Report by: Shivam Garud | shivam-garud.vercel.app", font=small_font, fill="white")

    final_img = Image.alpha_composite(bg, overlay)
    return final_img.convert("RGB")

def upload_image(image, date):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    key = f"{OUTPUT_FOLDER}Weather_Report_{date}.png"
    s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=buffer, ContentType="image/png")
    print("Uploaded:", key)

def lambda_handler(event, context):
    # EventBridge / S3 Trigger provides file info
    for record in event.get("Records", []):
        key = record["s3"]["object"]["key"]
        if key.endswith(".txt") and key.startswith(INPUT_FOLDER):
            data = read_weather_file(key)
            image = create_weather_image(data)
            upload_image(image, data["DATE"])
    return {"status": "SUCCESS"}
