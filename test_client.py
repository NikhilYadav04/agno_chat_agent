import asyncio
import httpx
import sys


async def test_streaming_query(user_id: str, message: str, file_path: str = None):
    url = "http://localhost:8000/query"

    data = {"token": user_id, "user_message": message}

    files = {}
    if file_path:
        files = {"file": open(file_path, "rb")}

    print(f"--- Sending Query: {message} ---")
    print(f"--- Streaming Response ---")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream("POST", url, data=data, files=files) as response:
                if response.status_code != 200:
                    print(f"Error: {response.status_code}")
                    print(await response.aread())
                    return

                async for chunk in response.aiter_text():
                    print(chunk, end="", flush=True)
                print("\n\n--- Stream Completed ---")
        except Exception as e:
            print(f"\nConnection Error: {e}")
        finally:
            if file_path:
                files["file"].close()


async def main():
    # Example Usage
    user_id = "test_user_123"
    message = "blood rpessure and oxygen relevls? ? \n The token is eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2OTQ3ZTI2ZmQ4YmM5YmRhZGQ2NzJhY2EiLCJpYXQiOjE3NzMxNzU0NzAsImV4cCI6MTc3Mzc4MDI3MH0.2vLIodZXQ7UfraCHg2pb7REew-a7FWWbI7ZfhNzV7kg"

    # You can pass a file path here if you have a PDF to test
    # file_path = "path/to/your/document.pdf"
    file_path = ""

    await test_streaming_query(user_id, message, file_path)


if __name__ == "__main__":
    asyncio.run(main())
