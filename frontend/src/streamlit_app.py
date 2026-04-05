import streamlit as st
import requests
import prometheus_client
from time import perf_counter

API_FRONTEND_REQUESTS_TOTAL = prometheus_client.Counter(
    'api_frontend_requests_total',
    'Total number of API requests made.'
)

LOCAL_FRONTEND_REQUESTS_TOTAL = prometheus_client.Counter(
    'local_frontend_requests_total',
    'Total number of local requests made.'
)

API_FRONTEND_ERRORS_TOTAL = prometheus_client.Counter(
    'api_frontend_errors_total',
    'Total number of API request errors occured in backend.'
)

LOCAL_FRONTEND_ERRORS_TOTAL = prometheus_client.Counter(
    'local_frontend_errors_total',
    'Total number of local request errors occured in backend.'
)

API_FRONTEND_REQUESTTIME_SECONDS = prometheus_client.Histogram(
    'api_frontend_requesttime_seconds',
    'Total time spent processing backend API requests.'
)

LOCAL_FRONTEND_REQUESTTIME_SECONDS = prometheus_client.Histogram(
    'local_frontend_requesttime_seconds',
    'Total time spent processing backend local requests.'
)


st.set_page_config(page_title="VLM Chat", page_icon=":robot_face:", layout="wide")
st.title("VLM Chat")

API_PORT = "22012"
API_SERVER = f"http://backend:{API_PORT}"
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
        req_start_time = perf_counter()
        st.chat_message("user").markdown(query)

        with st.spinner("Processing..."):
            # Convert chat history to a concatenated string 
            chat_history_str = "\n".join([f"{role}: {msg}" for role, msg in st.session_state.chat_history])
            
            if use_local_model:
                LOCAL_FRONTEND_REQUESTS_TOTAL.inc()
                response = requests.post(API_SERVER + "/api/generate-response-local", 
                files={"input_img": image}, 
                data={"query": query, "chat_history": chat_history_str}, timeout=HTTP_MAX_TIMEOUT_SECONDS)
            else:
                API_FRONTEND_REQUESTS_TOTAL.inc()
                response = requests.post(API_SERVER + "/api/generate-response-api", 
                files={"input_img": image}, 
                data={"query": query, "chat_history": chat_history_str}, timeout=HTTP_MAX_TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            st.chat_message("assistant").markdown(response.json()["response"])
            st.session_state.chat_history.append(("user", query))
            st.session_state.chat_history.append(("assistant", response.json()["response"]))
        else:
            if use_local_model:
                LOCAL_FRONTEND_ERRORS_TOTAL.inc()
            else:
                API_FRONTEND_ERRORS_TOTAL.inc()
            st.error(response.json().get("detail", "Unknown error"))
        
        if use_local_model:
            LOCAL_FRONTEND_REQUESTTIME_SECONDS.observe(perf_counter() - req_start_time)
        else:
            API_FRONTEND_REQUESTTIME_SECONDS.observe(perf_counter() - req_start_time)
        

@st.cache_resource
def start_server():
    prometheus_client.start_http_server(22013)
    return

start_server()


# streamlit run frontend/src/streamlit_app.py --server.port 7011 --server.address 0.0.0.0