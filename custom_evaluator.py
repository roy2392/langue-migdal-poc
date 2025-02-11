from typing import Dict, Any, List, Tuple
import time
from datetime import datetime
from ragas import evaluate
from base_evaluator import ToolEvaluator

class CustomEvaluator(ToolEvaluator):
    def __init__(self, **kwargs):
        """
        Initialize Custom Evaluator with all necessary components
        
        Args:
            **kwargs: Arguments passed to parent class
        """
        super().__init__(**kwargs)

    def _initialize_clients(self) -> None:
        """Initialize evaluation-specific models using shared clients"""
        # Use shared clients
        self.bedrock_agent_client = self.clients['bedrock_agent_client']
        self.bedrock_agent_runtime_client = self.clients['bedrock_agent_runtime']
        self.bedrock_client = self.clients['bedrock_runtime']

    def evaluate_response(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the RAG response using specified metrics
        
        Args:
            metadata (Dict[str, Any]): Evaluation metadata
            
        Returns:
            Dict containing evaluation results
        """

        return {"metric_scores": {}}

    def invoke_agent(self, tries: int = 1) -> Tuple[Dict[str, Any], datetime]:
        """
        Invoke the Custom tool and process its response with retry logic
        
        Args:
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
                sessionId=self.trace_id,
                enableTrace=self.config['ENABLE_TRACE']
            )

            # Process response
            agent_answer = None
            input_tokens = output_tokens = 0
            orc_trace_full = []
            full_trace = []
            
            for event in raw_response['completion']:
                if 'chunk' in event:
                    agent_answer = event['chunk']['bytes'].decode('utf-8')
                    
                elif "trace" in event:

                    full_trace.append(event['trace'])
                    
                    trace_obj = event['trace']['trace']
                    

                    if "orchestrationTrace" in trace_obj:
                        orc_trace = trace_obj['orchestrationTrace']
                        # Add trace to full_trace object
                        orc_trace_full.append(orc_trace)

                    # Extract token usage
                    if 'modelInvocationOutput' in orc_trace:
                        usage = orc_trace['modelInvocationOutput']['metadata']['usage']
                        input_tokens += usage['inputTokens']
                        output_tokens += usage['outputTokens']

            processed_response = {
                'agent_generation_metadata': {'ResponseMetadata': raw_response.get('ResponseMetadata', {})},
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
