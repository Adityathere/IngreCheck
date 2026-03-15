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
        model=Gemini(id="gemini-flash-lite-latest"),
        system_prompt=DESCRIPTION,
        instructions=INSTRUCTIONS,
        tools=[GoogleSearch(fixed_max_results=10)],
        show_tool_calls=False,
        markdown=True,
    )

def render_llm_output(content):
        st.markdown(
        f'<div class="llm-output">{content}</div>',
        unsafe_allow_html=True
    )

def analyze_image(image_path, agent):
    response = agent.run(
        """Analyze the product image with the following comprehensive steps:
        1. Extract ALL ingredients from the product label
        2. For EACH ingredient, provide:
           - The exact ingredient name
           - A concise 1-line description
           - Its primary function or origin
           - Any quick health note (if applicable)
        3. Format the results as a markdown table for easy reading (very important)""",
        images=[image_path],
    )
    

    ingredients_table = response.content

    analysis = agent.run(
        "Perform a comprehensive analysis of the product ingredients based on {system_prompt} and {instructions}",
        images=[image_path]
    ).content

    return ingredients_table, analysis






