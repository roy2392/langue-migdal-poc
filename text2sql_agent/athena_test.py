import boto3
import time
import os
import uuid
import json
import sys
from collections import defaultdict

# Initialize client
athena_client = boto3.client('athena')

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

            # print("Legit results: {}".format(results))
        
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



query = "SELECT T1.id, T2.text, T1.hasContentWarning FROM cards AS T1 INNER JOIN rulings AS T2 ON T1.uuid = T2.uuid WHERE T1.artist = 'Stephen Daniele' LIMIT 5"
results = query_athena(query)
# print(results)