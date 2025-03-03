# Amazon Bedrock Agent Evaluation

Bedrock Agent Evaluation is an evalauation framework for Amazon Bedrock agent tool-use and chain-of-thought reasoning.

## Features

- Test your own Bedrock Agent with custom questions
- Includes built-in evaluation for RAG, Text2SQL, and Chain-of-Thought
- Extend the capabilities to include custom tool evaluations
- Integrated with LangFuse for easy observability of evaluation results


### Deployment Options
1. Clone this repo to a SageMaker notebook instance
2. Clone this repo locally and set up AWS CLI credentials to your AWS account

### Pre-Requisites
Set up a LangFuse account and create a project using the cloud www.langfuse.com or self-host option for AWS https://github.com/aws-samples/deploy-langfuse-on-ecs-with-fargate/tree/main/langfuse-v3

### SageMaker Notebook Deployment Steps

1. Create a SageMaker notebook instance in your AWS account

2. Open a terminal and navigate to the SageMaker/ folder within the instance
```bash
cd SageMaker/
```

3. Clone this repository
```bash
git clone https://github.com/aws-samples/amazon-bedrock-agent-evaluation-framework
```

4. Navigate to the repository and install the necessary requirements
```bash
cd amazon-bedrock-agent-evaluation-framework/
pip3 install -r requirements.txt
```

### Local Deployment Steps

1. Clone this repository
```bash
git clone https://github.com/aws-samples/amazon-bedrock-agent-evaluation-framework
```

2. Navigate to the repository and install the necessary requirements
```bash
cd amazon-bedrock-agent-evaluation-framework/
pip3 install -r requirements.txt
```

3. Set up AWS CLI to access AWS account resources locally https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html


### Agent Evaluation Options
1. Bring you own agent to evaluate
2. Create sample agents from this repository and run evaluations

### Option 1: Bring your own agent to evaluate
1. Bring your existing agent you want to evaluate (Currently RAG and Text2SQL evaluations built-in)
2. Create a dataset file for evaluations, manually or using the generator (Refer to the data_files/sample_data_file.json for the necessary format)

3. Copy the config_tpl.py into a 'config.py' configuration file and fill in the necessary information
```bash
cp config_tpl.py config.py
```

4. Run driver.py to run the evaluation job
```bash
python3 driver.py
```

5. Check your Langfuse project console to see the evaluation results!

### Option 2: Create Sample Agents to run Evaluations
Follow the instructions in the [Blog Sample Agents README](blog_sample_agents/README.md). This is a guided way to run the evaluation framework on pre-created Bedrock Agents.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.