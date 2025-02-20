# Amazon Bedrock Agent Evaluation

Bedrock Agent Evaluation is an evlauation framework for Amazon Bedrock agent tool-use and chain-of-thought reasoning.

## Features

- Test your own Bedrock Agent with custom questions
- Includes built-in evaluation for RAG, Text2SQL, and Chain-of-Thought
- Extend the capabilities to include custom tool evaluations
- Integrated with LangFuse for easy observability of evaluation results

(Include a demo video here)

Screenshots / Code block to include:
1. Driver code snippet?
2. Run_Evaluation function code snippet?
3. Evaluator tool function code snippet?
4. Screenshots of langfuse dashboard
5. Screenshot of langfuse trace and evaluation metrics


## How to use

### Deployment environment options
1. Clone this repo in a SageMaker notebook (Link to how to do it)
2. Clone this repo locally and set up AWS CLI credentials to your AWS account (Link to how to do it)

### Pre-req

### Option 1: Bring your own agent to evaluate
1. Bring your existing agent (Currently RAG and Text2SQL evaluations built-in)
2. Use the provided dataset or create a dataset file for evaluations (Manually or using the generator)
3. Deploy the langfuse on AWS for self-hosted option (Follow this repo: Link to repo) or use the cloud version of langfuse (Link to langfuse)
3. Fill out the configuration file
4. Run the evaluation job

### Option 2: Create Sample Agents to run Evaluations
1. Deploy the sample agents for RAG and Text2SQL use cases in the sample_agents folder
2. Use the provided dataset or create the dataset file for evaluation using the data generator script
3. Deploy the langfuse on AWS for self-hosted option (Follow this repo: Link to repo) or use the cloud version of langfuse (Link to langfuse)
3. Fill out the configuration file
4. Run the evaluation job


## Navigating the Langfuse Traces and Dashboard

1. How each traces are structured and sent
2. What are included in each hierarchy level of trace / generation / span
3. What tags we are including and how to filter
4. How to use the dashboard
5. How to compare evaluation scores
6. How to compare model latency


## Documentation

Version 1:
What to include in documentation:
1. How the framework is structured (Each component/file of the framework): Driver, evaluators, setting up langfuse, custom evaluators
2. How evaluations are implemented and the workflow 
3. How to add custom evaluators
4. How to modify langfuse traces
5. How to modify evaluation logic for existing evaluations


Future iteration plan:
1. Change the framework to a more trajectory based rather than per question
2. Use Opentelemetry collectors for more accurate tracing
3. Abstract out the logic for trace parsing for bedrock calls
4. Make it Platform agnostic? (Might have to create multiple versions that needs to be imported for this)
5. Evaluation should be more trajectory and goal fulfillment / tool adherence rather than individual tools, and provide them with built-in metrics that can be chosen for each evaluation rather than evaluations for each tool
6. For langfuse evalutors, integrate more with langfuse capabilities: Dataset to run evaluations on langfuse, human annotation for human in the loop
7. A streamlit UI for online evaluation feature demo


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

