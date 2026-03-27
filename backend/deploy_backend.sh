#!/bin/bash

set -eou pipefail

echo "Deploying backend..."

echo "Setting up SSH"

USER="group11"
PORT="22011"
BACKEND_PORT="9011"
HOST_ADDRESS="0.0.0.0"
SERVER="paffenroth-23.dyn.wpi.edu"
KEY_PATH="./ssh_keys/secure_key"
LOCAL_DIR="./CS553-Case-Study-2/backend/."
REMOTE_DIR="./CS553-Case-Study-2/backend"

SCP_BASE=(scp -i "${KEY_PATH}" -P "${PORT}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
SSH_BASE=(ssh -i "${KEY_PATH}" -p "${PORT}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${USER}"@"${SERVER}")

echo "Copying backend files to remote server..."

"${SSH_BASE[@]}" "rm -rf \"${REMOTE_DIR}\" && mkdir -p \"${REMOTE_DIR}\""
"${SCP_BASE[@]}" -r "${LOCAL_DIR}" "${USER}@${SERVER}:${REMOTE_DIR}"
"${SCP_BASE[@]}" "./CS553-Case-Study-2/backend/.env" "${USER}@${SERVER}:${REMOTE_DIR}/"

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

echo "Starting backend app"

"${SSH_BASE[@]}" bash -l << EOF
source \$HOME/miniconda3/etc/profile.d/conda.sh
pkill -f "uvicorn src.app:app" || true
sleep 2
sudo fuser -k ${BACKEND_PORT}/tcp || true
sleep 1
tmux kill-session -t backend-11 || true
sleep 1
tmux new-session -d -s backend-11
tmux send-keys -t backend-11 "source \$HOME/miniconda3/etc/profile.d/conda.sh && conda activate venv && cd ${REMOTE_DIR} && uvicorn src.app:app --host ${HOST_ADDRESS} --port ${BACKEND_PORT}" Enter
EOF

echo "Done"