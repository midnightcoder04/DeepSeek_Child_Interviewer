from flask import Flask, request, jsonify
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains import RetrievalQA
import re
import os 
from werkzeug.utils import secure_filename
import uuid
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)
# Initialize global components (LLM, embedders, etc.)
embedder = HuggingFaceEmbeddings()
# Using a more capable model for better responses
llm = Ollama(model="deepseek-r1:1.5b")

# Improved prompt with more detailed instructions
prompt_template = """
Use the following resume context to generate a thoughtful interview question:
Context: {context}

Guidelines for generating questions:
1. Focus on technical skills mentioned in the resume
2. Ask about specific projects or achievements
3. Include scenario-based questions that test problem-solving
4. Ensure the question is open-ended and requires detailed answers
5. The question should be challenging but fair

Question: Generate a question that would be asked based on the skillset specified in the resume.
"""

# More structured feedback prompt
feedback_prompt = """
Question: {question}
Candidate's Answer: {answer}

Provide a comprehensive evaluation with the following structure:
1. Score (0-100): Evaluate based on accuracy, completeness, and depth of understanding
2. Strengths: List 1-2 strong points in the answer
3. Areas for improvement: Identify 1-2 specific areas that could be better
4. Overall assessment: 1-2 sentences summarizing the quality of the answer

Be concise and professional. DO NOT include any internal thinking or reasoning process.
"""

setup_prompt = PromptTemplate.from_template(prompt_template)
feedback_template = PromptTemplate.from_template(feedback_prompt)

UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'pdf'}

# Create data directory if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variables to store interview history and scores
question_answer_history = []
total_score = 0
num_answers = 0

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    try:
        # Generate unique filename
        original_name = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]  # Add unique identifier
        filename = f"{unique_id}_{original_name}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file permanently
        file.save(save_path)
        
        # Now load from the saved path
        loader = PyPDFLoader(save_path)
        docs = loader.load()

        # Rest of your processing logic
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        documents = text_splitter.split_documents(docs)
        
        vector = FAISS.from_documents(documents, embedder)
        retriever = vector.as_retriever(search_type="similarity", search_kwargs={"k": 3})

        # Store retriever in global state
        global retriever_instance
        retriever_instance = retriever

        # Automatically generate a question
        qa_chain = RetrievalQA(
            combine_documents_chain=StuffDocumentsChain(
                llm_chain=LLMChain(llm=llm, prompt=setup_prompt),
                document_variable_name="context"
            ),
            retriever=retriever
        )

        result = qa_chain.run("Generate an interview question based on the resume")
        
        # Improved question extraction with fallback
        question_pattern = r'"(.*?)"'
        matches = re.findall(question_pattern, result)

        if matches:
            question = matches[0]
        else:
            # Fallback: if no quotes found, use the entire response
            question = result.strip()
        question = clean_llm_response(question)
        return jsonify({
            "message": "Resume uploaded and processed successfully.",
            "filename": filename,
            "question": question
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def clean_llm_response(response):
    # Remove <think>...</think> blocks
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    
    # Remove any leftover HTML-like tags
    cleaned = re.sub(r'<.*?>', '', cleaned)
    
    # Format numbered lists properly (e.g., "1. **Score**: 85" -> "1. Score: 85")
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
    
    # Handle bullet points (- Item -> - Item)
    cleaned = re.sub(r'-\s+', '- ', cleaned)
    
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Add line breaks for readability after sections like "1. Score:", "2. Strengths:", etc.
    cleaned = re.sub(r'(\d+\.\s\S+?:)', r'\n\1', cleaned)

    return cleaned

@app.route('/evaluate-answer', methods=['POST'])
def evaluate_answer():
    global question_answer_history, total_score, num_answers
    data = request.json
    if not data or 'question' not in data or 'answer' not in data:
        return jsonify({"error": "Invalid input"}), 400

    # Step 1: Generate feedback
    feedback_chain = LLMChain(llm=llm, prompt=feedback_template)
    raw_feedback = feedback_chain.run({
        "question": data['question'],
        "answer": data['answer']
    })
    feedback = clean_llm_response(raw_feedback)

    score_match = re.search(r'Score:\s*(\d+)', feedback)
    print(score_match)
    if score_match:
        score = int(score_match.group(1))
        total_score += score
        num_answers += 1

    # Step 2: Generate follow-up question with improved prompt
    follow_up_prompt = """
    Based on the following question and the candidate's answer, generate a follow-up question:
    
    Original Question: {question}
    Candidate's Answer: {answer}
    
    Guidelines for the follow-up question:
    1. Dig deeper into areas where the candidate showed knowledge
    2. Explore any gaps or areas that need clarification
    3. Be specific and contextual to their answer
    4. Should be challenging but fair
    
    Provide ONLY the follow-up question, no explanations or commentary.
    """
    follow_up_template = PromptTemplate.from_template(follow_up_prompt)
    follow_up_chain = LLMChain(llm=llm, prompt=follow_up_template)
    raw_follow_up = follow_up_chain.run({
        "question": data['question'],
        "answer": data['answer']
    })
    follow_up_question = clean_llm_response(raw_follow_up)

    # Store question and answer in history
    question_answer_history.append({
        "question": data['question'],
        "answer": data['answer'],
        "feedback": feedback,
        "follow_up": follow_up_question
    })

    # Step 3: Return feedback and follow-up question
    return jsonify({
        "feedback": feedback.strip(),
        "follow_up_question": follow_up_question.strip()
    })

@app.route('/stop', methods=['POST'])
def stop_interview():
    global question_answer_history, total_score, num_answers
    if not question_answer_history:
        return jsonify({"message": "No interview history available."}), 400

    # Calculate average score
    if num_answers > 0:
        average_score = total_score / num_answers
    else:
        average_score = 0

    # Clear the interview history and scores
    question_answer_history = []
    total_score = 0
    num_answers = 0

    return jsonify({
        "message": f"The interview has ended. The average score of the candidate is {average_score:.2f}."
    })

if __name__ == '__main__':
    app.run(debug=True)