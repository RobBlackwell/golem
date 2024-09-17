GOLEM = ../../../golem.py
SUMMARY = ../../summarise.py

TEMP := $(shell date +%Y%m%d%H%M%S).jsonl

summary.psv: answers.jsonl
	$(SUMMARY) ../../questions.jsonl answers.jsonl summary.psv

answers.jsonl: ../prompts.jsonl ../system-prompt.txt
	$(GOLEM) --system-prompt ../system-prompt.txt --provider openai --model "gpt-3.5-turbo-0125"  --repeat "0,1,2" --temperature "0.0,0.5,1.0" -f $< > $(TEMP)
	mv $(TEMP) $@

clean:
	rm *.jsonl summary.psv
