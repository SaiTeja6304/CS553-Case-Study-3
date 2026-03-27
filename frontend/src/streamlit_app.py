import streamlit as st
import requests

st.set_page_config(page_title="VLM Chat", page_icon=":robot_face:", layout="wide")
st.title("VLM Chat")

API_PORT = "9011"
API_SERVER = f"http://paffenroth-23.dyn.wpi.edu:{API_PORT}"
HTTP_MAX_TIMEOUT_SECONDS = 2400

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

st.chat_message("assistant").markdown("I am a helpful chatbot to answer your questions about the uploaded image")
    
for role, msg in st.session_state.chat_history:
    st.chat_message(role).markdown(msg)

with st.sidebar:
    with st.expander("Model Selection"):
        use_local_model = st.checkbox("Use local model", value=False)
        st.info("Selecting local model will run the model locally (responses may take longer to generate).", icon="ℹ️")
    with st.expander("API Status", expanded=True):
        try:
            response = requests.get(API_SERVER + "/api/", timeout=10)
            if response.status_code == 200:
                st.info("VLM Chat API is running", icon="✅")
            else:
                st.error(f"VLM Chat API is not running: {response.json().get('detail', 'Unknown error')}", icon="❌")
        except Exception as e:
            st.error(f"VLM Chat API is not running: {e}", icon="❌")
        

image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
st.session_state.uploaded_image = image
if image is not None:
    st.image(image)
query = st.chat_input("Ask a question about the image")

if query:
    if st.session_state.uploaded_image is None:
        st.error("Please upload an image")
    else:
        st.chat_message("user").markdown(query)

        with st.spinner("Processing..."):
            # Convert chat history to a concatenated string 
            chat_history_str = "\n".join([f"{role}: {msg}" for role, msg in st.session_state.chat_history])
            
            if use_local_model:
                response = requests.post(API_SERVER + "/api/generate-response-local", 
                files={"input_img": image}, 
                data={"query": query, "chat_history": chat_history_str}, timeout=HTTP_MAX_TIMEOUT_SECONDS)
            else:
                response = requests.post(API_SERVER + "/api/generate-response-api", 
                files={"input_img": image}, 
                data={"query": query, "chat_history": chat_history_str}, timeout=HTTP_MAX_TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            st.chat_message("assistant").markdown(response.json()["response"])
            st.session_state.chat_history.append(("user", query))
            st.session_state.chat_history.append(("assistant", response.json()["response"]))
        else:
            st.error(response.json().get("detail", "Unknown error"))

# streamlit run frontend/src/streamlit_app.py --server.port 7011 --server.address 0.0.0.0