import boto3
import base64
from urllib.parse import unquote

def split_document(content, max_chunk_size):
    chunks = [content[i:i + max_chunk_size] for i in range(0, len(content), max_chunk_size)]
    return chunks

def translate_document_chunks(source_bucket, source_key, target_bucket, target_key, source_language, target_language, content_type, max_chunk_size = 102400):
    # Initialize AWS Translate client
    translate_client = boto3.client('translate')

    # Initialize AWS S3 client
    s3_client = boto3.client('s3')

    # Get the content of the document from the source S3 bucket
    response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    content = response['Body'].read().decode('utf-8')

    # Split the content into smaller chunks
    content_chunks = split_document(content, max_chunk_size)

    translated_chunks = []

    # Specify the content type based on the document format
    if content_type == 'txt':
        content_type = 'text/plain'
    elif content_type == 'doc' or content_type == 'docx':
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    for chunk in content_chunks:
        # Set up the translation request for each chunk
        translation_request = {
            'Document': {
                'Content': chunk,
                'ContentType': content_type
            },
            'SourceLanguageCode': source_language,
            'TargetLanguageCode': target_language,
        }

        # Perform the translation for each chunk
        translation_response = translate_client.translate_document(**translation_request)

        # Get the translated content for each chunk
        translated_chunks.append(translation_response['TranslatedDocument']['Content'])

    # Combine translated chunks into a single translated document
    translated_document = ''.join(translated_chunks)

    # Upload the translated content to the target S3 bucket
    s3_client.put_object(Bucket=target_bucket, Key=target_key, Body=translated_document.encode('utf-8'))
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
    translate_document_chunks(source_bucket, decoded_key, target_bucket, target_key, source_language=source_language, target_language=target_language,content_type=extension)
