from google.cloud import bigquery
import base64 
import json
from google.oauth2 import service_account
import os
credentials_b64 = os.environ['credentials_b64']

credentials_bytes = base64.b64decode(credentials_b64)
credentials_dict = json.loads(credentials_bytes)
credentials = service_account.Credentials.from_service_account_info(credentials_dict)
def query_to_dataframe(query):
    project_id = 'adept-cosine-420005'
    query=query
    client = bigquery.Client(project=project_id,credentials=credentials)
    try:
        query_job = client.query(query)
        query_job.result()
        df = query_job.to_dataframe()
    except Exception as e:
        return { "response": "error","query":"adi", "error": str(e) }
        # return "a","a",e
    return { "response": "success","query":query, "dataframe": df }