from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from app.prompts import DEFENSE_ASSISTANT_SYSTEM_PROMPT
from openai import OpenAI

def get_llm_client():
    

    client = OpenAI(
        api_key = DEEPSEEK_API_KEY,
        base_url = DEEPSEEK_BASE_URL,
    )
    
    return client,DEEPSEEK_MODEL

def chat_with_llm(user_message: str) -> str:
    
    client,model = get_llm_client()

    response = client.chat.completions.create(
        model = model,
        messages = [
            {"role":"system","content":DEFENSE_ASSISTANT_SYSTEM_PROMPT},
            {"role":"user","content":user_message},
        ],
        temperature = LLM_TEMPERATURE,
        max_tokens = LLM_MAX_TOKENS,
    )

    return response.choices[0].message.content