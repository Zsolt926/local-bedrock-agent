
import boto3

from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider


# Connect Boto3 to FakeCloud
bedrock_client = boto3.client(
    "bedrock-runtime",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

# Configure Bedrock provider
provider = BedrockProvider(
    bedrock_client=bedrock_client
)

# Select the Bedrock model
model = BedrockConverseModel(
    "anthropic.claude-3-haiku-20240307-v1:0",
    provider=provider,
)

# Create a simple agent
agent = Agent(
    model,
    system_prompt="You are a helpful AI assistant.",
)


if __name__ == "__main__":
    result = agent.run_sync("hello.")

    print(result.output)
