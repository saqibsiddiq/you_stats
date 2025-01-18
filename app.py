import streamlit as st
import subprocess
import psycopg2
import pandas as pd
import plotly.express as px

# Database connection settings
DB_CONN_STRING = os.getenv("DATABASE_URL")

def fetch_channel_data(channel_id):
    """
    Fetch channel data from the database.
    """
    try:
        conn = psycopg2.connect(DB_CONN_STRING)
        query = "SELECT * FROM youtube_channel WHERE channel_id = %s"
        df = pd.read_sql(query, conn, params=(channel_id,))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching channel data: {e}")
        return None

def fetch_video_data(channel_id):
    """
    Fetch video data for a channel from the database.
    """
    try:
        conn = psycopg2.connect(DB_CONN_STRING)
        query = "SELECT * FROM youtube_videos WHERE channel_id = %s"
        df = pd.read_sql(query, conn, params=(channel_id,))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching video data: {e}")
        return None

# Streamlit UI
st.title("YouTube Data Extraction")
st.write("Enter a YouTube channel homepage URL to fetch, save, and display its data.")

# Input field for YouTube URL
url = st.text_input("YouTube Channel URL", placeholder="https://www.youtube.com/@ExampleHandle")

# Initialize session state variables
if 'channel_id' not in st.session_state:
    st.session_state.channel_id = None

# Button to trigger extraction
if st.button("Fetch, Save, and Display Data"):
    if url:
        try:
            # Step 1: Run extract_id.py with the provided URL
            extract_process = subprocess.run(
                ["python", "extract_id.py"],
                input=url,
                text=True,
                capture_output=True
            )
            output = extract_process.stdout
            
            st.write("Extract ID Output:")
            st.code(output)

            # Check if the extraction was successful
            if "Resolved Channel ID" in output:
                # Extract channel ID from the output
                channel_id_line = [line for line in output.split("\n") if "Resolved Channel ID" in line]
                channel_id = channel_id_line[0].split(":")[-1].strip()
                st.session_state.channel_id = channel_id
                
                # Step 2: Run main.py with the resolved channel ID
                main_process = subprocess.run(
                    ["python", "main.py", channel_id],
                    capture_output=True,
                    text=True
                )
                main_output = main_process.stdout
                
                st.write("Main Script Output:")
                st.code(main_output)

                # Fetch and display data
                st.write("### Channel Information")
                channel_data = fetch_channel_data(channel_id)
                if channel_data is not None and not channel_data.empty:
                    st.dataframe(channel_data)
                else:
                    st.write("No channel data found.")

                st.write("### Videos Information")
                video_data = fetch_video_data(channel_id)
                if video_data is not None and not video_data.empty:
                    st.dataframe(video_data)

                    # Create graphs for views, likes, and comments
                    st.sidebar.title("Graph Options")
                    selected_metric = st.sidebar.radio(
                        "Select a metric to visualize:",
                        ("Views", "Likes", "Comments")
                    )

                    # Convert publish_date to datetime for plotting
                    video_data['publish_date'] = pd.to_datetime(video_data['publish_date'])

                    # Plot based on selected metric
                    fig = None
                    if selected_metric == "Views":
                        fig = px.line(video_data, x="publish_date", y="views", title="Video Views Over Time")
                    elif selected_metric == "Likes":
                        fig = px.line(video_data, x="publish_date", y="likes", title="Video Likes Over Time")
                    elif selected_metric == "Comments":
                        fig = px.line(video_data, x="publish_date", y="comments", title="Video Comments Over Time")

                    if fig is not None:
                        st.plotly_chart(fig)
                    else:
                        st.write("No video data found.")
                else:
                    st.write("No video data found.")

                st.success("Data has been successfully fetched, stored, and displayed!")

            else:
                st.error("Failed to resolve the channel ID. Please check the URL.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Please enter a valid YouTube URL.")

