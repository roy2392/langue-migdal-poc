from typing import Dict, Any, List, Tuple
from datetime import datetime
from langchain_aws.chat_models import ChatBedrock
from ragas.llms import LangchainLLMWrapper
import json
import time
from evaluators.cot_evaluator import ToolEvaluator

class Text2SQLEvaluator(ToolEvaluator):
    def __init__(self, **kwargs):
        """Initialize Text2SQL Evaluator with all necessary components"""
        super().__init__(**kwargs)

    def _initialize_clients(self) -> None:
        """Initialize evaluation-specific models using shared clients"""
        self.bedrock_agent_runtime_client = self.clients['bedrock_agent_runtime']
        self.bedrock_client = self.clients['bedrock_runtime']
        
        # Initialize evaluation model
        self.bedrock_model = ChatBedrock(
            model_id=self.config['MODEL_ID_EVAL'],
            client=self.bedrock_client
        )
        self.evaluator_llm = LangchainLLMWrapper(self.bedrock_model)

    def evaluate_response(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate Text2SQL response using LLM as judge with two key metrics"""
        try:

            evaluation_prompt = f"""You are an expert evaluator for Text2SQL systems. Evaluate the following response based on two key metrics.

                Question: {metadata['question']}
                Database Schema: {metadata['ground_truth']['ground_truth_sql_context']}

                Ground Truth SQL: {metadata['ground_truth']['ground_truth_sql_query']}
                Generated SQL: {metadata['evaluation_metadata']['agent_query']}

                Ground Truth Answer: {metadata['ground_truth']['ground_truth_answer']}
                Generated Answer: {metadata['agent_response']}

                Query Result: {metadata['ground_truth']['ground_truth_query_result']}

                Evaluate and provide scores (0-1) and explanations for these metrics:

                SQL Semantic Equivalence: Evaluate if the generated SQL would produce the same results as the ground truth SQL.
                Answer Correctness: Check if the generated answer correctly represents the query results and matches ground truth.
                
                Provide your evaluation in this exact JSON format:
                {{
                    "metrics_scores": {{
                        "sql_semantic_equivalence": {{
                            "score": numeric_value,
                            "explanation": "Brief explanation of why this score was given"
                        }},
                        "answer_correctness": {{
                            "score": numeric_value,
                            "explanation": "Brief explanation of why this score was given"
                        }}
                    }}
                }}
            """

            # Call LLM for evaluation, use Claude 3 Sonnet
            response = self.bedrock_client.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "temperature": 0,
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"type": "text", "text": evaluation_prompt}],
                        }
                    ],
                })
            )
            
            # Parse and return the evaluation
            evaluation = json.loads(json.loads(response['body'].read())['content'][0]['text'])
            return evaluation

        except Exception as e:
            raise Exception(f"error: {str(e)}")     
            
    def invoke_agent(self, tries: int = 1) -> Tuple[Dict[str, Any], datetime]:
        """
        Invoke the Text2SQL agent and process its response
        
        Args:
            question (str): Question to process
            trace_id (str): Unique identifier for the trace
            tries (int): Number of retry attempts
            
        Returns:
            Tuple of (processed_response, start_time)
        """
        agent_start_time = datetime.now()
        max_retries = 3
        
        try:
            # Invoke agent
            raw_response = self.bedrock_agent_runtime_client.invoke_agent(
                inputText=self.question,
                agentId=self.config['AGENT_ID'],
                agentAliasId=self.config['AGENT_ALIAS_ID'],
                # Confirm that this works
                sessionId=self.session_id,
                enableTrace=self.config['ENABLE_TRACE']
            )

            # Process response
            agent_query = ""
            agent_answer = None
            end_event_received = False
            input_tokens = 0
            output_tokens = 0
            full_trace = []
            

            for event in raw_response['completion']:
                if 'chunk' in event:
                    data = event['chunk']['bytes']
                    agent_answer = data.decode('utf-8')
                    end_event_received = True
                    
                elif "trace" in event:
                    full_trace.append(event['trace'])
                    trace_obj = event['trace']['trace']
                    if "orchestrationTrace" in trace_obj:
                        orc_trace = trace_obj['orchestrationTrace']
                        
                        # Extract SQL query
                        if 'observation' in orc_trace:
                            invoc_trace = orc_trace['observation']
                            if 'actionGroupInvocationOutput' in invoc_trace:
                                action_trace = invoc_trace['actionGroupInvocationOutput']
                                if 'text' in action_trace:
                                    if "the query i used" in action_trace['text']:
                                        agent_query = action_trace['text'].split("the query i used: ")[1]
                        
                        # Extract token usage if available
                        if 'modelInvocationOutput' in orc_trace:
                            usage = orc_trace['modelInvocationOutput']['metadata']['usage']
                            input_tokens += usage.get('inputTokens',0)
                            output_tokens += usage.get('outputTokens',0)

            if not end_event_received:
                raise Exception("End event not received")

            processed_response = {
                'agent_generation_metadata': {
                    "agent_query": agent_query,
                    'ResponseMetadata': raw_response.get('ResponseMetadata', {})
                },
                'agent_answer': agent_answer, 
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
            
            return full_trace, processed_response, agent_start_time
                
        except Exception as e:
            if (hasattr(e, 'response') and 
                'Error' in e.response and
                e.response['Error'].get('Code') == 'throttlingException' and 
                tries <= max_retries):
                
                wait_time = 30 * tries
                print(f"Throttling occurred. Attempt {tries} of {max_retries}. "
                    f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                return self.invoke_agent(tries + 1)
            else:
                raise e