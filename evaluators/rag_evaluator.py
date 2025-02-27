from typing import Dict, Any, List, Tuple
import boto3
import time
from botocore.client import Config
from datetime import datetime
from langchain_aws.chat_models.bedrock import ChatBedrock
from langchain_aws.embeddings.bedrock import BedrockEmbeddings
from datasets import Dataset
from ragas import evaluate
from evaluators.base_evaluator import ToolEvaluator
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    answer_similarity
)


class RAGEvaluator(ToolEvaluator):
    def __init__(self, **kwargs):
        """
        Initialize RAG Evaluator with all necessary components
        
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
        
        # Initialize evaluation models
        self.llm_for_evaluation = ChatBedrock(
            model_id=self.config['MODEL_ID_EVAL'],
            max_tokens=100000,
            client=self.bedrock_client  # Use shared client
        )
        
        self.bedrock_embeddings = BedrockEmbeddings(
            model_id=self.config['EMBEDDING_MODEL_ID'],
            client=self.bedrock_client  # Use shared client
        )

    def prepare_evaluation_dataset(self, metadata: Dict[str, Any]) -> Dataset:
        """
        Prepare dataset for RAG evaluation
        
        Args:
            metadata (Dict[str, Any]): Evaluation metadata
            
        Returns:
            Dataset object ready for evaluation
        """
        return Dataset.from_dict({
            "question": [metadata['question']],
            "answer": [metadata['agent_response']],
            "contexts": [metadata['evaluation_metadata']['rag_contexts']],
            "ground_truth": [metadata['ground_truth']]
        })

    def evaluate_response(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the RAG response using specified metrics
        
        Args:
            metadata (Dict[str, Any]): Evaluation metadata
            
        Returns:
            Dict containing evaluation results
        """
        try:
            dataset = self.prepare_evaluation_dataset(metadata)
            evaluation_results = evaluate(
                dataset=dataset,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_recall,
                    answer_similarity
                ],
                llm=self.llm_for_evaluation,
                embeddings=self.bedrock_embeddings
            )
            
            return {
                'metrics_scores': {
                    metric: {'score': score} for metric, score in evaluation_results.scores[0].items()
                }
            }
            
        except Exception as e:
            raise Exception("Error: {}".format(e))


    def invoke_agent(self, tries: int = 1) -> Tuple[Dict[str, Any], datetime]:
        """
        Invoke the RAG tool and process its response with retry logic
        
        Args:
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
                # Test that this works
                sessionId=self.session_id,
                enableTrace=self.config['ENABLE_TRACE']
            )


            # Process response
            rag_contexts = []
            agent_answer = None
            input_tokens = output_tokens = 0
            full_trace = []
            
            for event in raw_response['completion']:
                if 'chunk' in event:
                    agent_answer = event['chunk']['bytes'].decode('utf-8')
                    
                elif "trace" in event:
                    full_trace.append(event['trace'])
                    trace_obj = event['trace']['trace']
                    
                    if "orchestrationTrace" in trace_obj:
                        orc_trace = trace_obj['orchestrationTrace']

                        # Extract context from knowledge base lookup
                        if 'observation' in orc_trace:
                            obs_trace = orc_trace['observation']
                            if 'knowledgeBaseLookupOutput' in obs_trace:
                                output_trace = obs_trace['knowledgeBaseLookupOutput']
                                if 'retrievedReferences' in output_trace:
                                    for ref in output_trace['retrievedReferences']:
                                        rag_contexts.append(ref['content']['text'])
                        
                        # Extract token usage
                        if 'modelInvocationOutput' in orc_trace:
                            usage = orc_trace['modelInvocationOutput']['metadata']['usage']
                            input_tokens += usage['inputTokens']
                            output_tokens += usage['outputTokens']

            processed_response = {
                'agent_generation_metadata': {'ResponseMetadata': raw_response.get('ResponseMetadata', {}), "rag_contexts": rag_contexts},
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
