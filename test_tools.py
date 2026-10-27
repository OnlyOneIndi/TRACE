from pydantic_ai.models.test import TestModel

from agent import agent

with agent.override(model=TestModel()):
    result = agent.run_sync("Calculate 372 multiplied by 48.")

print("\nTEST RESULT:")
print(result.output)