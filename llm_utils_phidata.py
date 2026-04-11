import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.googlesearch import GoogleSearch
from prompts import DESCRIPTION, INSTRUCTIONS


@st.cache_resource
def get_agent():
    return Agent(
        model=Gemini(id="gemini-3.1-flash-lite-preview"),
        system_prompt=DESCRIPTION,
        instructions=INSTRUCTIONS,
        tools=[GoogleSearch(fixed_max_results=10)],
        show_tool_calls=False,
        markdown=True,
    )


import markdown as md
def render_llm_output(text):
    html = md.markdown(text, extensions=["tables", "nl2br"])
    st.markdown(f'<div class="llm-output">{html}</div>', unsafe_allow_html=True)

def analyze_image(image_path, agent):
    response = agent.run(
"""Analyze the product image with the following comprehensive steps:

1. Extract ALL ingredients from the product label.
2. For EACH ingredient provide:
   - The exact ingredient name
   - A concise 1-line description
   - Its primary function or origin
   - Health Score (Safe / Moderate / Risky)
   - Any quick health note (if applicable)
3. Format the results as a markdown table for easy reading (very important)


Health Score rules:
Safe → 🟢
Moderate → 🟡
Risky → 🔴

Return ONLY a markdown table in this format:
| Ingredient | Description | Function | Health Score | Health Note |
|---|---|---|---|---|

Health Score must include the emoji.
""",
        images=[image_path],
    )

    ingredients_table = response.content
    analysis = agent.run(
        """Perform a comprehensive analysis of the product ingredients based on {system_prompt} and {instructions}.

At the very END of your analysis, always include an **Overall Product Rating** section in this exact format:

---
## Overall Product Rating

**Category:** <Safe 🟢 / Moderate 🟡 / Risky 🔴>

**Overall Score:** <X/5>

**Summary:** <One sentence verdict on the product's overall healthiness>
---


Base the Overall Category on:
- Safe 🟢 → Mostly natural, minimal additives, no major health concerns
- Moderate 🟡 → Some artificial additives or moderate health concerns
- Risky 🔴 → Multiple harmful additives, high sugar/sodium, significant health concerns
""",
        images=[image_path]
    ).content

    return ingredients_table, analysis





