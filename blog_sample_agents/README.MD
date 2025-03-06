# Deploying Sample Agents for Evaluation

You can choose one or both of the RAG and Text2SQL sample agent to try out evaluations

## Deployment Steps

1. Set up a Langfuse project using either the cloud version www.langfuse.com or the AWS self-hosted option https://github.com/aws-samples/deploy-langfuse-on-ecs-with-fargate/tree/main/langfuse-v3

2. If you are using the self-hosted option and want to see model costs then you must create a model definition in Langfuse for "us.anthropic.claude-3-5-sonnet-20241022-v2:0", instructions can be found here https://langfuse.com/docs/model-usage-and-cost#custom-model-definitions

3. Create a SageMaker notebook instance in your AWS account

4. Open a terminal and navigate to the SageMaker/ folder within the instance
```bash
cd SageMaker/
```

5. Clone this repository
```bash
git clone https://github.com/aws-samples/amazon-bedrock-agent-evaluation-framework
```

6. Navigate to the repository and install the necessary requirements
```bash
cd amazon-bedrock-agent-evaluation-framework/
pip3 install -r requirements.txt
```

7. Go to the blog_sample_agents/ folder and navigate to 0-Notebook-environment/setup-environment.ipynb to set up your Jupyter environment

8. Choose the conda_python3 kernel for the SageMaker notebook

9. Follow the respective agent notebooks to deploy each agent and evaluate it with a benchmark dataset!


## RAG / Text2SQL Agent Setup

1. Run through the RAG/Text2SQL notebook to create the agents in your AWS account
(WARNING: DUE TO NATURE OF SQL QUERIES OPTIMIZED FOR DIFFERENT DATABASE ENGINES, SOME MORE COMPLEX TEXT2SQL SAMPLE QUESTIONS MAY EITHER NOT WORK OR HAVE A LOW EVALUATION SCORE)
2. Check the langfuse console for traces and evaluation metrics (Refer to the 'Navigating the Langfuse Console' section in the root readme)