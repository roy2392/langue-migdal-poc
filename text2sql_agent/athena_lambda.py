import boto3
import time
import os
import uuid
import json
import sys
from collections import defaultdict

athena_client = boto3.client('athena')


def refineSQL(sql, question):
    raw_schema = get_schema()
    schema = extract_table_columns(raw_schema)
    
    prompt = f"""
    You are an extremely critical SQL query evaluation assistant. Your job is to analyze
    the given schema, SQL query, and question to ensure the query is efficient and accurately answers the 
    question. You should focus on making the query as efficient as possible, using aggregation when applicable.

    Here is the schema you should consider:
    <schema>
    {json.dumps(schema)}
    </schema>
    
    Pay close attention to the accepted values and the column data type located in the comment field for each column.
    
    Here is the generated SQL query to evaluate:
    <sql_query>
    {sql}
    </sql_query>
    
    Here is the question that was asked:
    <question>
    {question}
    </question>
    
    Your task is to evaluate and refine the SQL query to ensure it is very efficient. Follow these steps:
    1. Analyze the query in relation to the schema and the question.
    2. Determine if the query efficiently answers the question.
    3. If the query is not efficient, provide a more efficient SQL query.
    4. If the query is already efficient, respond with "no change needed".

    When evaluating efficiency, consider the following:
    - Use of appropriate aggregation functions (COUNT, SUM, AVG, etc.)
    - Proper use of GROUP BY clauses
    - Avoiding unnecessary JOINs or subqueries
    - Selecting only necessary columns
    - Using appropriate WHERE clauses to filter data
    
    Here are examples to guide your evaluation:
    
    Inefficient query example:
    SELECT chemotherapy, survival_status FROM dev.public.lung_cancer_cases WHERE chemotherapy = 'Yes';

    This is inefficient because it does not provide a concise and informative output that directly answers
    the question. It results in a larger output size, does not aggregate the data, and presents the results
    in a format that is not easy to analyze and interpret.

    Efficient query example:
    SELECT survival_status, COUNT(*) AS count FROM dev.public.lung_cancer_cases WHERE chemotherapy = 'Yes' GROUP BY survival_status;

    This query uses COUNT(*) and GROUP BY to aggregate and count the records for each distinct value of survival_status, providing a more concise and informative result.
    
    Another efficient query example:
    SELECT smoking_status, COUNT(DISTINCT case_id) AS num_patients FROM clinical_genomic WHERE age_at_histological_diagnosis > 50 GROUP BY smoking_status;
    
    This query uses COUNT(DISTINCT) and GROUP BY to aggregate and provide a summary of the data, reducing the SQL output size.
    
    Provide your response within <efficientQuery> tags. If you suggest a new query, do not use line breaks in the generated SQL. Your response should be a single line of SQL or "no change needed" if the original query is already efficient.
    
    Remember to prioritize aggregation when possible to reduce SQL output size and provide more meaningful results.
    """
    client = boto3.client('bedrock-runtime')
    user_message = {"role": "user", "content": prompt}
    claude_response = {"role": "assistant", "content": "<efficientQuery>"}
    model_Id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
    messages = [user_message, claude_response]
    system_prompt = "You are an extremely critical sql query evaluation assistant, your job is to look at the schema, sql query and question being asked to then evaluate the query to ensure it is efficient."
    max_tokens = 1000
    
    body = json.dumps({
        "messages": messages,
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system_prompt
    })
    
    response = client.invoke_model(body=body, modelId=model_Id)
    response_bytes = response.get("body").read()
    response_text = response_bytes.decode('utf-8')
    response_json = json.loads(response_text)
    content = response_json.get('content', [])
    for item in content:
        if item.get('type') == 'text':
            result_text = item.get('text')
            print(result_text)
            return result_text
    
    return "No SQL found in response"
    
def get_schema(database_name="card_games"):
    """
    Get schema information for all tables in Athena databases
    """

    sql = f"""
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = '{database_name}'
        ORDER BY table_name, ordinal_position;
        """
        
    try:
        # Start query execution
        response = athena_client.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={
                'Database': database_name
            }
        )
            
        query_execution_id = response['QueryExecutionId']
            
        def wait_for_query_completion(query_execution_id):
            while True:
                response = athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                state = response['QueryExecution']['Status']['State']
                
                if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                    print(f"Query {state}")
                    return state
                    
                print("Waiting for query to complete...")
                time.sleep(2)
            
        # Wait for query completion
        state = wait_for_query_completion(query_execution_id)

        if state == 'SUCCEEDED':
            # Get query results
            results = athena_client.get_query_results(
                QueryExecutionId=query_execution_id
            )

            # Assuming you have a database connection and cursor setup
            # cursor.execute(sql)
            # results = cursor.fetchall()
            
            database_structure = {database_name: {}}
            
            # Skip the header row
            rows = results['ResultSet']['Rows'][1:]
            
            for row in rows:
                # Extract values from the Data structure
                table_name = row['Data'][0]['VarCharValue']
                column_name = row['Data'][1]['VarCharValue']
                data_type = row['Data'][2]['VarCharValue']
                
                # Initialize table if not exists
                if table_name not in database_structure[database_name]:
                    database_structure[database_name][table_name] = []
                
                # Append column information
                database_structure[database_name][table_name].append((column_name, data_type))

        else:
            raise Exception(f"Query failed with state: {state}")
    except Exception as e:
            print(f"Error getting schema: {e}")
            raise

def query_athena(query, database_name='card_games'):
    """
    Execute a query on Athena
    """
    try:
        # Start query execution
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': database_name
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        
        def wait_for_query_completion(query_execution_id):
            while True:
                response = athena_client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )
                state = response['QueryExecution']['Status']['State']
                
                if state == 'FAILED':
                    error_message = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                    raise Exception(f"Query failed: {error_message}")
                    
                if state == 'CANCELLED':
                    raise Exception("Query was cancelled")
                    
                if state == 'SUCCEEDED':
                    return state
                    
                print("Waiting for query to complete...")
                time.sleep(2)
        
        # Wait for query completion
        state = wait_for_query_completion(query_execution_id)
        
        # Get query results

        if state == 'SUCCEEDED':
            results = athena_client.get_query_results(
                QueryExecutionId=query_execution_id
            )
        
            # Process results
            processed_results = []
            headers = []
            
            # Get headers from first row
            if results['ResultSet']['Rows']:
                headers = [field.get('VarCharValue', '') for field in results['ResultSet']['Rows'][0]['Data']]
            
            # Process data rows
            for row in results['ResultSet']['Rows'][1:]:
                values = [field.get('VarCharValue', '') for field in row['Data']]
                row_dict = dict(zip(headers, values))
                processed_results.append(row_dict)
            
            return processed_results
            # return {
            #     'QueryExecutionId': query_execution_id,
            #     'ResultCount': len(processed_results),
            #     'Headers': headers,
            #     'Results': processed_results
            # }
        else:
            raise Exception(f"Query failed with state: {state}")
        
    except Exception as e:
        print(f"Error executing query: {e}")
        raise


# def upload_result_s3(result, bucket, key):
#     s3 = boto3.resource('s3')
#     s3object = s3.Object(bucket, key)
#     s3object.put(Body=(bytes(json.dumps(result).encode('UTF-8'))))
#     return s3object

def lambda_handler(event, context):
    result = None
    error_message = None

    try:
        if event['apiPath'] == "/getschema":
            result = get_schema()

        # elif event['apiPath'] == "/refinesql":
        #     params =event['parameters']
        #     for param in params:
        #         if param.get("name") == "sql":
        #             sql = param.get("value")
        #             print(sql)
        #         if param.get("name") == "question":
        #             question = param.get("value")
        #             print(question)
            
            # Don't use 
            # result = refineSQL(sql, question)
        
        elif event['apiPath'] == "/queryathena":
            params =event['parameters']
            for param in params:
                if param.get("name") == "query":
                    query = param.get("value")
                    print(query)
                
            result = query_athena(query)

        else:
            raise ValueError(f"Unknown apiPath: {event['apiPath']}")

        if result:
            print("Query Result:", result)
    
    except Exception as e:
        error_message = str(e)
        print(f"Error occurred: {error_message}")

    # BUCKET_NAME = os.environ['BUCKET_NAME']
    # KEY = str(uuid.uuid4()) + '.json'
    # size = sys.getsizeof(str(result)) if result else 0
    # print(f"Response size: {size} bytes")
    
    # if size > 20000:
    #     print('Size greater than 20KB, writing to a file in S3')
    #     result = upload_result_s3(result, BUCKET_NAME, KEY)
    #     response_body = {
    #         'application/json': {
    #             'body': f"Result uploaded to S3. Bucket: {BUCKET_NAME}, Key: {KEY}"
    #         }
    #     }
    # else:
    response_body = {
        'application/json': {
            'body': str(result) if result else error_message
        }
    }

    action_response = {
        'actionGroup': event['actionGroup'],
        'apiPath': event['apiPath'],
        'httpMethod': event['httpMethod'],
        'httpStatusCode': 200 if result else 500,
        'responseBody': response_body
    }

    # session_attributes = event['sessionAttributes']
    # prompt_session_attributes = event['promptSessionAttributes']
    
    api_response = {
        'messageVersion': '1.0', 
        'response': action_response,
        # 'sessionAttributes': session_attributes,
        # 'promptSessionAttributes': prompt_session_attributes
    }
        
    return api_response