"""
FILE: llm_utils_agent_advanced.py

TYPE: Agent-based (Advanced + Parallel Execution)

DESCRIPTION:
This module implements an advanced agent with multiple tools and parallel processing.
It enhances ingredient analysis using web search, Wikipedia, and food safety APIs.

KEY CHARACTERISTICS:
- Multi-tool agent (Tavily, DuckDuckGo, Wikipedia, OpenFoodFacts API)
- Custom tool for ingredient safety lookup
- Parallel execution for faster performance
- Optimized image handling (single encoding reuse)

USE CASE:
Designed for production-grade applications requiring high accuracy, speed,
and domain-specific intelligence (e.g., food ingredient analysis).
"""


import os
import base64
import mimetypes
import concurrent.futures
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import markdown as md
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from prompts import DESCRIPTION, INSTRUCTIONS, INGREDIENT_PROMPT, ANALYSIS_PROMPT, PRODUCT_DETAILS_PROMPT
from langchain.tools import tool


@tool
def check_ingredient_safety(ingredient_name: str) -> str:
    """
    Look up food safety data for a specific ingredient or additive using
    the Open Food Facts search API. Use this for E-numbers, food additives,
    preservatives, colorants, and any food ingredient name.
    """
    import requests
    import time

    url = "https://world.openfoodfacts.org/api/v2/search"
    tag = f"en:{ingredient_name.lower().replace(' ', '-')}"

    params = {
        "ingredients_tags": tag,
        "fields": "product_name,ingredients_analysis_tags,additives_tags,nutriscore_grade",
        "page_size": 3,
    }
    headers = {
        "User-Agent": "IngreCheck/1.0 (ingredient-analyzer-app)"
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=8)

            if response.status_code == 503:
                wait = 2 ** attempt
                time.sleep(wait)
                continue

            if response.status_code != 200:
                return f"API returned status {response.status_code} for '{ingredient_name}'"

            data = response.json()
            products = data.get("products", [])

            if not products:
                return f"No products found containing '{ingredient_name}' in Open Food Facts."

            results = []
            for p in products:
                name = p.get("product_name", "Unknown product")
                analysis = p.get("ingredients_analysis_tags", [])
                additives = p.get("additives_tags", [])
                nutriscore = p.get("nutriscore_grade", "N/A").upper()

                results.append(
                    f"Product: {name}\n"
                    f"  Ingredient analysis: {', '.join(analysis) if analysis else 'N/A'}\n"
                    f"  Additives present:   {', '.join(additives) if additives else 'None'}\n"
                    f"  Nutri-Score:         {nutriscore}"
                )

            return (
                f"Open Food Facts data for '{ingredient_name}':\n\n"
                + "\n\n".join(results)
            )

        except requests.Timeout:
            return f"No data returned for '{ingredient_name}' (request timed out)"
        except Exception as e:
            return f"Lookup failed for '{ingredient_name}': {str(e)}"

    return f"API unavailable after {max_retries} retries for '{ingredient_name}'"
    

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

    tavily_tool = TavilySearch(
        max_results=5,          
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
    )

    wikipedia_tool = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1000)
    )

    ddg_tool = DuckDuckGoSearchRun()

    return create_agent(
        llm,
        tools=[
            tavily_tool,          # primary web search
            ddg_tool,             # fallback web search, no quota
            wikipedia_tool,       # ingredient scientific background
            check_ingredient_safety,  # food-specific DB lookup
        ],
        system_prompt=system_prompt,
    )


def _load_image_as_base64(image_path: str) -> tuple[str, str]:
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    return image_data, mime_type


def _invoke_with_image_data(agent, prompt: str, image_data: str, mime_type: str) -> str:
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
    content = result["messages"][-1].content

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
    html = md.markdown(text, extensions=["tables", "nl2br"])
    st.markdown(f'<div class="llm-output">{html}</div>', unsafe_allow_html=True)


def analyze_image(image_path: str, model) -> tuple[str, str]:
    """
    Run ingredient extraction + analysis in parallel for faster results.

    Returns
    -------
    tuple[str, str]
        (ingredients_table, analysis) — both markdown strings.
    """
    # encode once, reuse for both parallel calls
    image_data, mime_type = _load_image_as_base64(image_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_ingredients = executor.submit(
            _invoke_with_image_data, model, INGREDIENT_PROMPT, image_data, mime_type
        )
        future_analysis = executor.submit(
            _invoke_with_image_data, model, ANALYSIS_PROMPT, image_data, mime_type
        )

        ingredients_table = future_ingredients.result()
        analysis = future_analysis.result()

    return ingredients_table, analysis
