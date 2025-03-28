import os
import streamlit as st
from PIL import Image
from io import BytesIO
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.googlesearch import GoogleSearch
from tempfile import NamedTemporaryFile
from prompts import DESCRIPTION, INSTRUCTIONS

MAX_IMAGE_WIDTH = 300

def resize_image_for_display(image_file):
    """Resize image for display only, returns bytes."""
    if isinstance(image_file, str):
        img = Image.open(image_file)
    else:
        img = Image.open(image_file)
        image_file.seek(0)

    aspect_ratio = img.height / img.width
    new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
    img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@st.cache_resource
def get_agent():
    return Agent(
        model=Gemini(id="gemini-2.0-flash-exp"),
        system_prompt=DESCRIPTION,
        instructions=INSTRUCTIONS,
        tools=[GoogleSearch(fixed_max_results=10)],
        show_tool_calls=True,
        markdown=True,
    )

def analyze_image(image_path, agent):
    response = agent.run(
        "Analyze the given image and list ingredients in table format",
        images=[image_path],
    )
    return response.content

def save_uploaded_file(uploaded_file):
    with NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        return temp_file.name

def remove_file(file_path):
    try:
        os.unlink(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")






def main():
    # Initialize session state attributes if they don't exist
    if 'selected_example' not in st.session_state:
        st.session_state.selected_example = None
    if 'selected_example_name' not in st.session_state:
        st.session_state.selected_example_name = None
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False

    st.set_page_config(
        page_title="IngreCheck",
        page_icon="assets/favicon.png",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={'About': "# This is a header. This is an *extremely* cool app!"}
    )

    # Sidebar for mode selection
    st.sidebar.markdown("Select between analyzing a single product or comparing two products.")
    mode = st.sidebar.radio(":green-background[:green[**Choose Mode**]]", ["**Analyze Product Ingredients**", "**Compare Product Ingredients**"])

    agent = get_agent()

    # Sample Image selection in the sidebar
    if mode == "**Analyze Product Ingredients**":
     with st.sidebar.expander("**Sample Images**", icon=":material/imagesmode:"):
        example_images = {
            "Chocolate(Dairy Milk)": "sample_images/Cadbury_DairyMilk.jpg",
            "Nutella": "sample_images/nutella.jpg",
            "Chips(Lays)": "sample_images/Lays_chips.jpg",
            "Energy Drink(Bournvita)": "sample_images/Bournvita.jpg",
            "Tomato Sauce(Kissan)": "sample_images/KissanTomato_Sauce.png",
            "Jam(Kissan)": "sample_images/Kissan_Jam.jpg",
            "Shampoo(Khadi)": "sample_images/Khadi_Shampoo.jpg",
            "moisturizer(Vaseline)": "sample_images/Vaseline.jpg",
            "Cleanser(Cetaphil)": "sample_images/Cetaphil_Cleanser.jpg"
        }

        for name, path in example_images.items():
            if st.button(name, use_container_width=True):
                st.session_state.selected_example = path
                st.session_state.selected_example_name = name
                st.session_state.analyze_clicked = False

    # Analyzer Mode
    if mode == "**Analyze Product Ingredients**":
        col1, outer_col2, col3 = st.columns((1, 4, 1))
        with outer_col2:
            st.image(Image.open("assets/logo.png"))
            with st.expander("**About**", icon=":material/info:", expanded=False):
                st.write(""" 
                :green-background[:green[**IngreCheck**]] is a :green-background[:green[**Product Ingredients Analyzer**]] an AI-powered application that helps you decode the ingredients in the products you use every day. 
                Whether you're uploading an image, snapping a quick photo, or selecting from a range of sample images, this app provides deep insights into what’s inside your products, empowering you to make healthier choices.

                #### Key Features:
                ▶️ Easily upload, capture, or select images of product ingredients directly from the app.  
                ▶️ AI-driven analysis that evaluates whether the ingredients are healthy or harmful.  
                ▶️ Interactive design with sample product images, perfect for quick testing.  
                ▶️ Agentic AI approach for dynamic and personalized ingredient evaluation.  
                """)

        # Sidebar options for Analyzer
        uploaded_file = st.sidebar.file_uploader(":green-background[:green[**Upload product image**]]", type=["jpg", "jpeg", "png"])
        camera_photo = st.sidebar.camera_input(":green-background[:green[**Take a picture of the Product**]]")

        col1, col2, col3 = st.columns([1, 2, 1])
        if uploaded_file or camera_photo:
            with col2:
                image_source = uploaded_file if uploaded_file else camera_photo
                resized_image = resize_image_for_display(image_source)
                st.image(resized_image, caption="Uploaded Image", use_container_width=False, width=MAX_IMAGE_WIDTH)

                if st.button("Analyze Image"):
                    temp_path = save_uploaded_file(image_source)
                    try:
                        with st.spinner("Analyzing image..."):
                            analysis = analyze_image(temp_path, agent)
                        st.markdown("### Analysis Result")
                        st.markdown(analysis)
                    finally:
                        remove_file(temp_path)

        # Display selected example image for analysis
        if st.session_state.selected_example:
            st.divider()
            st.subheader(f"Selected Product: {st.session_state.selected_example_name}")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                resized_image = resize_image_for_display(st.session_state.selected_example)
                st.image(resized_image, caption="Selected Example", use_container_width=False, width=MAX_IMAGE_WIDTH)

            if st.button("Analyze Example", key="analyze_example") and not st.session_state.analyze_clicked:
                st.session_state.analyze_clicked = True
                analysis_result=analyze_image(st.session_state.selected_example,agent)
                st.markdown("### Analysis Result")
                st.markdown(analysis_result)  # Display the analysis result

    # Comparison Mode
    elif mode == "**Compare Product Ingredients**":
        col1, outer_col2, col3 = st.columns((1, 4, 1))
        with outer_col2:
            st.image(Image.open("assets/logo2.png"))
            with st.expander("**About**", icon=":material/info:", expanded=False):
                st.write(""":green-background[:green[**IngreCompare**]] is an AI-powered application that compares the ingredients of two products side by side.

#### Key Features:
▶️ Compare ingredients lists of two products at a glance.  
▶️ Upload or Take photos of products for side by side comparison.  
▶️ AI-driven analysis highlights similarities and differences."""                       )
        product1_path, product2_path = None, None

        # Sidebar options for Comparison
        product1_file = st.sidebar.file_uploader(":green-background[:green[**Upload Image for Product 1**]]", type=["jpg", "jpeg", "png"])
        product2_file = st.sidebar.file_uploader(":green-background[:green[**Upload Image for Product 2**]]", type=["jpg", "jpeg", "png"])
        product1_camera = st.sidebar.camera_input(":green-background[:green[**Take a picture of Product 1**]]")
        product2_camera = st.sidebar.camera_input(":green-background[:green[**Take a picture of Product 2**]]")

        col1, col2 = st.columns(2)

        with col1:
            if product1_file or product1_camera:
                image_source = product1_file if product1_file else product1_camera
                resized_image = resize_image_for_display(image_source)
                st.image(resized_image, caption="Product 1", width=MAX_IMAGE_WIDTH)
                product1_path = save_uploaded_file(image_source)

        with col2:
            if product2_file or product2_camera:
                image_source = product2_file if product2_file else product2_camera
                resized_image = resize_image_for_display(image_source)
                st.image(resized_image, caption="Product 2", width=MAX_IMAGE_WIDTH)
                product2_path = save_uploaded_file(image_source)

        if product1_path and product2_path:
            if st.button("Compare Ingredients"):
                try:
                    with st.spinner("Analyzing and comparing..."):
                        product1_analysis = analyze_image(product1_path, agent)
                        product2_analysis = analyze_image(product2_path, agent)

                        st.markdown("### Comparison Results")
                        comparison_col1, comparison_col2 = st.columns(2)
                        with comparison_col1:
                            st.write("#### Product 1 Ingredients")
                            st.markdown(product1_analysis)
                        with comparison_col2:
                            st.write("#### Product 2 Ingredients")
                            st.markdown(product2_analysis)
                finally:
                    remove_file(product1_path)
                    remove_file(product2_path)


if __name__ == "__main__":
    main()


