import streamlit as st
# from langchain_community.document_loaders import PDFPlumberLoader
from langchain.document_loaders import PyPDFLoader
# from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains import RetrievalQA
import speech_recognition as sr
import pyttsx3
import re
import threading

# Streamlit UI Title
st.title("📄AI Interviewer with DeepSeek R1 & Ollama")

# Initialize Text-to-Speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)  # Adjust speech rate

# Initialize Speech-to-Text Recognizer
recognizer = sr.Recognizer()

def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()
    # tts_engine.stop()

def speak_non_blocking(text):
    def run():
        tts_engine.say(text)
        tts_engine.runAndWait()
    threading.Thread(target=run).start()

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for an answer...")
        audio = recognizer.listen(source)
    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        print(f"Answer: {text}")
        return text
    except Exception as e:
        print(f"Error: {e}")
        return None

# File Upload
uploaded_file = st.file_uploader("Upload your PDF file here", type="pdf")

if uploaded_file:

    #Loading the PDF file as temporary file
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getvalue())

    loader = PyPDFLoader("temp.pdf")
    docs = loader.load()


    #Text Splitter
    # text_splitter = SemanticChunker(HuggingFaceEmbeddings())
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documents = text_splitter.split_documents(docs)


    #Embedging and Vectorization
    embedder = HuggingFaceEmbeddings()
    vector = FAISS.from_documents(documents, embedder)
    retriever = vector.as_retriever(search_type="similarity", search_kwargs={"k": 3})


    #Language Model and Prompt Template
    llm = Ollama(model="deepseek-r1:1.5b")


    #User ask a question
    prompt = """
    Use the following resume context to generate an interview question:
    Context: {context}
    Question: Generate a question that would be asked based on the skillset specified in the resume.
    """
    

    setup_prompt = PromptTemplate.from_template(prompt)
    llm_chain = LLMChain(llm=llm, prompt=setup_prompt)

    combine_documents_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="context")
    qa = RetrievalQA(combine_documents_chain=combine_documents_chain, retriever=retriever)

    

    question = qa("Generate an interview question based on the resume")["result"]

    # question_pattern = r"\d+\.\s\*\*(.*?)\*\*:\s+(.*?)\n"
    question_pattern = r'"(.*?)"'
    matches = re.findall(question_pattern, question)

    question_stack = []
    first_question = None
    if matches:
    # Populate question_stack
        question_stack = [f"{idx + 1}. {q}" for idx, q in enumerate(matches)]
        print(f"Questions: {question_stack}")

    # Ensure the first question exists before speaking it
        if question_stack[0]:
            first_question = question_stack[0]
            st.write(f"**Interview Question:** {question_stack[0]}")
            speak_non_blocking(f"Question: {question_stack[0]}")
        else:
            st.warning("No valid questions retrieved. Please check the input or try again.")

    # Store questions in a stack (list)
    # question_stack = [f"{idx + 1}. {q}" for idx, q in enumerate(matches)]
    # for questions in question_stack:
    #     print(questions)
    # print(f"Question: {question}")
    # # speak(f"Question: {question_stack[0]}")
    # st.write(f"**Interview Question:** {question_stack[0]}")
    # speak_non_blocking(f"Question: {question_stack[0]}")

    print("Now for feedback")
    # Resume: {resume}
    feedback_prompt = """
    Question: {question}
    Candidate's Answer: {answer}
    Score the answer out of 100.    
    """
    # Score the answer out of 10 based on relevance, out of 10 on clarity, and out of 10 on completeness, and provide feedback.

    feedback_template = PromptTemplate.from_template(feedback_prompt)
    feedback_chain = LLMChain(llm=llm, prompt=feedback_template)

    user_input = st.text_input("Speak your answer or type it below:", "")

    if st.button("Start Listening"):
        recognize_speech(callback=lambda text: st.session_state.update({"user_input": text}))

    if user_input:
        print("Inside User Input:")
        feedback = feedback_chain.run({
            # "resume": docs,
            "question": first_question,
            "answer": user_input
        })

        # Display feedback and score
        st.write("**AI Feedback and Score:**")
        st.write(feedback)
        # response = qa()["result"]
        # st.write("**Response:**")
        # st.write(response)