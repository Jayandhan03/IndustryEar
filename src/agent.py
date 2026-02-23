import re
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from .llm import llm_model
from news import fetch_news

def clean_text(text: str) -> str:
    """
    Fix broken spacing like: 8 0 M i l l i o n -> 80 Million
    """
    # remove spaces between single characters only if there are multiple in a row (e.g., "8 0 M i l l i o n")
    text = re.sub(r'(?<=\b\w)\s(?=\w\b)', '', text)

    # normalize newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def agent(topic: str = "How solo entrepreneurs use AI to become multimillionaires"):

    # 1. Fetch fresh news from RapidAPI
    news_data = fetch_news(query=topic, limit=3)
    news_context = ""
    if news_data and "data" in news_data:
        for article in news_data["data"]:
            news_context += f"- {article.get('title')}: {article.get('link')}\n"

    search = TavilySearch(max_results=2)

    agent_executor = create_agent(
        model=llm_model,
        tools=[search],
    )

    task_input = (
        f"Find the latest news about {topic}. "
        f"Here is some initial news context to consider:\n{news_context}\n"
        "Summarize the most important findings in clear bullet points."
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
