import chainlit as cl
from langchain_huggingface import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import pipeline
from langchain.llms import OpenAI
import re
from datetime import datetime
import random

class LLMPoweredInterviewer:
    def __init__(self):
        self.llm = OpenAI(temperature=0.4)
        
        # Initialize interview state
        self.reset_interview()
        
        # Question bank with expected concepts
        self.questions = [
            {
                "id": 1,
                "question": "What's the difference between arrays and linked lists? When would you use each?",
                "key_concepts": "arrays, linked lists, time complexity, memory access, use cases",
                "difficulty": "medium",
                "follow_ups": [
                    "Can you explain the time complexity of insertions in both?",
                    "How does cache performance differ between arrays and linked lists?",
                    "When would you prefer a linked list over an array for dynamic data?"
                ]
            },
            {
                "id": 2,
                "question": "How would you detect a cycle in a linked list?",
                "key_concepts": "cycle detection, Floyd's algorithm, two pointers, time complexity",
                "difficulty": "medium",
                "follow_ups": [
                    "Can you describe Floyd's tortoise and hare algorithm in detail?",
                    "What is the time and space complexity of your approach?",
                    "How would you find the start of the cycle?"
                ]
            },
            {
                "id": 3,
                "question": "Explain binary search and its time complexity.",
                "key_concepts": "binary search, sorted array, O(log n), divide and conquer",
                "difficulty": "easy",
                "follow_ups": [
                    "What happens if the array is not sorted?",
                    "Can you implement binary search recursively?",
                    "How does binary search handle duplicate elements?"
                ]
            },
            {
                "id": 4,
                "question": "What is dynamic programming? Give an example.",
                "key_concepts": "dynamic programming, memoization, overlapping subproblems, optimization",
                "difficulty": "hard",
                "follow_ups": [
                    "What's the difference between memoization and tabulation?",
                    "Can you provide a code example for a dynamic programming problem?",
                    "When would dynamic programming be inefficient?"
                ]
            },
            {
                "id": 5,
                "question": "Explain how hash tables work and handle collisions.",
                "key_concepts": "hash tables, hash functions, collision resolution, chaining, open addressing",
                "difficulty": "medium",
                "follow_ups": [
                    "What makes a good hash function?",
                    "How does chaining compare to open addressing for collision resolution?",
                    "How does load factor affect hash table performance?"
                ]
            }
        ]
        
        # Refined prompt templates for better structured outputs
        self.analysis_prompt = PromptTemplate(
            input_variables=["question", "answer", "key_concepts"],
            template="""
You are a senior software engineer evaluating a DSA interview answer. Analyze the response for technical accuracy, depth, and coverage of key concepts. Be precise and focus on the data structures and algorithms context.

Question: {question}
Expected key concepts: {key_concepts}
Candidate's answer: {answer}

Judge the Cnandidate's answer ccording to the question and key concepts, and provide a score from 0 to 10 based on:
0-3 for poor answers missing key concepts or with major inaccuracies,
4-7 for fair answers that cover some concepts but lack depth or clarity,
8-10 for all better answers

decipher conecpts covered from the candidates response and identify any key concepts they missed by using the expected key concepts as a reference.

Quality should be according to score:
- 0-3: poor
- 4-7: fair
- 8 good
- 9-10: excellent

Respond in this EXACT format:
SCORE: [0-10]
CONCEPTS_COVERED: [comma-separated list of concepts mentioned, or "none" if none]
MISSING_CONCEPTS: [comma-separated list of concepts not mentioned, or "none" if all covered]
QUALITY: [excellent/good/fair/poor]
DEPTH: [deep/adequate/shallow]
DETAILED_ANALYSIS: [Detailed explanation of strengths and weaknesses, mentioning specific DSA concepts]
"""
        )
        
        self.feedback_prompt = PromptTemplate(
            input_variables=["question", "answer", "analysis", "score", "ind"],
            template="""
You are providing constructive feedback for a DSA interview candidate. Be encouraging, specific, and technical.

Question: {question}
Candidate's answer: {answer}
Analysis: {analysis}
Score: {score}/10
ind: {ind}

Provide feedback that:
1. Acknowledges strengths in the answer
2. Highlights areas for improvement with specific DSA concepts
3. Offers actionable, supportive advice
4. Uses a professional tone

Your response shoudl be concise, and solely focused on the technical content of the answer withour any salutations at the end.
You MUST NOT USE OR ASK FOR THE CANDIDATES NAME ANYWHERE.
"""
        )
        
        self.followup_question_prompt = PromptTemplate(
            input_variables=["original_question", "answer", "key_concepts", "analysis"],
            template="""
Generate a follow-up question for a DSA interview based on the candidate's response.

Original question: {original_question}
Candidate's answer: {answer}
Key concepts: {key_concepts}
Analysis: {analysis}

Create a follow-up question that:
1. Targets a missing concept or weak area from the analysis
2. Is relevant to the original question
3. Tests deeper understanding or implementation details
4. Matches the original question's difficulty

Respond in this format:
FOLLOW_UP: [Your follow-up question here]
"""
        )
        
        self.conversation_prompt = PromptTemplate(
            input_variables=["context", "user_input"],
            template="""
You are a friendly DSA interviewer. Respond naturally and professionally, staying focused on the interview context.

Context: {context}
User input: {user_input}

Respond in this format:
RESPONSE: [Your response here]
"""
        )
        
    def reset_interview(self):
        self.current_question_idx = 0
        self.questions_asked = 0
        self.performance_data = []
        self.stage = "greeting"
        self.current_question = None
        self.current_followup_count = 0  # Track follow-up iterations
        self.max_followups = 2  # Max follow-ups per question
        self.conversation_history = []  # Store history for context
        
    def create_chain(self, prompt_template):
        """Create a LangChain chain with the given prompt"""
        return LLMChain(llm=self.llm, prompt=prompt_template)
        
    async def analyze_answer_with_llm(self, question, answer, key_concepts):
        """Use LLM to analyze the candidate's answer"""
        chain = self.create_chain(self.analysis_prompt)
        
        try:
            analysis_result = chain.run(
                question=question,
                answer=answer,
                key_concepts=key_concepts
            )
            
            # Parse structured response
            score_match = re.search(r'SCORE:\s*(\d+)', analysis_result)
            concepts_covered_match = re.search(r'CONCEPTS_COVERED:\s*([^\n]*)', analysis_result)
            missing_concepts_match = re.search(r'MISSING_CONCEPTS:\s*([^\n]*)', analysis_result)
            quality_match = re.search(r'QUALITY:\s*([^\n]*)', analysis_result)
            depth_match = re.search(r'DEPTH:\s*([^\n]*)', analysis_result)
            detailed_analysis_match = re.search(r'DETAILED_ANALYSIS:\s*([^\n]*)', analysis_result)
            
            score = int(score_match.group(1)) if score_match else 5
            concepts_covered = concepts_covered_match.group(1).strip() if concepts_covered_match else "none"
            missing_concepts = missing_concepts_match.group(1).strip() if missing_concepts_match else "none"
            quality = quality_match.group(1).strip() if quality_match else "fair"
            depth = depth_match.group(1).strip() if depth_match else "adequate"
            detailed_analysis = detailed_analysis_match.group(1).strip() if detailed_analysis_match else "Analysis unavailable."
            
            return {
                "raw_analysis": analysis_result,
                "score": score,
                "normalized_score": score / 10.0,
                "concepts_covered": concepts_covered,
                "missing_concepts": missing_concepts,
                "quality": quality,
                "depth": depth,
                "detailed_analysis": detailed_analysis
            }
        except Exception as e:
            # Fallback scoring
            word_count = len(answer.split())
            fallback_score = min(8, max(2, word_count // 10))
            return {
                "raw_analysis": f"Analysis temporarily unavailable. Error: {str(e)[:50]}",
                "score": fallback_score,
                "normalized_score": fallback_score / 10.0,
                "concepts_covered": "none",
                "missing_concepts": key_concepts,
                "quality": "fair",
                "depth": "shallow",
                "detailed_analysis": f"Based on answer length ({word_count} words), more detail is needed."
            }
    
    async def generate_feedback_with_llm(self, question, answer, analysis, score, ind):
        """Use LLM to generate personalized feedback"""
        chain = self.create_chain(self.feedback_prompt)
        
        try:
            feedback = chain.run(
                question=question,
                answer=answer,
                analysis=analysis,
                score=score,
                ind = ind
            )
            feedback = feedback.replace("FEEDBACK:", "").strip()
            return feedback
        except Exception as e:
            # Fallback feedback
            if score >= 7:
                return f"Great answer! You demonstrated good understanding. Score: {score}/10. Try to include more specific DSA concepts."
            elif score >= 5:
                return f"Good response with room for improvement. Score: {score}/10. Focus on addressing all key concepts."
            else:
                return f"Your answer needs more detail and technical depth. Score: {score}/10. Review the key concepts: {analysis.get('missing_concepts', 'unknown')}."
    
    async def should_ask_followup_llm(self, question, answer, score, analysis):
        return score>=3
            
    
    async def generate_followup_question_llm(self, original_question, answer, key_concepts, analysis):
        """Use LLM to generate a relevant follow-up question"""
        chain = self.create_chain(self.followup_question_prompt)
        
        try:
            followup = chain.run(
                original_question=original_question,
                answer=answer,
                key_concepts=key_concepts,
                analysis=analysis
            )
            followup = followup.replace("FOLLOW_UP:", "").strip()
            return followup
        except Exception as e:
            # Fallback to predefined follow-ups
            print(f"Exception occurred: {e}")
            return random.choice(self.current_question['follow_ups'])
    
    async def handle_conversation_llm(self, context, user_input):
        """Use LLM for natural conversation handling"""
        chain = self.create_chain(self.conversation_prompt)
        
        try:
            response = chain.run(context=context, user_input=user_input)
            response = response.replace("RESPONSE:", "").strip()
            return response
        except Exception as e:
            return "Thank you for your response! Let's continue with our interview."
    
    async def process_greeting(self, user_input):
        """Handle initial greeting with LLM"""
        context = "This is the start of a DSA interview. The candidate just greeted you. Welome them warmly and explain that there are going to be asked 5 DSA questions with feedback and possible follow-ups. Dont ask them if they are ready to get started, just start"
        
        greeting_response = await self.handle_conversation_llm(context, user_input)
        
        # Move to questioning stage
        self.stage = "questioning"
        self.current_followup_count = 0
        self.current_question = self.questions[self.current_question_idx]
        self.questions_asked += 1
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": greeting_response})
        
        return f"{greeting_response}\n\n**Question {self.questions_asked}:**\n{self.current_question['question']}"
    
    async def process_answer(self, user_input):
        """Process candidate's answer using LLM analysis"""
        current_q = self.current_question
        
        # Analyze answer with LLM
        analysis = await self.analyze_answer_with_llm(
            current_q['question'], 
            user_input, 
            current_q['key_concepts']
        )
        
        # Generate feedback with LLM
        feedback = await self.generate_feedback_with_llm(
            current_q['question'],
            user_input,
            analysis['raw_analysis'],
            analysis['score'],
            self.current_question_idx
        )
        
        # Store performance data
        self.performance_data.append({
            "question_id": current_q['id'],
            "question": current_q['question'],
            "answer": user_input,
            "analysis": analysis,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
            "is_followup": False
        })
        
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": feedback})
        
        response = f"**Analysis & Feedback:**\n{feedback}\n\n"
        
        # Decide on follow-up with LLM
        should_followup = await self.should_ask_followup_llm(
            current_q['question'],
            user_input,
            analysis['score'],
            analysis['raw_analysis']
        )
        
        if should_followup and self.current_followup_count < self.max_followups:
            self.stage = "following_up"
            self.current_followup_count += 1
            followup_q = await self.generate_followup_question_llm(
                current_q['question'],
                user_input,
                current_q['key_concepts'],
                analysis['raw_analysis']
            )
            response += f"**Follow-up {self.current_followup_count}:**\n{followup_q}"
            self.conversation_history.append({"role": "assistant", "content": followup_q})
        else:
            self.current_followup_count = 0
            response += await self.move_to_next_question()
        
        return response
    
    async def process_followup(self, user_input):
        """Process follow-up response with full LLM analysis"""
        current_q = self.current_question
        
        # Analyze follow-up response with LLM
        analysis = await self.analyze_answer_with_llm(
            current_q['follow_ups'][self.current_followup_count - 1],
            user_input,
            current_q['key_concepts']
        )
        
        # Generate feedback with LLM
        feedback = await self.generate_feedback_with_llm(
            current_q['follow_ups'][self.current_followup_count - 1],
            user_input,
            analysis['raw_analysis'],
            analysis['score'],
            self.current_question_idx
        )
        
        # Store performance data
        self.performance_data.append({
            "question_id": current_q['id'],
            "question": current_q['follow_ups'][self.current_followup_count - 1],
            "answer": user_input,
            "analysis": analysis,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat(),
            "is_followup": True
        })
        
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": feedback})
        
        response = f"**Follow-up Analysis & Feedback:**\n{feedback}\n\n"
        
        # Decide on further follow-up
        should_followup = await self.should_ask_followup_llm(
            current_q['follow_ups'][self.current_followup_count - 1],
            user_input,
            analysis['score'],
            analysis['raw_analysis']
        )
        
        if should_followup and self.current_followup_count < self.max_followups:
            self.current_followup_count += 1
            followup_q = await self.generate_followup_question_llm(
                current_q['question'],
                user_input,
                current_q['key_concepts'],
                analysis['raw_analysis']
            )
            response += f"**Follow-up {self.current_followup_count}:**\n{followup_q}"
            self.conversation_history.append({"role": "assistant", "content": followup_q})
        else:
            self.current_followup_count = 0
            response += await self.move_to_next_question()
        
        return response
    
    async def move_to_next_question(self):
        """Move to next question or end interview"""
        self.current_question_idx += 1
        self.stage = "questioning"
        self.current_followup_count = 0
        
        if self.current_question_idx >= len(self.questions):
            return await self.end_interview()
        
        # Get next question
        self.current_question = self.questions[self.current_question_idx]
        self.questions_asked += 1
        
        response = f"---\n\n**Question {self.questions_asked}:**\n{self.current_question['question']}"
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    async def end_interview(self):
        """End interview with LLM-generated summary"""
        if not self.performance_data:
            return "🎉 **Interview Complete!** Thank you for your time!"
        
        # Calculate metrics
        main_scores = [p['analysis']['score'] for p in self.performance_data if not p['is_followup']]
        avg_score = sum(main_scores) / len(main_scores) if main_scores else 0
        
        # Generate summary context for LLM
        history_summary = "\n".join([f"{h['role']}: {h['content']}" for h in self.conversation_history[-10:]])
        context = f"""Generate a DSA interview summary.
                    Questions answered: {len([p for p in self.performance_data if not p['is_followup']])}
                    Follow-ups answered: {len([p for p in self.performance_data if p['is_followup']])}
                    Average score (main questions): {avg_score:.1f}/10
                    Recent conversation: {history_summary}
                    
                    Provide an encouraging summary with:
                    1. Overall performance assessment
                    2. Specific strengths
                    3. Areas for improvement
                    4. Actionable recommendations for DSA preparation
                    """
        
        llm_summary = await self.handle_conversation_llm(
            context,
            "Please provide a comprehensive interview summary."
        )
        
        summary = f"""🎉 **Interview Complete!**

**🤖 AI Analysis Summary:**
{llm_summary}

**📊 Performance Metrics:**
- Main questions answered: {len([p for p in self.performance_data if not p['is_followup']])}
- Follow-up questions answered: {len([p for p in self.performance_data if p['is_followup']])}
- Average score (main questions): {avg_score:.1f}/10 ({(avg_score/10)*100:.0f}%)

**📋 Question Breakdown:**"""
        
        for i, perf in enumerate(self.performance_data, 1):
            score = perf['analysis']['score']
            q_type = "Follow-up" if perf['is_followup'] else "Main"
            summary += f"\n{i}. {q_type} Q: {score}/10"
        
        return summary

# Global interviewer instance
interviewer = LLMPoweredInterviewer()

@cl.on_chat_start
async def start():
    global interviewer
    interviewer.reset_interview()
    
    welcome = """# 🤖 LLM-Powered DSA Interview

Welcome to your **AI-driven Data Structures & Algorithms interview**!

**🧠 Powered by Advanced AI:**
- **FLAN-T5** model analyzes your responses in real-time
- **Dynamic feedback** tailored to your specific answers  
- **Smart follow-up questions** based on your performance
- **Intelligent conversation** that adapts to your responses

**📋 Interview Format:**
- 5 DSA questions covering core concepts
- AI analyzes each answer for technical accuracy and depth
- Personalized feedback with improvement suggestions
- Up to 2 follow-up questions per topic to deepen understanding
- Comprehensive AI-generated performance summary

**🚀 Ready to begin?** 

Just say hello and let's start this intelligent interview experience!

*Note: The AI is analyzing your responses using natural language processing, so feel free to explain your thinking process naturally.*"""

    await cl.Message(content=welcome).send()

@cl.on_message
async def main(message: cl.Message):
    global interviewer
    
    try:
        user_input = message.content.strip()
        
        # Route to appropriate handler based on interview stage
        if interviewer.stage == "greeting":
            response = await interviewer.process_greeting(user_input)
        elif interviewer.stage == "questioning":
            response = await interviewer.process_answer(user_input)
        elif interviewer.stage == "following_up":
            response = await interviewer.process_followup(user_input)
        else:
            response = "Let's restart the interview. Say hello to begin! 😊"
            interviewer.reset_interview()
        
        await cl.Message(content=response).send()
        
    except Exception as e:
        error_response = f"I encountered an issue processing your response. Let me try to continue... 🤖\n\nError details: {str(e)[:100]}..."
        await cl.Message(content=error_response).send()