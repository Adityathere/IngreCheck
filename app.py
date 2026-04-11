from llm_utils_agent_advanced import get_agent, analyze_image, render_llm_output
from image_utils import resize_image_for_display, save_uploaded_file, remove_file
import streamlit as st
from PIL import Image
MAX_IMAGE_WIDTH = 300
st.set_page_config(page_title="IngreCheck", layout="wide")


def render_overall_rating(analysis_text):
    """Extracts and renders the overall rating as a styled banner."""
    import re

    if "Safe 🟢" in analysis_text or ("Safe" in analysis_text and "🟢" in analysis_text):
        color = "#2ecc71"
        bg = "#e9faf0"
        label = "Safe 🟢"
    elif "Risky 🔴" in analysis_text or ("Risky" in analysis_text and "🔴" in analysis_text):
        color = "#e74c3c"
        bg = "#fdf0f0"
        label = "Risky 🔴"
    else:
        color = "#f39c12"
        bg = "#fef9e7"
        label = "Moderate 🟡"

    score_match = re.search(r"\*\*Overall Score:\*\*\s*([\d.]+/\d+)", analysis_text)
    score = score_match.group(1) if score_match else "N/A"

    summary_match = re.search(r"\*\*Summary:\*\*\s*(.+?)(?:\n\n|\Z)", analysis_text, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""

    st.markdown(f"""
    <div class="llm-output" style="
        background-color: {bg};
        border-left: 6px solid {color};
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
    ">
        <div style="font-size: 22px; font-weight: bold; color: {color};">
            Overall Rating: {label}
        </div>
        <div style="font-size: 16px; margin-top: 6px; color: #333;">
            <strong>Score:</strong> {score} &nbsp;|&nbsp; {summary}
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="IngreCheck",
        page_icon="assets/favicon.png",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={'About': "# This is a header. This is an *extremely* cool app!"}
    )

    # Initialize session state attributes if they don't exist
    if 'selected_example' not in st.session_state:
        st.session_state.selected_example = None
    if 'selected_example_name' not in st.session_state:
        st.session_state.selected_example_name = None
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False


    st.markdown("""
<style>
/* Georgia font only for LLM output content */
.llm-output,
.llm-output p,
.llm-output li,
.llm-output td,
.llm-output th,
.llm-output h1,
.llm-output h2,
.llm-output h3,
.llm-output h4,
.llm-output div,
.llm-output span,
.llm-output strong,
.llm-output em {
    font-family: Georgia, "Times New Roman", serif !important;
    font-size: 18px;
}

.llm-output {
    overflow-x: auto;
    display: block;
    max-width: 100%;
}

.llm-output table {
    border-collapse: collapse;
    width: 100%;
    table-layout: fixed;
    word-wrap: break-word;
}

.llm-output table td,
.llm-output table th {
    border: 1px solid #ddd;
    padding: 8px;
    word-break: break-word;
    overflow-wrap: break-word;
}

.llm-output table td:first-child {
    font-weight: bold;
}

.llm-output table tr:nth-child(even) {
    background-color: #f9f9f9;
}

/* Analysis title styling */
.analysis-title {
    font-family: Georgia, "Times New Roman", serif !important;
    font-size: 28px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


    # Sidebar for mode selection
    st.sidebar.markdown("Select between analyzing a single product or comparing two products.")
    mode = st.sidebar.radio(":green-background[:green[**Choose Mode**]]", ["**Analyze Product Ingredients**", "**Compare Product Ingredients**"])

    agent = get_agent()

    # Sample Image selection in the sidebar
    if mode == "**Analyze Product Ingredients**":
     with st.sidebar.expander("**Sample Images**", icon=":material/imagesmode:"):
        example_images = {
            "Chocolate": "sample_images/Cadbury_DairyMilk.jpg",
            "Nutella": "sample_images/nutella.jpg",
            "Chips": "sample_images/Lays_chips.jpg",
            "Energy Drink": "sample_images/Bournvita.jpg",
            "Tomato Sauce": "sample_images/KissanTomato_Sauce.png",
            "Jam": "sample_images/Kissan_Jam.jpg",
            "Shampoo": "sample_images/Khadi_Shampoo.jpg",
            "moisturizer": "sample_images/Vaseline.jpg",
            "Cleanser": "sample_images/Cetaphil_Cleanser.jpg"
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
                Whether you're uploading an image, snapping a quick photo, or selecting from a range of sample images, this app provides deep insights into what's inside your products, empowering you to make healthier choices.

                #### Key Features:
                ▶️ Easily upload, capture, or select images of product ingredients directly from the app.  
                ▶️ AI-driven analysis that evaluates whether the ingredients are healthy or harmful.  
                ▶️ Interactive design with sample product images, perfect for quick testing.  
                ▶️ Agentic AI approach for dynamic and personalized ingredient evaluation.""", unsafe_allow_html=True)

        # Sidebar options for Analyzer
        uploaded_file = st.sidebar.file_uploader(":green-background[:green[**Upload product image**]]", type=["jpg", "jpeg", "png"])
        camera_photo = st.sidebar.camera_input(":green-background[:green[**Take a picture of the Product**]]")

        
        col1, col2, col3 = st.columns([1, 2, 1])
        if uploaded_file or camera_photo:
            image_source = uploaded_file if uploaded_file else camera_photo
            
            with col2:
                resized_image = resize_image_for_display(image_source)
                st.image(resized_image, caption="Uploaded Image", use_container_width=False)
                
            if st.button("Analyze Image"):
                temp_path = save_uploaded_file(image_source)
                try:
                    with st.spinner("Analyzing image..."):
                        ingredients_table, analysis = analyze_image(temp_path, agent)

                        st.markdown('<div class="analysis-title">Ingredients Breakdown</div>', unsafe_allow_html=True)
                        render_llm_output(ingredients_table)
                        
                        st.divider()
                        
                        st.markdown('<div class="analysis-title">Analysis Result</div>', unsafe_allow_html=True)
                        render_overall_rating(analysis)
                        render_llm_output(analysis)
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
                ingredients_table, analysis = analyze_image(st.session_state.selected_example, agent)
                
                st.markdown('<div class="analysis-title">Ingredients Breakdown</div>', unsafe_allow_html=True)
                render_llm_output(ingredients_table)
                st.divider()
                st.markdown('<div class="analysis-title">Analysis Result</div>', unsafe_allow_html=True)
                render_overall_rating(analysis)
                render_llm_output(analysis)

    # Comparison Mode
    elif mode == "**Compare Product Ingredients**":
        col1, outer_col2, col3 = st.columns((1, 4, 1))
        with outer_col2:
            st.image(Image.open("assets/logo2.png"))
            with st.expander("**About**", icon=":material/info:", expanded=False):
                st.write("""
                         
                         :green-background[:green[**IngreCompare**]] is an AI-powered application that compares the ingredients of two products side by side.
#### Key Features:
▶️ Compare ingredients lists of two products at a glance.  
▶️ Upload or Take photos of products for side by side comparison.  
▶️ AI-driven analysis highlights similarities and differences. """)
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
                        product1_table, product1_analysis = analyze_image(product1_path, agent)
                        product2_table, product2_analysis = analyze_image(product2_path, agent)
                        st.markdown("### Comparison Results")
                       
                        comparison_col1, comparison_col2 = st.columns(2)
                        with comparison_col1:
                            st.markdown('<div class="analysis-title">Product 1 Ingredients</div>', unsafe_allow_html=True)
                            render_llm_output(product1_table)

                           
                            st.markdown('<div class="analysis-title">Analysis</div>', unsafe_allow_html=True)
                            render_overall_rating(product1_analysis) # <-- add this line
                            render_llm_output(product1_analysis)
                        
                        with comparison_col2:
                            st.markdown('<div class="analysis-title">Product 2 Ingredients</div>', unsafe_allow_html=True)
                            render_llm_output(product2_table)

                           
                            st.markdown('<div class="analysis-title">Analysis</div>', unsafe_allow_html=True)
                            render_overall_rating(product2_analysis) # <-- add this line
                            render_llm_output(product2_analysis)                   
                finally:
                    remove_file(product1_path)
                    remove_file(product2_path)


if __name__ == "__main__":
    main()