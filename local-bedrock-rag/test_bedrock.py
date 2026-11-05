import boto3
import json

client = boto3.client(
    "bedrock-runtime",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

response = client.converse(
    modelId="anthropic.claude-3-haiku-20240307-v1:0",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": "Explain how RAG works in three sentences."
                }
            ],
        }
    ],
    inferenceConfig={
        "maxTokens": 128,
        "temperature": 0.2,
    },
)

print(json.dumps(response, indent=2, default=str))

print("\nMODEL RESPONSE:")
print(response["output"]["message"]["content"][0]["text"])