import asyncio

from app.llm.ollama_client import generate_response


async def main():
    prompt = "Explain prompt injection in two sentences."

    response = await generate_response(prompt)

    print("\n========== OLLAMA RESPONSE ==========")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())