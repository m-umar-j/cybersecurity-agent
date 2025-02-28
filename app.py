from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_mistralai import ChatMistralAI
from typing import Annotated 
from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    MessageLikeRepresentation,
    SystemMessage,
    ToolCall,
    ToolMessage,
)
from langchain_core.runnables import RunnableLambda

from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv
import os
import subprocess
#
from IPython.display import Image, display
#
load_dotenv()
MISTRAL_API_KEY=os.getenv("MISTRAL_API_KEY")

import subprocess
# result = subprocess.check_output(command, shell=True, text=True)
# print(result)
class State(TypedDict):
    messages: Annotated[list, add_messages]
@tool
def nmap(command: str):
    """ Tool to execute nmap command
    args:
        command: command to be executed -> str
        output: the logs from terminal ->str
    """
    print("yes")
    return subprocess.check_output(command, shell=True, text=True)
tools=[nmap]
nmap_model=ChatMistralAI(
    model='mistral-large-latest',
    api_key=MISTRAL_API_KEY
).bind_tools(tools)

def search_ports(state: State):
    response= nmap_model.invoke(state)

    return {"messages", [response]}

@tool
def gobuster(command: str):
    """
    Tool to use gobuster for directory bruteforcing
    """
    response=subprocess.check_output(command, shell=True, text=True)
    return {"messages": [response]}
model_gobuster = ChatMistralAI(
    model='mistral-large-latest',
    api_key=MISTRAL_API_KEY
).bind_tools([gobuster])
def directory_bruteforcing(state: State):
    response=model_gobuster(state)

    return {"messages", [response]}

@tool
def ffuf(command: str):
    """
    Tool for web fuzzing
    """
    response=subprocess.check_output(command, shell=True, text=True)

    return {"messages": [response]}
model_ffuf = ChatMistralAI(
    model='mistral-large-latest',
    api_key=MISTRAL_API_KEY
).bind_tools([ffuf])
def web_fuzzing(state: State):
    response = model_ffuf(state)
    return {"messages", [response]}

def should_continue1(state:State)->Literal["nmap", "directory_bruteforcing"]:
    last_message=state["messages"][-1]
    if last_message.tool_calls():
        return "nmap"
    else:
        return "directory_bruteforcing"
    
def should_continue2(state: State)->Literal["gobuster", "web_fuzzing"]:
    last_message=state["messages"][-1]

    if last_message.tool_calls():
        return "gobuster"
    else:
        return "web_fuzzing"

def should_continue3(state: State)->Literal["ffuf", END]:
    last_message=state["messages"][-1]
    if last_message.tool_calls():
        return "ffuf"
    return END

workflow = StateGraph(State)
workflow.add_node("search_ports", search_ports)
workflow.add_node("nmap", nmap)
workflow.add_node("directory_bruteforcing", directory_bruteforcing)
workflow.add_node("gobuster", gobuster)
workflow.add_node("web_fuzzing", web_fuzzing)
workflow.add_node("ffuf", ffuf)

workflow.add_edge(START, "search_ports")
workflow.add_edge("nmap", "search_ports")
workflow.add_edge("gobuster", "directory_bruteforcing")
workflow.add_edge("ffuf", "web_fuzzing")

workflow.add_conditional_edges("search_ports", should_continue1)
workflow.add_conditional_edges("directory_bruteforcing", should_continue2)
workflow.add_conditional_edges("web_fuzzing", should_continue3)

graph = workflow.compile()


graph_image = graph.get_graph().draw_mermaid_png()  # This generates the PNG

# Save the image to a file
with open("graph.png", "wb") as f:
    f.write(graph_image)
print("Image saved as graph.png")