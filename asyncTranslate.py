from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import boto3
import uuid
import io
from botocore.exceptions import NoCredentialsError
from mangum import Mangum
from botocore.config import Config
app = FastAPI()

# AWS S3 Configuration
INPUT_S3_BUCKET_NAME = 'demodocumentinput'
OUTPUT_S3_BUCKET_NAME = 'newdocoutput'
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

RoleArn = "arn:aws:iam::992382810653:role/service-role/Translatedoc"
RoleId = "992382810653"

path = f"{RoleId}-TranslateText-"

config = Config(signature_version='s3v4')
translate_client = boto3.client('translate', region_name=S3_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def upload_to_s3(client_id, file, file_key, folder = 'docx'):
    s3 = boto3.client('s3', region_name=S3_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY,config=config)
    file_key = file_key.replace(" ","_")

    
    # Create a new folder by adding a dummy object with a trailing slash
    folder_key = f"{folder}/{path}{client_id}/{file_key}"
    
    try:
        s3.upload_fileobj(file, INPUT_S3_BUCKET_NAME,folder_key)
        return True
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="S3 credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def download_from_s3(job_id,file_key, folder='docx',lang_to = "fr"):
    s3 = boto3.client('s3', region_name=S3_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY,config=config)

    try:
        key = f"{folder}/{path}{job_id}/{lang_to}.{file_key}.{folder}"
        print(key)
        response = s3.get_object(Bucket=OUTPUT_S3_BUCKET_NAME, Key= key)

        file_content = response['Body'].read()
        return StreamingResponse(io.BytesIO(file_content), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename={file_key}"})
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="S3 credentials not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_translation_job(client_id="",folder="docx",lang_from = "en",lang_to = "fr"):
    # Specify input, output, and job parameters
    input_data_config = {
        'S3Uri': f's3://{INPUT_S3_BUCKET_NAME}/{folder}/{path}{client_id}',
        'ContentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    print(input_data_config['S3Uri'])
    output_data_config = {
        'S3Uri': f's3://{OUTPUT_S3_BUCKET_NAME}/{folder}',
    }

    job_params = {
        'JobName': f'translation-job-{client_id}',
        'InputDataConfig': input_data_config,
        'OutputDataConfig': output_data_config,
        'DataAccessRoleArn': RoleArn,
        'SourceLanguageCode': lang_from,
        'TargetLanguageCodes': [lang_to],
        'ClientToken': client_id,
    }

    # Start the asynchronous translation job
    response = translate_client.start_text_translation_job(**job_params)
    return response['JobId']

@app.get("/")
async def root():
    return {"status":"ACTIVE"}

@app.post("/upload/{client_id}/{file_type}")
async def upload_file(client_id: str,file_type: str,file: UploadFile = File(...)):
    file_key = file.filename
    upload_to_s3(client_id,file.file, file_key, folder =file_type)
    return {"message": "File uploaded successfully"}

@app.get("/download/{job_id}/{folder}/{file_key}/{lang_from}/{lang_to}")
async def download_file(job_id: str,folder: str, file_key: str,lang_from: str,lang_to: str):
    return download_from_s3(job_id,file_key,folder,lang_to)

@app.post("/translate/{client_id}/{file_type}/{lang_from}/{lang_to}")
async def translate_document(client_id: str,file_type: str,lang_from: str,lang_to: str):
    job_id = start_translation_job(client_id,file_type,lang_from,lang_to)
    return {"message": f"Translation Job Started. Job ID: {job_id}", "job_id": job_id}

# Wrap the FastAPI app with Mangum for use with AWS Lambda
handler = Mangum(app)
