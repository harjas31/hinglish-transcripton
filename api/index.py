from subprocess import Popen
import os
from pathlib import Path

def init_streamlit():
    # Get the root directory (parent of /api)
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent
    
    # Path to your main Streamlit app file
    streamlit_script = str(root_dir / "app.py")
    
    # Command to run Streamlit with proper server settings
    cmd = [
        "streamlit", "run",
        streamlit_script,
        "--server.address", "0.0.0.0",
        "--server.port", "8501",
        "--server.fileWatcherType", "none",
        "--server.baseUrlPath", "",  # Important for Vercel subdirectory deployment
        "--browser.serverAddress", "0.0.0.0",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--theme.base", "light"  # Optional: Set theme
    ]
    
    # Additional environment variables for Streamlit
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_dir)  # Add root dir to Python path
    
    # Start Streamlit process
    process = Popen(cmd, env=env)
    
    # Wait for the process to complete
    process.wait()

# Start the Streamlit application
if __name__ == "__main__":
    init_streamlit()
