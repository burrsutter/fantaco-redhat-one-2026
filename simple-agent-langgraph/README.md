# LangGraph -> Llama Stack -> MCP Server

This project builds up to using LangGraph clients that connect THROUGH Llama Stack into MCP Servers.  

## Setup
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Follow the numbers

The goal is to arrive at a basic Agent that accepts an email address and finds the orders for that customer.

```
python 7_langgraph_client_list_orders_any_customer.py <email-address>
```

Database includes:
franwilson@example.com
thomashardy@example.com
liuwong@example.com


The reason this is tricky is because the orders database uses a "customer_id" which is first discovered by going to the customer database to find the customer_id by searching for the contact_email address.

## Find all orders for <email address>
```bash
python 7_langgraph_client_list_orders_any_customer.py thomashardy@example.com
```

## Find all invoices for <email address>

```bash
python 8_langgraph_client_list_invoices_any_customer.py thomashardy@example.com
```

## Fast API version 

```bash
python 9_langgraph_fastapi.py
```

```bash
open http://localhost:8000/docs
```

```bash
curl -sS "http://localhost:8000/find_orders?email=thomashardy@example.com" | jq
curl -sS "http://localhost:8000/find_invoices?email=liuwong@example.com" | jq
```




