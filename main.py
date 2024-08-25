import json
import csv
from google.cloud import storage
import pymysql
import os
from flask import jsonify

# Configuration
PROJECT_ID = 'data-on-cloud-431403'
HOST = '34.171.167.187'
DB_USER = 'root'
DB_PASSWORD = 'password'
DB_NAME = 'employeedb'
GCS_BUCKET_NAME = 'first_data_bkt'
GCS_JSON_FILE_NAME = 'data.json'
GCS_CSV_FILE_NAME = 'data.csv'
GCS_OUTPUT_JSON_FILE_NAME = 'output_data1.json'

# Initialize GCS client
storage_client = storage.Client()

def read_from_gcs(bucket_name, file_name):
    """Reads a file from GCS."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    content = blob.download_as_text()
    return content

def read_from_sql():
    """Reads data from Cloud SQL."""
    connection = pymysql.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=HOST
    )

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM employees")
        rows = cursor.fetchall()

    connection.close()
    return rows

def transform_to_json(sql_data, json_data, csv_data):
    """Transforms SQL, JSON, and CSV data into a single JSON object."""
    combined_data = {
        'sql_data': sql_data,
        'json_data': json.loads(json_data),
        'csv_data': list(csv.DictReader(csv_data.splitlines()))
    }
    return combined_data

def upload_to_gcs(bucket_name, file_name, data):
    """Uploads a file to GCS."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')

def etl_pipeline(request):
    """HTTP Cloud Function to execute the ETL pipeline."""
    try:
        print(f"Attempting to download {GCS_JSON_FILE_NAME} from bucket {GCS_BUCKET_NAME}")

        # Read data from GCS (JSON and CSV)
        json_data = read_from_gcs(GCS_BUCKET_NAME, GCS_JSON_FILE_NAME)
        csv_data = read_from_gcs(GCS_BUCKET_NAME, GCS_CSV_FILE_NAME)

        # Read data from Cloud SQL
        sql_data = read_from_sql()
        print(sql_data)

        # Transform data
        transformed_data = transform_to_json(sql_data, json_data, csv_data)

        # Upload transformed data to GCS
        upload_to_gcs(GCS_BUCKET_NAME, GCS_OUTPUT_JSON_FILE_NAME, transformed_data)

        return jsonify({"status": "success", "message": "Data pipeline executed successfully."}), 200
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
