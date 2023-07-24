import os
import io
import uuid
import boto3
from PIL import Image

region="ca-central-1"
s3_client = boto3.client('s3')
thumbnail_size = int(os.environ["TUMBTAIL_SIZE"])
db_table = str(os.environ["DYNAMO_TABLE"])
dynamodb = boto3.resource('dynamodb', region_name=region)


def s3_tumbnail_generator(event, context):
    
    # Parse the event data
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    if key.endswith("_thumbnail.png"):
        return
        
    # download the object, read its content
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    image_content = obj['Body'].read()
    
    
    #create tumbnail image
    thumbnail_content = create_thumbnail(image_content)
    
    #create new key
    thumbnail_key = add_thumbnail_suffix(key)
    
    #upload to s3
    s3_client.put_object(Bucket=bucket, Key=thumbnail_key, Body=thumbnail_content)
    
    #get the url
    url = f"https://s3.${region}.amazonaws.com/${bucket}/${thumbnail_key}"

    store_tumbnail_url_to_dynamoDB(img_url=url)
    
    return url


def create_thumbnail(image_content):
    # Create a Pillow Image object from the image content
    image = Image.open(io.BytesIO(image_content))

    # Create the thumbnail image
    image.thumbnail((thumbnail_size, thumbnail_size))
    

    # Save the thumbnail as a new image in memory
    thumbnail_bytes = io.BytesIO()
    image.save(thumbnail_bytes, format=image.format)

    # Get the thumbnail content as bytes
    thumbnail_content = thumbnail_bytes.getvalue()

    return thumbnail_content


def add_thumbnail_suffix(original_key):
    
    split_key = original_key.split(".", 1)
    
    thumbnail_key = split_key[0] + "_thumbnail.png"

    return thumbnail_key


def store_tumbnail_url_to_dynamoDB(img_url):
    table = dynamodb.Table(db_table)
    
    item={
        "id": str(uuid.uuid4()),
        "url": str(img_url)
    }  
    
    # Put the item into the DynamoDB table
    table.put_item(Item=item)
    
    return {"status": "ok", "msg": item["url"]}
