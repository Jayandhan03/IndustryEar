from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from .llm import llm_model
import re


def clean_text(text: str) -> str:
    """
    Fix broken spacing like: 8 0 M i l l i o n -> 80 Million
    """
    # remove spaces between single characters
    text = re.sub(r'(?<=\w)\s(?=\w)', '', text)

    # normalize newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def agent():

    search = TavilySearch(max_results=2)

    agent_executor = create_agent(
        model=llm_model,
        tools=[search],
    )

    task_input = (
        "Find the latest news about how solo entrepreneurs use AI to become multimillionaires. "
        "Summarize in clear bullet points."
    )

    response = agent_executor.invoke(
        {"messages": [("user", task_input)]}
    )

    # -------- Extract ONLY final text --------
    final_text = None

    for msg in reversed(response["messages"]):
        if msg.type == "ai" and msg.content:
            # content can be list[dict] or str
            if isinstance(msg.content, list):
                for block in msg.content:
                    if block.get("type") == "text":
                        final_text = block.get("text")
                        break
            elif isinstance(msg.content, str):
                final_text = msg.content

        if final_text:
            break

    if not final_text:
        return "No summary generated."

    return clean_text(final_text)



if __name__ == "__main__":

    result = agent()
    print(result)   
