import os
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient

# Load environment variables
load_dotenv()

# Get configuration from environment
LLAMA_STACK_BASE_URL = os.getenv("LLAMA_STACK_BASE_URL", "http://localhost:8321")

# Initialize client
client = LlamaStackClient(base_url=LLAMA_STACK_BASE_URL)

# List all vector stores
print("Fetching vector stores...")
vector_stores = list(client.vector_stores.list())

if not vector_stores:
    print("No vector stores found.")
    exit(0)

print(f"\nFound {len(vector_stores)} vector store(s):")
print("-" * 80)
for i, vs in enumerate(vector_stores, 1):
    print(f"{i}. Name: {vs.name}")
    print(f"   ID: {vs.id}")
    print(f"   Created: {vs.created_at}")
    print()

# Delete options
print("Delete options:")
print("  1. Delete all vector stores")
print("  2. Delete by name pattern (e.g., 'hr-benefits-*')")
print("  3. Delete specific vector store by number")
print("  4. Cancel")
print()

choice = input("Enter choice (1-4): ").strip()

stores_to_delete = []

if choice == "1":
    confirm = input(f"Delete ALL {len(vector_stores)} vector store(s)? (yes/no): ").strip().lower()
    if confirm == "yes":
        stores_to_delete = vector_stores
    else:
        print("Cancelled.")
        exit(0)

elif choice == "2":
    pattern = input("Enter name pattern (e.g., 'hr-benefits'): ").strip()
    stores_to_delete = [vs for vs in vector_stores if pattern in vs.name]
    if stores_to_delete:
        print(f"\nMatching vector stores:")
        for vs in stores_to_delete:
            print(f"  - {vs.name} ({vs.id})")
        confirm = input(f"\nDelete {len(stores_to_delete)} vector store(s)? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            exit(0)
    else:
        print(f"No vector stores match pattern '{pattern}'")
        exit(0)

elif choice == "3":
    try:
        num = int(input(f"Enter number (1-{len(vector_stores)}): ").strip())
        if 1 <= num <= len(vector_stores):
            stores_to_delete = [vector_stores[num - 1]]
            print(f"\nSelected: {stores_to_delete[0].name} ({stores_to_delete[0].id})")
            confirm = input("Delete this vector store? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Cancelled.")
                exit(0)
        else:
            print("Invalid number.")
            exit(1)
    except ValueError:
        print("Invalid input.")
        exit(1)

elif choice == "4":
    print("Cancelled.")
    exit(0)

else:
    print("Invalid choice.")
    exit(1)

# Delete selected vector stores
print(f"\nDeleting {len(stores_to_delete)} vector store(s)...")
print("-" * 80)

for vs in stores_to_delete:
    try:
        client.vector_stores.delete(vector_store_id=vs.id)
        print(f"✓ Deleted: {vs.name} ({vs.id})")
    except Exception as e:
        print(f"✗ Failed to delete {vs.name}: {e}")

print("\nDone!")
