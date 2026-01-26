#!/bin/bash
# Source this file to set CUSTOMER_MCP_SERVER_URL and FINANCE_MCP_SERVER_URL environment variables
# Usage: source export_customer_finance_mcp_urls.sh

export CUSTOMER_MCP_SERVER_URL=https://$(oc get routes -l app=mcp-customer -o jsonpath="{range .items[*]}{.status.ingress[0].host}{end}")/mcp
echo "CUSTOMER_MCP_SERVER_URL=$CUSTOMER_MCP_SERVER_URL"

export FINANCE_MCP_SERVER_URL=https://$(oc get routes -l app=mcp-finance -o jsonpath="{range .items[*]}{.status.ingress[0].host}{end}")/mcp
echo "FINANCE_MCP_SERVER_URL=$FINANCE_MCP_SERVER_URL"
