#!/bin/bash

set -eou pipefail

echo "Deploying frontend..."

echo "Setting up SSH"

USER="group11"
PORT="22000"
FRONTEND_PORT="7011"
HOST_ADDRESS="0.0.0.0"
SERVER="paffenroth-23.dyn.wpi.edu"
KEY_PATH="./ssh_keys/group_key"
LOCAL_DIR="./CS553-Case-Study-2/frontend/."
REMOTE_DIR="./CS553-Case-Study-2/frontend"

SCP_BASE=(scp -i "${KEY_PATH}" -P "${PORT}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
SSH_BASE=(ssh -i "${KEY_PATH}" -p "${PORT}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${USER}"@"${SERVER}")

echo "Copying frontend files to remote server..."

"${SSH_BASE[@]}" "rm -rf \"${REMOTE_DIR}\" && mkdir -p \"${REMOTE_DIR}\""
"${SCP_BASE[@]}" -r "${LOCAL_DIR}" "${USER}@${SERVER}:${REMOTE_DIR}"

echo "Installing miniconda..."

"${SSH_BASE[@]}" \
"sudo apt update && \
if [ ! -d \"\$HOME/miniconda3\" ]; then
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p \$HOME/miniconda3 && \
    rm /tmp/miniconda.sh
fi && \
sudo apt install -y tmux"

echo "Cleaning conda cache..."
"${SSH_BASE[@]}" \
"source \$HOME/miniconda3/etc/profile.d/conda.sh && \
conda clean --all -y"

echo "Creating conda environment and intalling libraries"

"${SSH_BASE[@]}" \
"source \$HOME/miniconda3/etc/profile.d/conda.sh && \
conda tos accept && \
conda env remove -y -n venv || true && \
conda create -y -n venv python=3.11 && \
conda activate venv && \
pip install --upgrade pip --no-cache-dir && \
pip install -r ${REMOTE_DIR}/requirements.txt --no-cache-dir"

echo "Starting frontend app"

"${SSH_BASE[@]}" bash -l << EOF
source \$HOME/miniconda3/etc/profile.d/conda.sh
sudo fuser -k ${FRONTEND_PORT}/tcp || true
sleep 1
tmux kill-session -t frontend-11 || true
sleep 1
tmux new-session -d -s frontend-11
tmux send-keys -t frontend-11 "source \$HOME/miniconda3/etc/profile.d/conda.sh && conda activate venv && cd ${REMOTE_DIR} && streamlit run src/streamlit_app.py --server.port ${FRONTEND_PORT} --server.address ${HOST_ADDRESS}" Enter
EOF

echo "Done"