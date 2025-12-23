#!/usr/bin/env python3
"""
Test client for Thomas Hardy customer query
Tests the LangGraph + Langfuse API with MCP tool integration
Query: "who does Thomas Hardy work for?"
Expected: Answer should include "Around the Horn", customer ID "AROUT", and city "London"
"""

import httpx
import json
import sys
from datetime import datetime


# Hard-coded test query
TEST_QUERY = "who does Thomas Hardy work for?"

# Expected values in the response
EXPECTED_COMPANY = "Around the Horn"
EXPECTED_CUSTOMER_ID = "AROUT"
EXPECTED_CITY = "London"


def validate_response(response_message: str) -> dict:
    """
    Validate that the response contains expected information about Thomas Hardy.

    Args:
        response_message: The AI's response message

    Returns:
        Dictionary with validation results
    """
    results = {
        "company_found": EXPECTED_COMPANY in response_message,
        "customer_id_found": EXPECTED_CUSTOMER_ID in response_message,
        "city_found": EXPECTED_CITY in response_message,
        "all_passed": False
    }

    results["all_passed"] = (
        results["company_found"] and
        results["customer_id_found"] and
        results["city_found"]
    )

    return results


def test_thomas_hardy(base_url: str = "http://localhost:8002"):
    """
    Test the API with Thomas Hardy query and validate the response.

    Args:
        base_url: Base URL of the API (default: http://localhost:8002)
    """

    # Prepare the request
    url = f"{base_url}/api/v1/chat"
    payload = {
        "message": TEST_QUERY,
        "user_id": "test-user",
        "session_id": f"test-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    }

    print("=" * 80)
    print("🚀 Testing Thomas Hardy Customer Query")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Query: {TEST_QUERY}")
    print()
    print("Expected in response:")
    print(f"  ✓ Company Name: {EXPECTED_COMPANY}")
    print(f"  ✓ Customer ID: {EXPECTED_CUSTOMER_ID}")
    print(f"  ✓ City: {EXPECTED_CITY}")
    print("=" * 80)
    print()

    try:
        # Make the request
        print("📤 Sending request...")
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()

            # Parse response
            result = response.json()
            ai_message = result.get('message', '')

            print("✅ Response received!")
            print("=" * 80)
            print("📋 Response Details:")
            print("=" * 80)
            print(f"Session ID: {result.get('session_id')}")
            print(f"User ID: {result.get('user_id')}")
            print()
            print("💬 AI Response:")
            print("-" * 80)
            print(ai_message)
            print("-" * 80)
            print()

            # Validate the response
            print("🔍 Validating Response...")
            print("=" * 80)
            validation = validate_response(ai_message)

            # Display validation results
            status_icon_company = "✅" if validation["company_found"] else "❌"
            status_icon_id = "✅" if validation["customer_id_found"] else "❌"
            status_icon_city = "✅" if validation["city_found"] else "❌"

            print(f"{status_icon_company} Company Name '{EXPECTED_COMPANY}': {'FOUND' if validation['company_found'] else 'NOT FOUND'}")
            print(f"{status_icon_id} Customer ID '{EXPECTED_CUSTOMER_ID}': {'FOUND' if validation['customer_id_found'] else 'NOT FOUND'}")
            print(f"{status_icon_city} City '{EXPECTED_CITY}': {'FOUND' if validation['city_found'] else 'NOT FOUND'}")
            print("=" * 80)
            print()

            # Final result
            if validation["all_passed"]:
                print("🎉 TEST PASSED! All expected values found in response.")
                print()
                print("💡 Next steps:")
                print("  1. Check the Langfuse dashboard to see the trace")
                print("  2. Verify that the search_customers MCP tool was called")
                print("  3. Review the tool parameters and results")
                print()
                return 0
            else:
                print("❌ TEST FAILED! Some expected values were not found.")
                print()
                print("📊 Full Response JSON:")
                print(json.dumps(result, indent=2))
                print()
                print("💡 Debugging tips:")
                print("  1. Check if the Customer MCP server is running")
                print("  2. Verify the MCP server is returning correct data")
                print("  3. Check the Langfuse trace for errors")
                print("  4. Review the tool execution logs")
                print()
                return 1

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return 1

    except httpx.ConnectError:
        print(f"❌ Connection Error: Could not connect to {base_url}")
        print("Make sure the server is running!")
        print()
        print("To start the server, run:")
        print("  cd backend")
        print("  python main.py")
        print()
        return 1

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main function to run the test."""
    print()
    print("🧪 Thomas Hardy Customer Query Test")
    print(f"Query: {TEST_QUERY}")
    print()

    exit_code = test_thomas_hardy()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
