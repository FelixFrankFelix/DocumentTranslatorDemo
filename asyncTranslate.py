from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import boto3
import uuid
import io
from botocore.exceptions import NoCredentialsError
from mangum import Mangum

app = FastAPI()

# AWS S3 Configuration
INPUT_S3_BUCKET_NAME = 'demodocumentinput'
OUTPUT_S3_BUCKET_NAME = 'demodocumentoutput'
S3_REGION = 'us-east-1'
AWS_ACCESS_KEY_ID = "AKIA6ODU77IO5BEWVLND"
AWS_SECRET_ACCESS_KEY = "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"

# Initialize Amazon Translate client
# Get role credentials
#session = boto3.Session()
#credentials = session.get_credentials()

# Create Translate client using role credentials
#translate_client = boto3.client('translate', region_name=S3_REGION, aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
print( "Starting :::::::::::::::")
session = boto3.Session()
client = session.client('sts')

print( "assuming role :::::::::::::::")
#response = client.assume_role(
#    RoleArn="arn:aws:iam::992382810653:role/service-role/Translatedoc",
#    RoleSessionName="my-session"
#)
#print( "role asssumption done :::::::::::::::")
#credentials = response['Credentials']

# Use these credentials to create the Translate client
#translate_client = boto3.client('translate', region_name=S3_REGION, **credentials)


translate_client = boto3.client('translate', region_name=S3_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def upload_to_s3(file, file_key, folder = 'docx'):
    s3 = boto3.client('s3', region_name=S3_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    try:
        s3.upload_fileobj(file, INPUT_S3_BUCKET_NAME,f"{folder}/{file_key}")
        return True
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="S3 credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def download_from_s3(file_key, folder='docx'):
    s3 = boto3.client('s3', region_name=S3_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    try:
        response = s3.get_object(Bucket=OUTPUT_S3_BUCKET_NAME, Key=f"{folder}/{file_key}")
        return StreamingResponse(io.BytesIO(response['Body'].read()), media_type='application/octet-stream')
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="S3 credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_translation_job(folder="docx"):
    # Generate a unique ClientToken
    client_token = str(uuid.uuid4())

    # Specify input, output, and job parameters
    input_data_config = {
        'S3Uri': f's3://{INPUT_S3_BUCKET_NAME}/{folder}/',
        'ContentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }

    output_data_config = {
        'S3Uri': f's3://{OUTPUT_S3_BUCKET_NAME}/{folder}/',
        'EncryptionKey': {
            'Type': 'KMS',
            'Id': 'arn:aws:kms:us-east-1:992382810653:key/a787ade0-cfd0-4339-bf41-c8bcbac96db5'
        }
    }

    job_params = {
        'JobName': f'translation-job-{client_token}',
        'InputDataConfig': input_data_config,
        'OutputDataConfig': output_data_config,
        'DataAccessRoleArn': 'arn:aws:iam::992382810653:role/service-role/Translatedoc',
        'SourceLanguageCode': 'en',
        'TargetLanguageCodes': ['fr'],
        'ClientToken': client_token,
    }

    # Start the asynchronous translation job
    response = translate_client.start_text_translation_job(**job_params)

    return response['JobId']

@app.get("/")
async def root():
    return {"status":"ACTIVE"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_key = file.filename
    upload_to_s3(file.file, file_key)
    return {"message": "File uploaded successfully"}

@app.get("/download/{file_key}")
async def download_file(file_key: str):
    return download_from_s3(file_key)

@app.post("/translate/")
async def translate_document():
    job_id = start_translation_job()
    return {"message": f"Translation Job Started. Job ID: {job_id}"}

# Wrap the FastAPI app with Mangum for use with AWS Lambda
handler = Mangum(app)
