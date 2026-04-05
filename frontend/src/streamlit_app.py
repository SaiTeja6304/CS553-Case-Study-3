import streamlit as st
import requests
import prometheus_client
from time import perf_counter

@st.cache_resource
def _start_prometheus_metrics_server(port: int = 33333) -> dict:
    """Bind once per process; Streamlit reruns the script on every interaction."""
    prometheus_client.start_http_server(port)

    return {
        "api_requests": prometheus_client.Counter(
            'api_frontend_requests_total', 'Total number of API requests made.'
        ),
        "local_requests": prometheus_client.Counter(
            'local_frontend_requests_total', 'Total number of local requests made.'
        ),
        "api_errors": prometheus_client.Counter(
            'api_frontend_errors_total', 'Total number of API request errors.'
        ),
        "local_errors": prometheus_client.Counter(
            'local_frontend_errors_total', 'Total number of local request errors.'
        ),
        "api_time": prometheus_client.Histogram(
            'api_frontend_requesttime_seconds', 'Time spent processing API requests.'
        ),
        "local_time": prometheus_client.Histogram(
            'local_frontend_requesttime_seconds', 'Time spent processing local requests.'
        )
    }


st.set_page_config(page_title="VLM Chat", page_icon=":robot_face:", layout="wide")
metrics = _start_prometheus_metrics_server()
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
                metrics["local_requests"].inc()
                response = requests.post(API_SERVER + "/api/generate-response-local", 
                files={"input_img": image}, 
                data={"query": query, "chat_history": chat_history_str}, timeout=HTTP_MAX_TIMEOUT_SECONDS)
            else:
                metrics["api_requests"].inc()
                response = requests.post(API_SERVER + "/api/generate-response-api", 
                files={"input_img": image}, 
                data={"query": query, "chat_history": chat_history_str}, timeout=HTTP_MAX_TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            st.chat_message("assistant").markdown(response.json()["response"])
            st.session_state.chat_history.append(("user", query))
            st.session_state.chat_history.append(("assistant", response.json()["response"]))
        else:
            if use_local_model:
                metrics["local_errors"].inc()
            else:
                metrics["api_errors"].inc()
            st.error(response.json().get("detail", "Unknown error"))
        
        if use_local_model:
            metrics["local_time"].observe(perf_counter() - req_start_time)
        else:
            metrics["api_time"].observe(perf_counter() - req_start_time)
