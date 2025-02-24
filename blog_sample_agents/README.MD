# Deploying Sample Agents for Evaluation

You can choose one or both RAG and Text2SQL sample agent to try out evaluations

## Pre-requisites

1. Make your you hvae installed the required dependencies for the framework from the requirements.txt in the root of the repository
2. Set up a Langfuse project using either the cloud version (Link to langfuse) or AWS self-hosted option (Link to repo for aws self-hosting), and get the required security tokens to connect to the framework
3. Run through the 0-Notebook-environment/setup-environment.ipynb to setup your AWS environment
4. Choose the conda_python3 kernel for the SageMaker notebook

## RAG / Text2SQL Agent setup

1. Run through the RAG/Text2SQL notebook to create the agents in your AWS account
(WARNING: DUE TO NATURE OF SQL QUERIES OPTIMIZED FOR DIFFERENT DATABASE ENGINES, SOME MORE COMPLEX TEXT2SQL SAMPLE QUESTIONS MAY EITHER NOT WORK OR HAVE A LOW EVALUATION SCORE)
2. Modify the configuration file with the appropriate information about your agent, and evaluation models, etc (This information will also be given at the end of each notebook)
3. Run the driver.py script to run evaluations.
4. Check the langfuse console for traces and evaluation metrics (Refer to the 'Navigating the Langfuse Console' section in the root readme)


FOR RUNNING EVALUTION: MAYBE HAVE A SINGLE DATASET FILE THAT WILL RUN UNLESS OVERRIDDEN. THE DATAFILE TO RUN WILL BE SPECIFIED IN THE CONFIGURATION FILE. FOR THIS SAMPLE AGENTS, THE DEFAULT IS A GIVEN SAMPLE DATAFILE (THE USER WILL NEED TO REPLACE WITH THE GIVEN SAMPLE), OR IF THEY WANT TO CREATE THEIR OWN, RUNNING EACH DATA GENERATION FOR EACH TYPE OF AGENT WILL WRITE TO A NEW FILE OR TO THE EXISTING SAMPLE DATAFILE (FOR GENERATING DATASET, CHECK IF EACH TAG EXISTS FOR THAT SPECIFIC TOOL, AND IF IT EXISTS, EMPTY IT AND WRITE IT IN THERE, AND IF NOT JUST CREATE A NEW ONE)


