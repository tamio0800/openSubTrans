import streamlit as st
import os
from srt_processor import parse_srt_file, create_srt_output, validate_srt_content
from translator import translate_with_openai, estimate_translation_cost

# Page configuration
st.set_page_config(
    page_title="OpenSubTrans",
    page_icon="🎬",
    layout="centered"
)

# Title
st.title("🎬 OpenSubTrans")
st.write("Translate movie and TV subtitles using AI")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # OpenAI API Key input
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key to enable translation"
    )
    
    # GPT-5 model selection (simplified)
    model_info = {
        "gpt-5-mini": "GPT-5 Mini - Balanced performance",
        "gpt-5": "GPT-5 - Ultimate quality 🚀"
    }
    
    selected_model = st.selectbox(
        "OpenAI Model",
        options=list(model_info.keys()),
        format_func=lambda x: model_info[x],
        index=0,
        help="Choose the GPT-5 model for translation."
    )

# Initialize session state
if 'file_processed' not in st.session_state:
    st.session_state.file_processed = False
if 'translation_completed' not in st.session_state:
    st.session_state.translation_completed = False

# File upload
st.subheader("📁 Upload Subtitle File")
uploaded_file = st.file_uploader(
    "Choose a subtitle file",
    type=['srt']
)

# Target language selection
st.subheader("🌍 Target Language")
languages = [
    "Chinese (Traditional)",
    "Chinese (Simplified)", 
    "Japanese",
    "Korean",
    "English"
]

target_language = st.selectbox(
    "Select target language:",
    languages
)

# Process file when uploaded
if uploaded_file is not None:
    # Only process file once
    if not st.session_state.file_processed or st.session_state.get('current_file') != uploaded_file.name:
        try:
            # Read and process file
            file_content = uploaded_file.read().decode('utf-8')
            
            if validate_srt_content(file_content):
                parsed_entries = parse_srt_file(file_content)
                texts_to_translate = [entry[2] for entry in parsed_entries]
                
                # Store in session state
                st.session_state.file_content = file_content
                st.session_state.parsed_entries = parsed_entries
                st.session_state.texts_to_translate = texts_to_translate
                st.session_state.current_file = uploaded_file.name
                st.session_state.file_processed = True
                st.session_state.translation_completed = False
                
                # File processed silently
                
            else:
                st.error("Invalid SRT format")
                st.session_state.file_processed = False
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.file_processed = False

# Show file details and cost estimation if file is processed
if st.session_state.file_processed:
    
    # Cost estimation
    cost_info = estimate_translation_cost(st.session_state.texts_to_translate, target_language, selected_model)
    
    # Show cost only if significant
    if cost_info['estimated_cost_usd'] > 0.01:
        st.write(f"**Estimated cost:** ${cost_info['estimated_cost_usd']:.4f}")
    
    st.divider()

# Translation section
st.subheader("🚀 Translation")

# Check if ready to translate
can_translate = api_key and uploaded_file and st.session_state.file_processed

if not can_translate:
    translate_button = st.button("🚀 Start Translation", type="primary", disabled=True)
    if not api_key:
        st.error("Please enter your API key")
    elif not uploaded_file:
        st.error("Please upload a file")
    elif not st.session_state.file_processed:
        st.error("Please upload a valid SRT file")
else:
    translate_button = st.button("🚀 Start Translation", type="primary")

# Handle translation
if translate_button and can_translate:
    st.session_state.translation_completed = False
    
    try:
        # Translation process with simple progress
        with st.spinner("Translating..."):
            progress_bar = st.progress(0)
            
            # Perform translation
            translated_texts = translate_with_openai(
                st.session_state.texts_to_translate, 
                target_language, 
                api_key, 
                selected_model
            )
            
            progress_bar.progress(100)
            
            # Create translated SRT content
            translated_entries = []
            for i, translated_text in enumerate(translated_texts):
                start, end, original_text = st.session_state.parsed_entries[i]
                translated_entries.append((start, end, translated_text))
            
            translated_srt = create_srt_output(translated_entries)
            
            # Store results
            st.session_state.translated_texts = translated_texts
            st.session_state.translated_srt = translated_srt
            st.session_state.translation_completed = True
            
            # Clear progress
            progress_bar.empty()
            
    except Exception as e:
        st.error(f"Translation failed: {str(e)}")

# Show results if translation completed
if st.session_state.translation_completed:
    # Generate filename
    original_name = st.session_state.current_file.rsplit('.', 1)[0]
    lang_code = target_language.replace(' ', '_').replace('(', '').replace(')', '').lower()
    translated_filename = f"{original_name}_{lang_code}.srt"
    
    # Download button
    st.download_button(
        label=f"Download {translated_filename}",
        data=st.session_state.translated_srt,
        file_name=translated_filename,
        mime="text/plain",
        type="primary",
        use_container_width=True
    )
    
    # Show sample results
    with st.expander("Preview translation", expanded=True):
        sample_count = min(3, len(st.session_state.parsed_entries))
        for i in range(sample_count):
            start, end, original = st.session_state.parsed_entries[i]
            translated = st.session_state.translated_texts[i]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**{start} → {end}**")
                st.write(original)
            with col2:
                st.write("**Translated**")
                st.write(translated)
            
            if i < sample_count - 1:
                st.divider()