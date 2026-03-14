from chains.summarizer import summarize
from agents.search_agent import run_search_agent

def test_model(model_name):
    print(f"\n{'='*50}")
    print(f"Testing model: {model_name}")
    print('='*50)
    
    query = "Latest advances in AI agents"
    results = run_search_agent(query)
    
    content = ""
    for r in results["results"][:2]:  # Just use first 2 results for testing
        content += r["content"] + "\n"
    
    # Override the model temporarily
    from langchain_openai import ChatOpenAI
    from config import OPENAI_API_KEY
    import chains.summarizer
    chains.summarizer.llm = ChatOpenAI(model=model_name, api_key=OPENAI_API_KEY)
    
    summary = summarize(content)
    print(f"Summary length: {len(summary)} chars")
    print(f"Preview: {summary[:200]}...")

# Test different models
models_to_test = ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"]
for model in models_to_test:
    test_model(model)