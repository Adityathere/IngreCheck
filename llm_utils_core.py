"""
FILE: llm_utils_core.py

TYPE: Direct LLM (No Agent)

DESCRIPTION:
This module uses a direct LLM invocation approach without any agent or external tools.
It sends prompts and images directly to the Gemini model and returns responses.

KEY CHARACTERISTICS:
- No agent framework
- No external tools (no search, no APIs)
- Fully deterministic and controlled execution
- Sequential processing (ingredient extraction → analysis)

USE CASE:
Best suited for simple, fast, and predictable workflows where no external knowledge is required.
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



@st.cache_resource
def get_agent() -> ChatGoogleGenerativeAI:
    if isinstance(INSTRUCTIONS, list):
        instructions_text = "\n".join(INSTRUCTIONS)
    else:
        instructions_text = INSTRUCTIONS

    system_prompt = f"{DESCRIPTION}\n\n{instructions_text}"
    model = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        max_retries=3,
    )

    model._system_prompt = system_prompt
    return model



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


def _invoke_with_image(model: ChatGoogleGenerativeAI, prompt: str, image_path: str) -> str:
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

    system_message = SystemMessage(content=model._system_prompt)
    response: AIMessage = model.invoke([system_message, human_message])
    content = response.content
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Extract text from each block; blocks are either str or {"type":"text","text":...}
        return "\n".join(
            block["text"] if isinstance(block, dict) and "text" in block
            else str(block)
            for block in content
            if not (isinstance(block, dict) and block.get("type") == "tool_use")
        )
    else:
        return str(content)  # absolute fallback



def render_llm_output(text: str) -> None:
    """Render markdown LLM output safely in Streamlit."""
    html = md.markdown(text, extensions=["tables", "nl2br"])
    st.markdown(f'<div class="llm-output">{html}</div>', unsafe_allow_html=True)




def analyze_image(image_path: str, model: ChatGoogleGenerativeAI) -> tuple[str, str]:
    """
    Run the two-step ingredient extraction + holistic analysis on a product image.

    Parameters
    ----------
    image_path : str
        Path to the product image file.
    model : ChatGoogleGenerativeAI
        The bound model returned by get_agent().

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