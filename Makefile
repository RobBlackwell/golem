GOLEM=./golem.py

all : clean install test

test: math models logprobs temperature repeat system

math :
	$(GOLEM) --provider openai "What is 1 + 2? Only give the final answer" | jq -r .answer | grep -q 3
	$(GOLEM) --provider azureai "What is 2 + 2? Only give the final answer" | jq -r .answer | grep -q 4
	$(GOLEM) --provider azure "What is 3 + 2? Only give the final answer" | jq -r .answer | grep -q 5
	$(GOLEM) --provider ollama "What is 4 + 2? Only give the final answer" | jq -r .answer | grep -q 6
	$(GOLEM) --provider anthropic --max_tokens 200  "What is 5 + 2? Only give the final answer" | jq -r .answer | grep -q 7
	$(GOLEM) --provider google "What is 6 + 2? Only give the final answer" | jq -r .answer | grep -q 8

models:
	$(GOLEM) --provider openai --max_tokens 10 "Why is the sky blue" | jq .model | grep -q "gpt-4o-2024-05-13"
	$(GOLEM) --provider ollama --max_tokens 10 "Why is the sky blue" | jq .model | grep -q "llama3"
	$(GOLEM) --provider azure --max_tokens 10 "Why is the sky blue" | jq .model | grep -q "gpt-4o-2024-05-13"
	$(GOLEM) --provider anthropic --max_tokens 10 "Why is the sky blue" | jq .model | grep -q "claude-3-5-sonnet-20240620"
	$(GOLEM) --provider google --max_tokens 10 "Why is the sky blue" | jq .model | grep -q "gemini-1.5-flash-001"
	$(GOLEM) --provider azure --model gpt-4o-mini-2024-07-18 --url "$$AZURE_OPENAI_ENDPOINT_1" --key "$$AZURE_OPENAI_API_KEY_1" --max_tokens 10 "Why is the sky blue" | jq .model | grep -q gpt-4o-mini
	$(GOLEM) --provider azure --model gpt-4o-2024-05-13 --url "$$AZURE_OPENAI_ENDPOINT_1" --key "$$AZURE_OPENAI_API_KEY_1" --max_tokens 10 "Why is the sky blue" | jq .model | grep -q gpt-4o-2024-05-13
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --max_tokens 10 "Why is the sky blue" | jq .model | grep -q gpt-35-turbo
	$(GOLEM) --provider azure --model gpt-4-turbo-2024-04-09 --url "$$AZURE_OPENAI_ENDPOINT_3" --key "$$AZURE_OPENAI_API_KEY_3" --max_tokens 10 "Why is the sky blue" | jq .model | grep -q gpt-4-turbo-2024-04-09
	$(GOLEM) --provider openai --model gpt-4o-2024-05-13 --max_tokens 10 "Why is the sky blue" --key "$$OPENAI_API_KEY"| jq .model | grep -q "gpt-4o-2024-05-13"

logprobs:
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --logprobs true --top_logprobs 3 "Why is the sky blue" | jq '.response.choices[].logprobs.content[].logprob' > /dev/null

temperature:
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --temperature 0.5 "Why is the sky blue" | jq .temperature | grep -q 0.5
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --temperature "0.5,0.6" "Why is the sky blue" | jq .temperature | tail -n 1 | grep -q 0.6
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --temperature "0.5:1.0:0.2" "Why is the sky blue" | jq .temperature | tail -n 1 | grep -q 0.9


top_p:
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --top_p 0.5 "Why is the sky blue" | jq .top_p | grep -q 0.5
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --top_p "0.5,0.6" "Why is the sky blue" | jq .top_p | tail -n 1 | grep -q 0.6
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --top_p "0.5:1.0:0.2" "Why is the sky blue" | jq .top_p | tail -n 1 | grep -q 0.9

repeat:
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --repeat "a" "Why is the sky blue" | jq .repeat | grep -q "a"
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --repeat 1 "Why is the sky blue" | jq .repeat | grep -q 1
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --repeat "1,2" "Why is the sky blue" | jq .repeat | tail -n 1 | grep -q 2
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --repeat "3:5:1" "Why is the sky blue" | jq .repeat | tail -n 1 | grep -q 4

system:
	$(GOLEM) --provider azure --model gpt-35-turbo-0125 --url "$$AZURE_OPENAI_ENDPOINT_2" --key "$$AZURE_OPENAI_API_KEY_2" --skip 1 --repeat "1,2" --system-prompt example/standard/system-prompt.txt -f example/standard/prompts.jsonl | wc -l | grep -q 9

pylint:
	pylint -d duplicate-code $$(git ls-files '*.py')
install:
	bin/install.sh

clean:
	rm -rf venv
