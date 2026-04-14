"""
Script to send ingestion requests to the storage microservice API.

Reads all JSON files from the 'data' folder and sends POST requests
to http://localhost:8072/ingest with the JSON data as the request body.
Uses httpx for async HTTP requests and sends all requests in parallel.
"""

import asyncio
import json
from pathlib import Path

import httpx


async def send_ingest_request(client: httpx.AsyncClient, json_file_path: str) -> None:
    """
    Load a JSON file and send it as a POST request to the ingest endpoint.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        response = await client.post(
            '/ingest',
            json=data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code in (200, 201):
            print(f"✓ Successfully ingested: {json_file_path}")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Failed to ingest: {json_file_path}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")

    except Exception as e:
        print(f"✗ Error processing {json_file_path}: {str(e)}")


async def main():
    """
    Find all JSON files in the 'data' folder and send ingest requests in parallel.
    """
    data_folder = Path('data')

    if not data_folder.exists():
        print("Error: 'data' folder not found in the current directory.")
        return

    json_files = list(data_folder.glob('*.json'))

    if not json_files:
        print("No JSON files found in the 'data' folder.")
        return

    print(f"Found {len(json_files)} JSON files. Sending ingest requests in parallel...")

    async with httpx.AsyncClient(base_url='http://localhost:8072') as client:
        tasks = [
            send_ingest_request(client, str(json_file))
            for json_file in json_files
        ]
        await asyncio.gather(*tasks)

    print("All requests sent.")


if __name__ == "__main__":
    asyncio.run(main())