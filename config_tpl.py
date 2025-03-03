# Bedrock Models for Evaluation
MODEL_ID_EVAL="us.anthropic.claude-3-5-haiku-20241022-v1:0"
MODEL_ID_EVAL_COT="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
EMBEDDING_MODEL_ID="amazon.titan-embed-text-v2:0"

# Model parameters
MAX_TOKENS = 2048
TEMPERATURE = 0
TOP_P = 1

# Bedrock Agent details
AGENT_ID=""
AGENT_ALIAS_ID=""

# Trajectories to evaluate, place data file in data_files/ folder
DATA_FILE_PATH="data_files/DATA_FILE_NAME"

# Langfuse Project Setup
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_SECRET_KEY=""
LANGFUSE_HOST=""
