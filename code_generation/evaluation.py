import uuid
from langsmith import Client
from langchain.smith import RunEvalConfig, run_on_dataset
from langsmith.evaluation import EvaluationResult, run_evaluator
from langsmith.schemas import Example, Run
from typing import Union

@run_evaluator
def check_import(run: Run, example: Union[Example, None] = None):
    model_outputs = run.outputs
    imports = model_outputs['imports']
    try:
        exec(imports)
        score = 1
    except:
        score = 0
    return EvaluationResult(key="check_import", score=score)

@run_evaluator
def check_execution(run: Run, example: Union[Example, None] = None):
    model_outputs = run.outputs
    imports = model_outputs['imports']
    code = model_outputs['code']
    code_to_execute = imports +"\n"+ code
    try:
        exec(code_to_execute)
        score = 1
    except:
        score = 0
    return EvaluationResult(key="check_execution", score=score)

# Config
evaluation_config = RunEvalConfig(
    custom_evaluators = [check_import,check_execution],
)

client = Client()