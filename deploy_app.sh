# SSH Setup Script

#!/bin/bash
set -euo pipefail

# Define constants

USER="group11"
PORT="22011"
SERVER="paffenroth-23.dyn.wpi.edu"
PUB_KEY_PATH="./ssh_keys/group_key"
SECURE_KEY_NAME="secure_key"
REPO="https://github.com/SaiTeja6304/CS553-Case-Study-2.git"
REPO_DIR="CS553-Case-Study-2"
echo "$USER" "$PORT" "$SERVER" "$PUB_KEY_PATH" "$SECURE_KEY_NAME"

# Move to the script's directory
cd "$(dirname "$0")"
ls

# Set initial SSH key permissions
chmod 600 "$PUB_KEY_PATH"
ls -l "$PUB_KEY_PATH"

# Setup SSH command
SSH_BASE=(ssh -i "$PUB_KEY_PATH" -p "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "${USER}@${SERVER}")
echo "${SSH_BASE[@]}"

# Store public key
SECURE_PUB_KEY_CONTENT="$(cat "./ssh_keys/${SECURE_KEY_NAME}.pub")"
echo "$SECURE_PUB_KEY_CONTENT"

# Replace authorized keys with secure key

if "${SSH_BASE[@]}" "exit" 2>/dev/null; then
    echo "used group key to ssh"

    "${SSH_BASE[@]}" \
    "echo $SECURE_PUB_KEY_CONTENT > ~/.ssh/authorized_keys"

    echo "swapped keys"
else
    echo "group key denied, using secure key"
fi

# Try connecting via new key
SSH_BASE[2]="./ssh_keys/${SECURE_KEY_NAME}"
if ! "${SSH_BASE[@]}" "cat ~/.ssh/authorized_keys"; then
    exit 1
else
    echo "successfully connected with secure key"
fi

#update the repo, break if there are any changes (there shouldnt be on the linux server tho)
git -C "$REPO_DIR" pull --ff-only

#deploy backend
bash "./$REPO_DIR/backend/deploy_backend.sh"

#deploy frontend
bash "./$REPO_DIR/frontend/deploy_frontend.sh"