# Having signed up with cloud or LLM API providers such as Open AI,
# you will be issued with credentials. This script allows you to add
# your credentials as shell variables so that they can be accesssed by
# scripts such as golem.
#
# I store this script in my home directory and run it using
# source ~/tokens.sh

# OpenAI - https://openai.com/api/

export OPENAI_API_KEY="PASTE YOUR KEY HERE"

# Azure OpenAI - https://learn.microsoft.com/en-us/training/modules/get-started-openai/

export AZURE_OPENAI_ENDPOINT="https://YOURENDPOINT.openai.azure.com/"
export AZURE_OPENAI_API_KEY="PASTE YOUR KEY HERE"

# Azure AI Model Inference API, see https://learn.microsoft.com/en-us/azure/ai-studio/reference/reference-model-inference-api?tabs=python

export AZUREAI_ENDPOINT_URL="https://YOURENDPOINT.YOURREGION.models.ai.azure.com/" # /chat/completions
export AZUREAI_ENDPOINT_KEY="PASTE YOUR KEY HERE"

# Anthropic

export ANTHROPIC_API_KEY="PASTE YOUR KEY HERE"

# Google

export GOOGLE_CLOUD_PROJECT="YOUR GOOGLE CLOUD PROJECT"
export GOOGLE_APPLICATION_CREDENTIALS="~/.config/gcloud/application_default_credentials.json"

export CLOUDSDK_CORE_PROJECT="YOUR GOOGLE CLOUD PROJECT"
export CLOUDSDK_COMPUTE_REGION="YOUR REGION" # e.g., europe-west2 is London
