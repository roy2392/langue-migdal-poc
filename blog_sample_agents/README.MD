# Deploying Sample Agents for Evaluation

You can choose one or both RAG and Text2SQL sample agent to try out evaluations

## Deployment Steps

1. Set up a Langfuse project using either the cloud version www.langfuse.com or the AWS self-hosted option https://github.com/aws-samples/deploy-langfuse-on-ecs-with-fargate/tree/main/langfuse-v3

2. Create a SageMaker notebook instance in your AWS account

3. Open a terminal and navigate to the SageMaker/ folder within the instance
```bash
cd SageMaker/
```

4. Clone this repository
```bash
git clone https://github.com/aws-samples/amazon-bedrock-agent-evaluation-framework
```

5. Navigate to the repository and install the necessary requirements
```bash
cd amazon-bedrock-agent-evaluation-framework/
pip3 install -r requirements.txt
```

6. Go to the blog_sample_agents/ folder and navigate to 0-Notebook-environment/setup-environment.ipynb to set up your Jupyter environment

7. Choose the conda_python3 kernel for the SageMaker notebook

8. Follow the respective agent notebooks to deploy each agent and evaluate it against a benchmark dataset!


## RAG / Text2SQL Agent setup

1. Run through the RAG/Text2SQL notebook to create the agents in your AWS account
(WARNING: DUE TO NATURE OF SQL QUERIES OPTIMIZED FOR DIFFERENT DATABASE ENGINES, SOME MORE COMPLEX TEXT2SQL SAMPLE QUESTIONS MAY EITHER NOT WORK OR HAVE A LOW EVALUATION SCORE)
2. Modify the configuration file with the appropriate information about your agent, and evaluation models, etc (This information will also be given at the end of each notebook)
3. Run the driver.py script to run evaluations.
4. Check the langfuse console for traces and evaluation metrics (Refer to the 'Navigating the Langfuse Console' section in the root readme)


FOR RUNNING EVALUTION: MAYBE HAVE A SINGLE DATASET FILE THAT WILL RUN UNLESS OVERRIDDEN. THE DATAFILE TO RUN WILL BE SPECIFIED IN THE CONFIGURATION FILE. FOR THIS SAMPLE AGENTS, THE DEFAULT IS A GIVEN SAMPLE DATAFILE (THE USER WILL NEED TO REPLACE WITH THE GIVEN SAMPLE), OR IF THEY WANT TO CREATE THEIR OWN, RUNNING EACH DATA GENERATION FOR EACH TYPE OF AGENT WILL WRITE TO A NEW FILE OR TO THE EXISTING SAMPLE DATAFILE (FOR GENERATING DATASET, CHECK IF EACH TAG EXISTS FOR THAT SPECIFIC TOOL, AND IF IT EXISTS, EMPTY IT AND WRITE IT IN THERE, AND IF NOT JUST CREATE A NEW ONE)


