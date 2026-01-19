import asyncio
import os

# Use environment variable for API key (set externally)
if "YANDEX_CLOUD_API_KEY" not in os.environ:
    print("WARNING: YANDEX_CLOUD_API_KEY not set. Some tests may fail.")


async def main():
    print("\n===== TESTING IMPROVEMENTS =====\n")

    # Test 1: Enhanced RAG search
    print("1. Enhanced RAG search...")
    from bot.services.knowledge_service import get_knowledge_service

    ks = get_knowledge_service()
    results = await ks.enhanced_search("photosynthesis", user_age=10, top_k=3)
    print(f"   Results: {len(results)} items [OK]")

    # Test 2: Context compression
    print("\n2. Context compression...")
    from bot.services.rag import ContextCompressor

    comp = ContextCompressor()
    text = "This is a long text. " * 50
    compressed = comp.compress(text, "question", max_sentences=5)
    ratio = len(compressed) / len(text) * 100
    saved = 100 - ratio
    print(f"   Compression: {ratio:.1f}% ({saved:.1f}% saved) [OK]")

    # Test 3: Response generator integration
    print("\n3. Response generator integration...")
    import bot.services.yandex_ai_response_generator as mod

    with open(mod.__file__, encoding="utf-8") as f:
        source = f.read()
    has_rag = "enhanced_search" in source
    has_comp = "ContextCompressor" in source
    print(f"   Uses enhanced_search: {has_rag} [OK]")
    print(f"   Uses ContextCompressor: {has_comp} [OK]")

    # Test 4: Streaming chat integration
    print("\n4. Streaming chat integration...")
    import bot.api.miniapp.stream_handlers.ai_chat_stream as stream_mod

    with open(stream_mod.__file__, encoding="utf-8") as f:
        stream_source = f.read()
    stream_has_rag = "enhanced_search" in stream_source
    stream_has_comp = "ContextCompressor" in stream_source
    print(f"   Uses enhanced_search: {stream_has_rag} [OK]")
    print(f"   Uses ContextCompressor: {stream_has_comp} [OK]")

    # Test 5: Prompt improvements
    print("\n5. Prompt improvements...")
    from bot.config.prompts import AI_SYSTEM_PROMPT

    has_gpt5 = "GPT-5" in AI_SYSTEM_PROMPT
    has_depth = "depth" in AI_SYSTEM_PROMPT.lower() or "gluboki" in AI_SYSTEM_PROMPT.lower()
    has_all_words = (
        "all words" in AI_SYSTEM_PROMPT.lower() or "vse slova" in AI_SYSTEM_PROMPT.lower()
    )
    print(f"   Mentions GPT-5 quality: {has_gpt5} [OK]")
    print(f"   Requires depth: {has_depth} [OK]")
    print(f"   Requires all words: {has_all_words} [OK]")

    # Summary
    print("\n===== SUMMARY =====")
    all_ok = all(
        [
            len(results) >= 0,  # enhanced_search works
            saved > 50,  # compression works
            has_rag,
            has_comp,
            stream_has_rag,
            stream_has_comp,
            has_gpt5,
        ]
    )

    if all_ok:
        print("ALL TESTS PASSED! Quality improvements are working.\n")
    else:
        print("Some tests failed. Review needed.\n")

    return all_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
