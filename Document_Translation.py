import boto3
import base64
from urllib.parse import unquote

def translate_document(source_bucket, source_key, target_bucket, target_key, source_language, target_language, content_type):
    # Initialize AWS Translate client
    translate_client = boto3.client('translate')

    # Initialize AWS S3 client
    s3_client = boto3.client('s3')

    # Get the content of the document from the source S3 bucket
    response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    content = response['Body'].read()
    print(content)
    # Encode the content using base64
    #encoded_content = base64.b64encode(content)

    # Specify the content type based on the document format (e.g., 'text/plain' or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    if content_type == 'txt':
        content_type = 'text/plain'
    if content_type == 'doc' or content_type == 'docx':
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    # Set up the translation request
    translation_request = {
        'Document': {
            'Content': content,
            'ContentType': content_type
        },
        'SourceLanguageCode': source_language,
        'TargetLanguageCode': target_language,
        
    }

    # Perform the translation
    translation_response = translate_client.translate_document(**translation_request)

    # Get the translated content
    #translated_content = base64.b64decode(translation_response['TranslatedDocument']['Content'])
    translated_content = translation_response['TranslatedDocument']['Content']
    print(translation_response)
    
    # Upload the translated content to the target S3 bucket
    s3_client.put_object(Bucket=target_bucket, Key=target_key, Body=translated_content)
    print("Translated", target_key)

def lambda_handler(event, context):
    # Extract file information from S3 event
    source_key = event['Records'][0]['s3']['object']['key']
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    
    print(source_key)

    decoded_key = unquote(source_key)
    split_name = decoded_key.split(".")
    extension = split_name[-1]
    name_desc = split_name[0].split('|')
    print(split_name)
    print(extension,name_desc)
    file_name = name_desc[2]
    source_language = name_desc[0]
    target_language = name_desc[1]
    print(file_name,source_language,target_language)
    file_name = file_name+target_language+'.'+extension
    print(file_name)

    # Specify target bucket and key for translated document
    target_bucket = 'documentoutput'
    target_key = file_name
    
    # Translate the document and store the result in the target S3 bucket
    print(file_name)
    translate_document(source_bucket, decoded_key, target_bucket, target_key, source_language=source_language, target_language=target_language,content_type=extension)
