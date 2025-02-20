# Deploying Sample Agents for Evaluation

You can choose one or both RAG and Text2SQL sample agent to try out evaluations

## RAG / Text2SQL Agent setup

1. Run through the RAG/Text2SQL notebook to create the agents in your AWS account
2. For each agent type, either use the provided evaluation dataset or run the data generator to create a set of sample datafiles for other questions (WARNING: DUE TO NATURE OF SQL QUERIES OPTIMIZED FOR DIFFERENT DATABASE ENGINES, SOME MORE COMPLEX TEXT2SQL SAMPLE QUESTIONS MAY EITHER NOT WORK OR HAVE A LOW EVALUATION SCORE)
3. Either deploy the langfuse on your AWS with the self-hosted option (Link to repo) or set up a project in the cloud langfuse
4. Modify the configuration file with the appropriate information about your agent, and evaluation models, etc
5. Run the evalution script
6. Check the langfuse console for traces and evaluation metrics (Refer to the Navigating the Langfuse Console section in the root readme)


FOR RUNNING EVALUTION: MAYBE HAVE A SINGLE DATASET FILE THAT WILL RUN UNLESS OVERRIDDEN. THE DATAFILE TO RUN WILL BE SPECIFIED IN THE CONFIGURATION FILE. FOR THIS SAMPLE AGENTS, THE DEFAULT IS A GIVEN SAMPLE DATAFILE (THE USER WILL NEED TO REPLACE WITH THE GIVEN SAMPLE), OR IF THEY WANT TO CREATE THEIR OWN, RUNNING EACH DATA GENERATION FOR EACH TYPE OF AGENT WILL WRITE TO A NEW FILE OR TO THE EXISTING SAMPLE DATAFILE (FOR GENERATING DATASET, CHECK IF EACH TAG EXISTS FOR THAT SPECIFIC TOOL, AND IF IT EXISTS, EMPTY IT AND WRITE IT IN THERE, AND IF NOT JUST CREATE A NEW ONE)


