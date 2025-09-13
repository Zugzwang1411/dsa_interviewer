import re
import asyncio
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
from .config import get_config

def create_chain(prompt_template_string):
    config = get_config()
    
    llm = OpenAI(
        temperature=0.4,
        openai_api_key=config.get('OPENAI_API_KEY'),
        model_name=config.get('LLM_MODEL', 'gpt-3.5-turbo-instruct')
    )
    
    prompt = PromptTemplate(
        input_variables=list(re.findall(r'\{(\w+)\}', prompt_template_string)),
        template=prompt_template_string
    )
    
    return prompt | llm

async def run_chain(chain, inputs, stream=False):
    loop = asyncio.get_event_loop()
    
    try:
        result = await loop.run_in_executor(None, lambda: chain.invoke(inputs))
        print(f"🔍 Backend: run_chain result type: {type(result)}, value: {str(result)[:100]}...")
        return result
    except Exception as e:
        print(f"🔍 Backend: run_chain error: {e}")
        raise e

def parse_analysis(raw_text):
    score_match = re.search(r'SCORE:\s*(\d+)', raw_text)
    concepts_covered_match = re.search(r'CONCEPTS_COVERED:\s*([^\n]*)', raw_text)
    missing_concepts_match = re.search(r'MISSING_CONCEPTS:\s*([^\n]*)', raw_text)
    quality_match = re.search(r'QUALITY:\s*([^\n]*)', raw_text)
    depth_match = re.search(r'DEPTH:\s*([^\n]*)', raw_text)
    detailed_analysis_match = re.search(r'DETAILED_ANALYSIS:\s*([^\n]*)', raw_text)
    
    score = int(score_match.group(1)) if score_match else 5
    concepts_covered_str = concepts_covered_match.group(1).strip() if concepts_covered_match else "none"
    missing_concepts_str = missing_concepts_match.group(1).strip() if missing_concepts_match else "none"
    quality = quality_match.group(1).strip() if quality_match else "fair"
    depth = depth_match.group(1).strip() if depth_match else "adequate"
    detailed_analysis = detailed_analysis_match.group(1).strip() if detailed_analysis_match else "Analysis unavailable."
    
    concepts_covered = [c.strip() for c in concepts_covered_str.split(',')] if concepts_covered_str != "none" else []
    missing_concepts = [c.strip() for c in missing_concepts_str.split(',')] if missing_concepts_str != "none" else []
    
    return {
        "raw_analysis": raw_text,
        "score": score,
        "normalized_score": score / 10.0,
        "concepts_covered": concepts_covered,
        "missing_concepts": missing_concepts,
        "quality": quality,
        "depth": depth,
        "detailed_analysis": detailed_analysis
    }

def fallback_scoring(answer, key_concepts=""):
    word_count = len(answer.split())
    fallback_score = min(8, max(2, word_count // 10))
    
    return {
        "raw_analysis": f"Analysis temporarily unavailable. Using fallback scoring.",
        "score": fallback_score,
        "normalized_score": fallback_score / 10.0,
        "concepts_covered": [],
        "missing_concepts": [key_concepts] if key_concepts else [],
        "quality": "fair",
        "depth": "shallow",
        "detailed_analysis": f"Based on answer length ({word_count} words), more detail is needed."
    }
