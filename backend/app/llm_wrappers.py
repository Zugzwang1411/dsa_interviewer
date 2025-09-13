import re
import asyncio
import logging
from typing import Dict, List, Any, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMService:
    """Service class for managing LLM operations with enhanced error handling and caching"""
    
    def __init__(self):
        self.config = Config()
        self._llm_cache = {}
        
    def _get_llm(self, model_name: Optional[str] = None) -> OpenAI:
        """Get or create LLM instance with caching"""
        model = model_name or self.config.LLM_MODEL
        
        if model not in self._llm_cache:
            self._llm_cache[model] = OpenAI(
                temperature=self.config.LLM_TEMPERATURE,
                openai_api_key=self.config.OPENAI_API_KEY,
                model_name=model
            )
            logger.info(f"Created new LLM instance for model: {model}")
        
        return self._llm_cache[model]
    
    def create_chain(self, prompt_template_string: str, model_name: Optional[str] = None):
        """Create a LangChain chain with the given prompt template"""
        try:
            llm = self._get_llm(model_name)
            
            # Extract input variables from template
            input_variables = list(re.findall(r'\{(\w+)\}', prompt_template_string))
            
            prompt = PromptTemplate(
                input_variables=input_variables,
                template=prompt_template_string
            )
            
            logger.info(f"Created chain with {len(input_variables)} input variables")
            return prompt | llm
            
        except Exception as e:
            logger.error(f"Failed to create chain: {e}")
            raise

# Global service instance
llm_service = LLMService()

def create_chain(prompt_template_string: str, model_name: Optional[str] = None):
    """Legacy function for backward compatibility"""
    return llm_service.create_chain(prompt_template_string, model_name)

async def run_chain(chain, inputs: Dict[str, Any], stream: bool = False) -> str:
    """Run a LangChain chain asynchronously with enhanced error handling"""
    loop = asyncio.get_event_loop()
    
    try:
        logger.info(f"Running chain with inputs: {list(inputs.keys())}")
        result = await loop.run_in_executor(None, lambda: chain.invoke(inputs))
        
        # Ensure result is a string
        if isinstance(result, str):
            logger.info(f"Chain result length: {len(result)} characters")
            return result
        else:
            logger.warning(f"Unexpected result type: {type(result)}, converting to string")
            return str(result)
            
    except Exception as e:
        logger.error(f"Chain execution failed: {e}")
        raise e

def parse_analysis(raw_text: str) -> Dict[str, Any]:
    """Parse structured analysis response from LLM with enhanced error handling"""
    try:
        # Extract all required fields using regex
        score_match = re.search(r'SCORE:\s*(\d+)', raw_text)
        concepts_covered_match = re.search(r'CONCEPTS_COVERED:\s*([^\n]*)', raw_text)
        missing_concepts_match = re.search(r'MISSING_CONCEPTS:\s*([^\n]*)', raw_text)
        quality_match = re.search(r'QUALITY:\s*([^\n]*)', raw_text)
        depth_match = re.search(r'DEPTH:\s*([^\n]*)', raw_text)
        detailed_analysis_match = re.search(r'DETAILED_ANALYSIS:\s*([^\n]*)', raw_text)
        
        # Parse with fallbacks
        score = int(score_match.group(1)) if score_match else 5
        concepts_covered_str = concepts_covered_match.group(1).strip() if concepts_covered_match else "none"
        missing_concepts_str = missing_concepts_match.group(1).strip() if missing_concepts_match else "none"
        quality = quality_match.group(1).strip() if quality_match else "fair"
        depth = depth_match.group(1).strip() if depth_match else "adequate"
        detailed_analysis = detailed_analysis_match.group(1).strip() if detailed_analysis_match else "Analysis unavailable."
        
        # Process concept lists
        concepts_covered = [c.strip() for c in concepts_covered_str.split(',')] if concepts_covered_str != "none" else []
        missing_concepts = [c.strip() for c in missing_concepts_str.split(',')] if missing_concepts_str != "none" else []
        
        logger.info(f"Parsed analysis: score={score}, quality={quality}, depth={depth}")
        
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
        
    except Exception as e:
        logger.error(f"Failed to parse analysis: {e}")
        return fallback_scoring("", "")

def fallback_scoring(answer: str, key_concepts: str = "") -> Dict[str, Any]:
    """Provide fallback scoring when LLM analysis fails"""
    word_count = len(answer.split())
    fallback_score = min(8, max(2, word_count // 10))
    
    logger.warning(f"Using fallback scoring for answer with {word_count} words")
    
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
