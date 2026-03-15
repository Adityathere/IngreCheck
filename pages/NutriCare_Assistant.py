from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.googlesearch import GoogleSearch
from phi.run.response import RunEvent, RunResponse
from PIL import Image
import streamlit as st
from dotenv import load_dotenv
load_dotenv()


agent = Agent(
    name="Web Agent",
    role="Search the web for health and nutrition information",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[GoogleSearch()],
    description="A health-focused chatbot providing evidence-based information about nutrition, wellness, and fitness.",
    instructions=[
        "Provide accurate and user-friendly responses to health and nutrition queries.",
        "Always use tables to display nutrient requirements, recommended daily values, or any other structured data.",
        "When necessary, clarify medical terms and suggest consulting a healthcare professional for personalized advice.",
        "Maintain a conversational and empathetic tone to ensure user comfort."
    ],
    show_tool_calls=False,
    markdown=True,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
)


# Function to stream responses
def as_stream(response):
    full_response = ""
    for chunk in response:
        if isinstance(chunk, RunResponse) and isinstance(chunk.content, str):
            if chunk.event == RunEvent.run_response:
                full_response += chunk.content
                yield chunk.content  # Stream chunk to the interface
    return full_response




# Streamlit application
st.set_page_config( 
    page_title="NutriCare Assistant",
    page_icon="assets/favicon.png",
    layout="wide"
)
col1, col2, col3 = st.columns((1, 2, 1))
with col2:
    st.image(Image.open("assets/assistant.png"))


# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"],avatar="assets/user.png" if message["role"] == "user" else "assets/agent.png"):
        st.markdown(message["content"])

# Input for the user prompt
if prompt := st.chat_input("Let’s talk about Health, Nutrition, and Wellness. Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})  # Add user message
    with st.chat_message("user",avatar="assets/user.png"):
        st.markdown(prompt)

    # Agent response
    with st.chat_message("assistant",avatar="assets/agent.png"):
        chunks = agent.run(prompt, stream=True)
        response = "".join(as_stream(chunks))  # Collect the streamed response
        st.markdown(response)  # Display the final response

    # Save the assistant's response in the chat history
    st.session_state.messages.append({"role": "assistant", "content": response})


with st.sidebar:
    st.title("**About**")
    st.markdown("""
    This health and nutrition assistant provides:
    - Evidence-based information
    - Nutritional guidance
    - Wellness recommendations
    - Fitness advice
    
    :red-background[Please note: Provides general information and should not replace professional medical advice.]
    """)
    
    
    if st.button("Clear Chat",icon=":material/close:",use_container_width=True):
        st.session_state.messages = []
        st.rerun()
