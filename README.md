### AI Interviewer
Note: The name is kept as child interviwer not cause it interviews children but cause the 1.5 billion paramters model of DeepSeek feels like a child and was actually hard to work with... 

## What it does?
- It generates questions from your resume 
- Speaks it out
- Takes answer in audio
- Gives score

## Pre-Setup -
Download Anaconda [link](https://www.anaconda.com/download)
Download the deepseek Model from Olama [link](https://ollama.com/download/OllamaSetup.exe
)
Download an Editor (If you dont have one)

## Setup
1. Create a venv on anaconda terminal
```conda create -n AI_Interviewer python=3.10.10 -y```
2. Install required packages using pip (install pip if you dont have before this step)
```pip install -U langchain langchain-community streamlit pdfplumber semantic-chunkers open-text-embeddings ollama prompt-template langchain langchain_experimental sentence-transformers faiss-cpu```
3. Navigate to the forked repo folder with the app.py file (cd to path) and run
```streamlit run app.py```
