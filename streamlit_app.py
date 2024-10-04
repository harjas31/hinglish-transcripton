import streamlit as st
import tempfile
import os
from openai import OpenAI
from datetime import timedelta

# Constants
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a"}

def format_time(seconds):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def transcribe_audio(api_key, audio_file):
    client = OpenAI(api_key=api_key)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        temp_audio_file.write(audio_file.read())
        temp_audio_file_path = temp_audio_file.name

    try:
        with open(temp_audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
                prompt="Yeh audio Hinglish mein hai. Hum Hindi bol rahe hain, lekin yeh sab Roman script mein likha gaya hai. Transcribe this audio into very short phrases or fragments. Each segment should be extremely brief, ideally no more than 2-3 words long. Break sentences into smaller parts if necessary.",
            )
    except Exception as e:
        if "Incorrect API key provided" in str(e):
            st.error("Invalid API key. Please check your OpenAI API key and try again.")
        else:
            st.error(f"An error occurred during transcription: {str(e)}")
        return None
    finally:
        os.unlink(temp_audio_file_path)

    return transcription

def generate_srt(transcription):
    srt_content = ""
    for i, segment in enumerate(transcription.segments, start=1):
        start_time = segment.start
        end_time = segment.end
        text = segment.text.strip()
        
        srt_content += f"{i}\n{format_time(start_time)} --> {format_time(end_time)}\n{text}\n\n"
    
    return srt_content

# Streamlit UI
st.set_page_config(page_title="Audio Transcription to SRT", page_icon="🎙️")

st.title("🎙️ Audio Transcription to SRT")
st.markdown("Created with ❤️ by Harjas Singh [Best Intern]")
st.markdown("""
This app allows you to transcribe audio files and generate SRT subtitles using OpenAI's API.

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
                    srt_content = generate_srt(transcription)
                    
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
                        for i, segment in enumerate(transcription.segments, start=1):
                            st.text(f"Segment {i}: Start = {segment.start:.2f}, End = {segment.end:.2f}, Duration = {segment.end - segment.start:.2f}")
                            if i < len(transcription.segments):
                                gap = transcription.segments[i].start - segment.end
                                st.text(f"Gap to next segment: {gap:.2f}")
                            st.text(f"Text: {segment.text.strip()}\n")

st.markdown("---")
