#!/bin/bash

# Function to open terminal windows and run Python script
open_terminals() {
    local num_windows=$1
    local python_script="client.py"
    local terminal_emulator="gnome-terminal"

    for ((i = 0; i < num_windows; i++)); do
        $terminal_emulator -- bash -c "python3 $python_script $i; exec bash" &
    done
}

# Check if arguments are provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <number of terminals>"
    exit 1
fi

# Check if the first argument is a valid number
if ! [[ $1 =~ ^[0-9]+$ ]]; then
    echo "Error: Please provide a valid number of terminals."
    exit 1
fi

# Open the specified number of terminal windows and run the Python script
open_terminals $1

exit 0
