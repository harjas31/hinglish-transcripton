import streamlit as st
import tempfile
import os
from openai import OpenAI
from datetime import timedelta
import ast

# Constants
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a"}

def format_time(seconds):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def parse_word(word_str):
    # Extract values from the TranscriptionWord string
    try:
        # Convert the string representation to a dictionary-like structure
        word_str = word_str.replace("TranscriptionWord(", "").replace(")", "")
        parts = word_str.split(", ")
        word_data = {}
        for part in parts:
            key, value = part.split("=")
            word_data[key] = float(value) if key in ['start', 'end'] else value.strip("'")
        return word_data
    except Exception as e:
        st.error(f"Error parsing word: {word_str}, Error: {str(e)}")
        return None

def transcribe_audio(api_key, audio_file):
    client = OpenAI(api_key=api_key)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        temp_audio_file.write(audio_file.read())
        temp_audio_file_path = temp_audio_file.name

    try:
        with open(temp_audio_file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"],
                prompt="Yeh audio Hinglish mein hai. Hum Hindi bol rahe hain, lekin yeh sab Roman script mein likha gaya hai. Transcribe this audio into very short phrases or fragments. Each segment should be extremely brief, ideally no more than 2-3 words long. Break sentences into smaller parts if necessary.",
            )
            return response
    except Exception as e:
        if "Incorrect API key provided" in str(e):
            st.error("Invalid API key. Please check your OpenAI API key and try again.")
        else:
            st.error(f"An error occurred during transcription: {str(e)}")
        return None
    finally:
        os.unlink(temp_audio_file_path)

def generate_srt(response):
    if not response:
        st.error("No transcription response received")
        return ""
    
    srt_content = ""
    counter = 1
    
    try:
        # Process words directly from the words list
        if hasattr(response, 'words') and response.words:
            for word_str in response.words:
                word_data = parse_word(word_str)
                if word_data:
                    start_time = word_data['start']
                    end_time = word_data['end']
                    text = word_data['word']
                    
                    srt_content += f"{counter}\n{format_time(start_time)} --> {format_time(end_time)}\n{text}\n\n"
                    counter += 1
    except Exception as e:
        st.error(f"Error in generate_srt: {str(e)}")
        return ""
    
    return srt_content

# Streamlit UI
st.set_page_config(page_title="Audio Transcription to SRT", page_icon="🎙️")

st.title("🎙️ Audio Transcription to SRT")
st.markdown("Created with ❤️ by Harjas Singh [Best Intern]")
st.markdown("""
This app allows you to transcribe audio files and generate SRT subtitles using OpenAI's API.
Now with word-level timestamp granularity!

Please note:
- Your API key and uploaded files are not stored and are only used for the current session.
- Maximum file size: 25 MB
- Supported formats: MP3, WAV, M4A
""")

api_key = st.text_input("Enter your OpenAI API key:", type="password")

if api_key:
    uploaded_file = st.file_uploader("Choose an audio file", type=list(ALLOWED_EXTENSIONS))

    if uploaded_file:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.write(file_details)

        if uploaded_file.size > MAX_FILE_SIZE:
            st.error(f"File size exceeds the maximum limit of {MAX_FILE_SIZE / 1024 / 1024} MB.")
        else:
            if st.button("Transcribe and Generate SRT"):
                with st.spinner("Transcribing audio... This may take a few minutes."):
                    transcription = transcribe_audio(api_key, uploaded_file)
                
                if transcription:
                    try:
                        srt_content = generate_srt(transcription)
                        if srt_content:
                            st.success("Transcription complete!")
                            
                            st.subheader("Generated SRT Content:")
                            st.text_area("SRT Content", srt_content, height=300)
                            
                            st.download_button(
                                label="Download SRT File",
                                data=srt_content,
                                file_name="transcription.srt",
                                mime="text/plain"
                            )
                            
                            with st.expander("Debug Information"):
                                try:
                                    st.text("Full text:")
                                    st.text(transcription.text)
                                    st.text("\nWord-level information:")
                                    for word_str in transcription.words:
                                        word_data = parse_word(word_str)
                                        if word_data:
                                            st.text(f"Word: {word_data['word']}, Start: {word_data['start']:.2f}, End: {word_data['end']:.2f}")
                                except Exception as e:
                                    st.error(f"Error in debug info: {str(e)}")
                    except Exception as e:
                        st.error(f"Error processing transcription: {str(e)}")

st.markdown("---")
