import streamlit as st
from srt_processor import parse_srt_file, create_srt_output, validate_srt_content

# Page configuration
st.set_page_config(
    page_title="OpenSubTrans",
    page_icon="🎬",
    layout="centered"
)

# Title
st.title("🎬 OpenSubTrans")
st.write("Translate movie and TV subtitles using AI")

# API Key input
st.subheader("🔑 OpenAI API Key")
api_key = st.text_input(
    "Enter your OpenAI API Key:",
    type="password",
    placeholder="sk-..."
)

# File upload
st.subheader("📁 Upload Subtitle File")
uploaded_file = st.file_uploader(
    "Choose a subtitle file",
    type=['srt', 'vtt', 'ass', 'ssa']
)

# Process uploaded file
if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    # Display file info
    file_details = {
        "Filename": uploaded_file.name,
        "File size": f"{uploaded_file.size} bytes",
        "File type": uploaded_file.type
    }
    st.write("**File Details:**")
    for key, value in file_details.items():
        st.write(f"- {key}: {value}")
    
    # Process and preview the subtitle file (only for SRT files for now)
    if uploaded_file.name.lower().endswith('.srt'):
        try:
            # Read file content
            file_content = uploaded_file.read().decode('utf-8')
            
            # Validate SRT format
            if validate_srt_content(file_content):
                st.success("✅ Valid SRT format detected")
                
                # Parse subtitles
                parsed_entries = parse_srt_file(file_content)
                st.info(f"📊 Found {len(parsed_entries)} subtitle entries")
                
                # Show preview of first few entries
                if parsed_entries:
                    st.subheader("🔍 Preview (First 5 entries)")
                    preview_count = min(5, len(parsed_entries))
                    
                    for i in range(preview_count):
                        start, end, text = parsed_entries[i]
                        with st.expander(f"Entry {i+1}: {start} → {end}"):
                            st.write(text)
                            
                    if len(parsed_entries) > 5:
                        st.write(f"... and {len(parsed_entries) - 5} more entries")
                        
            else:
                st.error("❌ Invalid SRT format. Please upload a valid SRT file.")
                
        except UnicodeDecodeError:
            st.error("❌ Unable to read file. Please ensure it's a text-based SRT file.")
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    else:
        st.info("ℹ️ Currently only SRT format is supported. Other formats coming soon!")

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

# Translation button
st.subheader("🚀 Translation")
if st.button("Start Translation", type="primary"):
    if not api_key:
        st.error("Please enter your OpenAI API key")
    elif not uploaded_file:
        st.error("Please upload a subtitle file")
    else:
        # Check if file is SRT format
        if not uploaded_file.name.lower().endswith('.srt'):
            st.error("❌ Currently only SRT format is supported")
        else:
            try:
                # Reset file pointer and read content
                uploaded_file.seek(0)
                file_content = uploaded_file.read().decode('utf-8')
                
                if validate_srt_content(file_content):
                    parsed_entries = parse_srt_file(file_content)
                    
                    st.success("✅ Ready to translate!")
                    st.info(f"📁 File: {uploaded_file.name}")
                    st.info(f"🌍 Target Language: {target_language}")
                    st.info(f"📊 Subtitle entries: {len(parsed_entries)}")
                    
                    # Show what would be translated
                    with st.expander("Show sample entries to be translated"):
                        sample_count = min(2, len(parsed_entries))
                        for i in range(sample_count):
                            start, end, text = parsed_entries[i]
                            st.write(f"**{start} → {end}**")
                            st.write(f"Original: {text}")
                            st.write(f"Will translate to: {target_language}")
                            st.write("---")
                    
                    st.info("🔄 Translation functionality will be implemented in the next step...")
                    
                else:
                    st.error("❌ Invalid SRT format detected")
                    
            except UnicodeDecodeError:
                st.error("❌ Unable to read file. Please ensure it's a text-based SRT file.")
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
