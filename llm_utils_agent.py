"""
FILE: llm_utils_agent.py

TYPE: Agent-based (Basic)

DESCRIPTION:
This module uses a LangChain agent with limited tool support (e.g., Tavily search).
The agent can enhance responses by retrieving external information when needed.

KEY CHARACTERISTICS:
- Uses LangChain agent framework
- Includes basic web search tool (Tavily)
- Dynamic reasoning capability
- Sequential execution

USE CASE:
Suitable for applications that require occasional external data lookup or enhanced reasoning.
"""

import os
import base64
import mimetypes
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import markdown as md
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from prompts import DESCRIPTION, INSTRUCTIONS, INGREDIENT_PROMPT, ANALYSIS_PROMPT


from langchain.agents import create_agent  
from langchain_community.tools.tavily_search import TavilySearchResults

@st.cache_resource
def get_agent():
    if isinstance(INSTRUCTIONS, list):
        instructions_text = "\n".join(INSTRUCTIONS)
    else:
        instructions_text = INSTRUCTIONS

    system_prompt = f"{DESCRIPTION}\n\n{instructions_text}"

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_retries=3,
    )

    tavily_tool = TavilySearchResults(
        max_results=10,
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
    )


    agent = create_agent(
        llm,
        tools=[tavily_tool],
        system_prompt=system_prompt,
    )
    return agent



def _load_image_as_base64(image_path: str) -> tuple[str, str]:
    """
    Read a local image file and return (base64_string, mime_type).
    Supports JPEG, PNG, WEBP, GIF (anything mimetypes recognises).
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"  # safe default

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    return image_data, mime_type



def _invoke_with_image(agent, prompt: str, image_path: str) -> str:
    image_data, mime_type = _load_image_as_base64(image_path)

    human_message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
            },
        ]
    )

    result = agent.invoke({"messages": [human_message]})

    last_message = result["messages"][-1]
    content = last_message.content

    # same type-safety normalization — AIMessage.content can be str or list
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "\n".join(
            block["text"] if isinstance(block, dict) and "text" in block
            else str(block)
            for block in content
            if not (isinstance(block, dict) and block.get("type") == "tool_use")
        )
    else:
        return str(content)



def render_llm_output(text: str) -> None:
    """Render markdown LLM output safely in Streamlit."""
    html = md.markdown(text, extensions=["tables", "nl2br"])
    st.markdown(f'<div class="llm-output">{html}</div>', unsafe_allow_html=True)



def analyze_image(image_path: str, model) -> tuple[str, str]:
    """
    Run the two-step ingredient extraction + holistic analysis on a product image.
    Parameters
    ----------
    image_path : str
        Path to the product image file.
    model : agent
        The agent returned by get_agent().

    Returns
    -------
    tuple[str, str]
        (ingredients_table, analysis) — both are markdown strings (str),
        identical in type to the original phidata implementation.
    """
    
    # ── Step 1: Ingredient extraction ────────────────────────────────────────
    # Replaces: response = agent.run(INGREDIENT_PROMPT, images=[image_path])
    #           ingredients_table = response.content
    ingredients_table: str = _invoke_with_image(
        model,
        prompt=INGREDIENT_PROMPT,
        image_path=image_path,
    )

    # ── Step 2: Holistic product analysis ────────────────────────────────────
    # Replaces: analysis = agent.run(ANALYSIS_PROMPT, images=[image_path]).content
    analysis: str = _invoke_with_image(
        model,
        prompt=ANALYSIS_PROMPT,
        image_path=image_path,
    )

    # Returns tuple[str, str] — identical to the original phidata implementation
    return ingredients_table, analysis