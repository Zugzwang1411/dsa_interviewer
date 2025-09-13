from datetime import datetime
import random
import json
import os
from .llm_wrappers import create_chain, run_chain, parse_analysis
from .config import get_config

class LLMPoweredInterviewer:
    def __init__(self):
        self.config = get_config()
        
        self.reset_interview()
        
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
        
        self.analysis_prompt_template = """
You are a senior software engineer evaluating a DSA interview answer. Analyze the response for technical accuracy, depth, and coverage of key concepts. Be precise and focus on the data structures and algorithms context.

Question: {question}
Expected key concepts: {key_concepts}
Candidate's answer: {answer}

Judge the Candidate's answer according to the question and key concepts, and provide a score from 0 to 10 based on:
0-3 for poor answers missing key concepts or with major inaccuracies,
4-7 for fair answers that cover some concepts but lack depth or clarity,
8-10 for all better answers

decipher concepts covered from the candidates response and identify any key concepts they missed by using the expected key concepts as a reference.

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
        
        self.feedback_prompt_template = """
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

Your response should be concise, and solely focused on the technical content of the answer without any salutations at the end.
You MUST NOT USE OR ASK FOR THE CANDIDATES NAME ANYWHERE.
"""
        
        self.followup_question_prompt_template = """
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
        
        self.conversation_prompt_template = """
You are a friendly DSA interviewer. Respond naturally and professionally, staying focused on the interview context.

Context: {context}
User input: {user_input}

Respond in this format:
RESPONSE: [Your response here]
"""
        
    def reset_interview(self):
        self.current_question_idx = 0
        self.questions_asked = 0
        self.performance_data = []
        self.stage = "greeting"
        self.current_question = None
        self.current_followup_count = 0
        self.max_followups = 2
        self.conversation_history = []
        
    async def analyze_answer_with_llm(self, question, answer, key_concepts):
        chain = create_chain(self.analysis_prompt_template)
        
        try:
            analysis_result = await run_chain(chain, {
                "question": question,
                "answer": answer,
                "key_concepts": key_concepts
            })
            
            return parse_analysis(analysis_result)
        except Exception as e:
            from .llm_wrappers import fallback_scoring
            return fallback_scoring(answer, key_concepts)
    
    async def generate_feedback_with_llm(self, question, answer, raw_analysis, score, ind):
        chain = create_chain(self.feedback_prompt_template)
        
        try:
            feedback = await run_chain(chain, {
                "question": question,
                "answer": answer,
                "analysis": raw_analysis,
                "score": score,
                "ind": ind
            })
            return feedback.replace("FEEDBACK:", "").strip()
        except Exception as e:
            if score >= 7:
                return f"Great answer! You demonstrated good understanding. Score: {score}/10. Try to include more specific DSA concepts."
            elif score >= 5:
                return f"Good response with room for improvement. Score: {score}/10. Focus on addressing all key concepts."
            else:
                # Since raw_analysis is a string, we can't extract missing_concepts from it
                # Use a generic fallback message
                return f"Your answer needs improvement. Score: {score}/10. Please provide more detailed explanations and cover the key concepts."
    
    async def should_ask_followup_llm(self, question, answer, score, analysis):
        # Ask follow-up for medium scores (3-7), move forward for very low (0-2) or high (8-10) scores
        return 3 <= score
            
    async def generate_followup_question_llm(self, original_question, answer, key_concepts, analysis):
        chain = create_chain(self.followup_question_prompt_template)
        
        try:
            followup = await run_chain(chain, {
                "original_question": original_question,
                "answer": answer,
                "key_concepts": key_concepts,
                "analysis": analysis
            })
            return followup.replace("FOLLOW_UP:", "").strip()
        except Exception as e:
            print(f"Exception occurred: {e}")
            return random.choice(self.current_question['follow_ups'])
    
    async def handle_conversation_llm(self, context, user_input):
        chain = create_chain(self.conversation_prompt_template)
        
        try:
            response = await run_chain(chain, {
                "context": context, 
                "user_input": user_input
            })
            return response.replace("RESPONSE:", "").strip()
        except Exception as e:
            return "Thank you for your response! Let's continue with our interview."
    
    async def process_greeting(self, user_input):
        context = "This is the start of a DSA interview. The candidate just greeted you. Welcome them warmly and explain that there are going to be asked 5 DSA questions with feedback and possible follow-ups. Don't ask them if they are ready to get started, just start"
        
        greeting_response = await self.handle_conversation_llm(context, user_input)
        
        self.stage = "questioning"
        self.current_followup_count = 0
        self.current_question = self.questions[self.current_question_idx]
        self.questions_asked += 1
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": greeting_response})
        
        return f"{greeting_response}\n\n**Question {self.questions_asked}:**\n{self.current_question['question']}"
    
    async def process_answer(self, user_input):
        current_q = self.current_question
        
        analysis = await self.analyze_answer_with_llm(
            current_q['question'], 
            user_input, 
            current_q['key_concepts']
        )
        
        feedback = await self.generate_feedback_with_llm(
            current_q['question'],
            user_input,
            analysis['raw_analysis'],
            analysis['score'],
            self.current_question_idx
        )
        
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
        current_q = self.current_question
        
        analysis = await self.analyze_answer_with_llm(
            current_q['follow_ups'][self.current_followup_count - 1],
            user_input,
            current_q['key_concepts']
        )
        
        feedback = await self.generate_feedback_with_llm(
            current_q['follow_ups'][self.current_followup_count - 1],
            user_input,
            analysis['raw_analysis'],
            analysis['score'],
            self.current_question_idx
        )
        
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
        self.current_question_idx += 1
        self.stage = "questioning"
        self.current_followup_count = 0
        
        if self.current_question_idx >= len(self.questions):
            return await self.end_interview()
        
        self.current_question = self.questions[self.current_question_idx]
        self.questions_asked += 1
        
        response = f"---\n\n**Question {self.questions_asked}:**\n{self.current_question['question']}"
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    async def end_interview(self):
        if not self.performance_data:
            return "🎉 **Interview Complete!** Thank you for your time!"
        
        main_scores = [p['analysis']['score'] for p in self.performance_data if not p['is_followup']]
        avg_score = sum(main_scores) / len(main_scores) if main_scores else 0
        
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
    
    def get_state(self):
        return {
            "current_question_idx": self.current_question_idx,
            "questions_asked": self.questions_asked,
            "stage": self.stage,
            "current_question": self.current_question,
            "current_followup_count": self.current_followup_count,
            "performance_data": self.performance_data,
            "conversation_history": self.conversation_history
        }
    
    def save_to_file(self, session_id):
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        with open(os.path.join(data_dir, f'{session_id}.json'), 'w') as f:
            json.dump(self.get_state(), f, indent=2)
    
    def load_from_file(self, session_id):
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        file_path = os.path.join(data_dir, f'{session_id}.json')
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                state = json.load(f)
                
            self.current_question_idx = state['current_question_idx']
            self.questions_asked = state['questions_asked']
            self.stage = state['stage']
            self.current_question = state['current_question']
            self.current_followup_count = state['current_followup_count']
            self.performance_data = state['performance_data']
            self.conversation_history = state['conversation_history']
