from langchain_core.runnables import RunnableLambda
from langchain_core.pydantic_v1 import BaseModel
from langchain.output_parsers.openai_tools import PydanticToolsParser
from langchain.prompts import PromptTemplate

## Data model
class code(BaseModel):
    """Code output"""
    prefix: str = Field(description="Description of the problem and approach")
    imports: str = Field(description="Code block import statements")
    code: str = Field(description="Code block not including import statements")

## LLM
model = ChatOpenAI(temperature=0, model="gpt-4-0125-preview", streaming=True)

# Tool
code_tool_oai = convert_to_openai_tool(code)

# LLM with tool and enforce invocation
llm_with_tool = model.bind(
    tools=[convert_to_openai_tool(code_tool_oai)],
    tool_choice={"type": "function", "function": {"name": "code"}},
)

# Parser
parser_tool = PydanticToolsParser(tools=[code])

# Create a prompt template with format instructions and the query
prompt = PromptTemplate(
    template = """You are a coding assistant with expertise in LCEL, LangChain expression language. \n 
        Here is a full set of LCEL documentation: 
        \n ------- \n
        {context} 
        \n ------- \n
        Answer the user question based on the above provided documentation. \n
        Ensure any code you provide can be executed with all required imports and variables defined. \n
        Structure your answer with a description of the code solution. \n
        Then list the imports. And finally list the functioning code block. \n
        Here is the user question: \n --- --- --- \n {question}""",
    input_variables=["question","context"])

def parse_answer_to_dict(x):
    return x[0].dict()

chain_base_case = (
    {
        "context": lambda x: concatenated_content,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm_with_tool
    | parser_tool
    | RunnableLambda(parse_answer_to_dict)
)