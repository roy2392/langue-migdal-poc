import os
import uuid
import boto3
import sys
import json
from typing import Dict, Any, List
from rag_evaluator import RAGEvaluator
from text2sql_evaluator import Text2SQLEvaluator
from custom_evaluator import CustomEvaluator
from botocore.client import Config
from agent_info_extractor import AgentInfoExtractor
import time
import requests
import base64

#import necessary user-defined configs
from config import (
    #AGENT SETUP
    AGENT_ID, 
    AGENT_ALIAS_ID, 

    #LANGFUSE SETUP
    LANGFUSE_PUBLIC_KEY, 
    LANGFUSE_SECRET_KEY, 
    LANGFUSE_HOST,
    
    #MODEL HYPERPARAMETERS
    MAX_TOKENS, 
    TEMPERATURE, 
    TOP_P, 

    #EVALUATION MODELS
    MODEL_ID_EVAL,
    EMBEDDING_MODEL_ID,
    MODEL_ID_EVAL_COT
)

# def process_model_definitions(agent_model_id):

#     # Create base64 encoded auth string
#     BASE_URL = "https://us.cloud.langfuse.com/api/public"
    
#     auth_str = f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}"
#     base64_auth = base64.b64encode(auth_str.encode('ascii')).decode('ascii')
    
#     # Headers
#     headers = {
#         "Authorization": f"Basic {base64_auth}",
#         "Content-Type": "application/json"
#     }
    
#     # Make request
#     response = requests.get(
#         f"{BASE_URL}/models",
#         headers=headers
#     )
    
#     #iterate through model name and match
#     json_data = response.json()

#     print(json_data)
    
#     models = [item['modelName'] for item in json_data['data']]

#     create_definition = True
#     for model in models:
#         print("Model in LangFuse: {}".format(model))
#         if agent_model_id.startswith(model):
#             print("Not creating model definition")
#             create_definition = False

    
#     if create_definition:

#         print("Creating model definition")
#         response = requests.post(
#             f"{BASE_URL}/models",
#             headers = headers,
#             json =
#                 {
#                     "modelName": agent_model_id,
#                     "matchPattern": "^(us\.)?amazon\.nova-pro-v1:0$",
#                     "unit": "TOKENS",
#                     "inputPrice": 0.0000008,
#                     "outputPrice": 0.0000032,
#                 }
#         )

#         # Make second request to get all models
#         response = requests.get(
#             f"{BASE_URL}/models",
#             headers=headers
#         )
        
#         json_data = response.json()

#         print("Models second request: {}".format([item['modelName'] for item in json_data['data']]))
#         # print("Post response: {}".format(response))

 

def setup_environment() -> None:
    """Setup environment variables for Langfuse"""
    langfuse_vars = {
        "LANGFUSE_PUBLIC_KEY": LANGFUSE_PUBLIC_KEY,
        "LANGFUSE_SECRET_KEY": LANGFUSE_SECRET_KEY,
        "LANGFUSE_HOST": LANGFUSE_HOST
    }
    for key, value in langfuse_vars.items():
        os.environ[key] = value

def get_config() -> Dict[str, Any]:
    """Get configuration settings"""

    # Create shared clients
    bedrock_config = Config(
        connect_timeout=120, 
        read_timeout=120, 
        retries={'max_attempts': 0}
    )

    shared_clients = {
        'bedrock_agent_client': boto3.client('bedrock-agent'),
        'bedrock_agent_runtime': boto3.client(
            'bedrock-agent-runtime',
            config=bedrock_config
        ),
        'bedrock_runtime': boto3.client('bedrock-runtime')
    }

    return {
        'AGENT_ID': AGENT_ID,
        'AGENT_ALIAS_ID': AGENT_ALIAS_ID,
        'MODEL_ID_EVAL': MODEL_ID_EVAL,
        'EMBEDDING_MODEL_ID': EMBEDDING_MODEL_ID,
        'TEMPERATURE': TEMPERATURE,
        'MAX_TOKENS': MAX_TOKENS,
        'MODEL_ID_EVAL_COT': MODEL_ID_EVAL_COT,
        'TOP_P': TOP_P,
        'ENABLE_TRACE': True,
        'clients': shared_clients
    }


def create_evaluator(eval_type: str, config: Dict[str, Any], 
                    agent_info: Dict[str, Any], data: Dict[str, Any], trace_id: str, 
                    session_id: str) -> Any:
    """Create appropriate evaluator based on evaluation type"""
    evaluator_map = {
        'RAG': RAGEvaluator,
        'TEXT2SQL': Text2SQLEvaluator,
        'COT': CustomEvaluator
        # Add other evaluator types here
    }
    
    evaluator_class = evaluator_map.get(eval_type)
    if not evaluator_class:
        raise ValueError(f"Unknown evaluation type: {eval_type}")
        
    return evaluator_class(
        config=config,
        agent_info=agent_info,
        eval_type=eval_type,
        question=data['question'],
        ground_truth=data['ground_truth'],
        trace_id=trace_id,
        session_id=session_id,
        question_id=data['question_id']
    )

       

def run_evaluation(data_file: str) -> None:
    """Main evaluation function"""
    # Setup
    setup_environment()
    config = get_config()
    
    # Initialize clients and extractors
    extractor = AgentInfoExtractor(config['clients']['bedrock_agent_client'])
    agent_info = extractor.extract_agent_info(AGENT_ID, AGENT_ALIAS_ID)
    
    # Extract agent model from agent info
    # agent_model = agent_info['agentModel']

    # Check if model definition exists in LangFuse and create if needed
    #TODO: Ask Hasan if this is necessary
    # process_model_definitions(agent_model)
    
    # Create session ID
    session_id = str(uuid.uuid4())
    os.environ["SESSION_ID"] = session_id
    print(f"Run ID for evaluation run: {session_id}")

    # Load and process data
    with open(data_file, 'r') as f:
        data_dict = json.load(f)
        
        for eval_type, questions in data_dict.items():
            print(f"Running {eval_type} evaluation")
            
            for question_data in questions:
                trace_id = str(uuid.uuid1())

                question_id = question_data['question_id']
                print(f"Question: {question_id}")
                
                try:
                    evaluator = create_evaluator(
                        eval_type=eval_type,
                        config=config,
                        agent_info=agent_info,
                        data=question_data,
                        trace_id=trace_id,
                        session_id=session_id
                    )
                     
                    results = evaluator.run_evaluation()
                    if results is None:
                        print(f"Skipping question {question_id} due to evaluation failure")
                        time.sleep(60)
                        continue
                        
                    print(f"Successfully evaluated question {question_id}")
                    # print(results)
                    time.sleep(60)
                    
                except Exception as e:
                    print(f"Failed to evalute for question {question_id}: {str(e)}")
                    #if not a bedrock error, continue to next question
                    time.sleep(60)
                    continue
                
                # TODO: Implement langfuse.flush() functionality
                except KeyboardInterrupt:
                    sys.exit(0)
                
# Driver
if __name__ == "__main__":
    #Name of the data file
    run_evaluation('data_files/official_demo_data_file.json')