#!/bin/bash
echo "This script cleans out the local Llama Stack distribution directory.  This will delete the MCP server registrations and other state."
echo "Are you sure you want to proceed? (y/n)"
read -n 1 -s sure
if [ "$sure" != "y" ]; then
    echo "Aborting..."
    exit 1
fi
rm -rf ~/.llama/distributions/
echo "Llama Stack distribution directory cleaned out"