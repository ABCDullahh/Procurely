"""Test script to verify Gemini models work correctly."""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.llm.gemini import GeminiProvider
from app.services.llm.base import LLMConfig


async def test_model(api_key: str, model_name: str):
    """Test a single Gemini model."""
    print(f"\nTesting {model_name}...")
    provider = GeminiProvider(api_key, default_model=model_name)

    try:
        # Simple test prompt
        response = await provider.complete_text(
            "Say 'Hello' in exactly one word.",
            config=LLMConfig(model=model_name, temperature=0.1, max_tokens=50)
        )
        print(f"  SUCCESS: Got response: '{response.content[:100]}'")
        print(f"  Tokens: {response.total_tokens}")
        await provider.close()
        return True
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        await provider.close()
        return False


async def test_json_extraction(api_key: str, model_name: str):
    """Test JSON extraction."""
    print(f"\nTesting JSON extraction with {model_name}...")
    provider = GeminiProvider(api_key, default_model=model_name)

    try:
        result = await provider.extract_json(
            "Extract info: Company name is 'Acme Corp', founded in 2020, location 'Jakarta'",
            schema_hint='{"name": "string", "year": "number", "location": "string"}',
            config=LLMConfig(model=model_name, temperature=0.1, max_tokens=200)
        )
        print(f"  SUCCESS: Got JSON: {result}")
        await provider.close()
        return True
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        await provider.close()
        return False


async def main():
    # Get API key from environment or database
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        # Try to get from database
        try:
            # Load .env first
            from dotenv import load_dotenv
            load_dotenv()

            from app.core.database import SessionLocal
            from app.models.api_key import ApiKey
            from app.core.security import decrypt_api_key

            db = SessionLocal()
            # API key is stored under provider "GEMINI"
            key_record = db.query(ApiKey).filter(ApiKey.provider == "GEMINI").first()
            if key_record:
                # decrypt_api_key only takes encrypted_value, uses settings internally
                api_key = decrypt_api_key(key_record.encrypted_value)
                print(f"Using API key from database (GEMINI)")
            db.close()
        except Exception as e:
            print(f"Could not get API key from database: {e}")
            import traceback
            traceback.print_exc()

    if not api_key:
        print("ERROR: No GEMINI_API_KEY found. Set environment variable or check database.")
        return

    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")

    # Models to test
    models = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    results = {}

    # Test basic completion
    print("\n" + "="*60)
    print("TESTING BASIC COMPLETION")
    print("="*60)

    for model in models:
        results[model] = await test_model(api_key, model)

    # Test JSON extraction with working models
    print("\n" + "="*60)
    print("TESTING JSON EXTRACTION")
    print("="*60)

    working_models = [m for m, success in results.items() if success]
    for model in working_models[:2]:  # Test first 2 working models
        await test_json_extraction(api_key, model)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for model, success in results.items():
        status = "✓ WORKS" if success else "✗ FAILED"
        print(f"  {model}: {status}")

    working = [m for m, s in results.items() if s]
    print(f"\nWorking models: {working}")

    if "gemini-2.5-pro" in working:
        print("\n✓ gemini-2.5-pro is working! Recommended for production.")
    elif working:
        print(f"\nRecommended model: {working[0]}")


if __name__ == "__main__":
    asyncio.run(main())
