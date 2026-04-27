from llama_cpp import Llama
from .config import settings

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = Llama(
            model_path=settings.LLM_MODEL_PATH,
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )
    return _llm

def generate_response(prompt: str) -> str:
    llm = get_llm()
    
    # Формат для Saiga (инструкция)
    formatted_prompt = f"""<s>Вопрос: {prompt}

Ответ:"""
    
    output = llm(
        formatted_prompt,
        max_tokens=512,
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
        stop=["</s>", "Вопрос:", "\n\n\n"],
        echo=False
    )
    result = output["choices"][0]["text"].strip()
    
    # Очистка от мусора
    if result.startswith("Ответ:"):
        result = result[6:].strip()
    
    if not result or len(result) < 3:
        return "Я не уверен в ответе. Пожалуйста, переформулируйте вопрос."
    
    return result