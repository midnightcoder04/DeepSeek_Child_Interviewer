# AI Interviewer  
**Note**: The name is kept as "Child Interviewer" not because it interviews children, but because the 1.5 billion parameter model of DeepSeek feels like a child and was actually hard to work with.  

## What it does?  
- Generates interview questions from your resume.  
- Speaks the questions aloud.  
- Takes answers via audio input.  
- Provides a score and feedback.  

---

## Project Structure  
The project is divided into two main folders:  
1. **Backend**: Flask server for processing resumes, generating questions, and evaluating answers.  
2. **Frontend**: React app for user interaction, file upload, and displaying results.  

---

## Pre-Setup  
1. **Download Anaconda** (for Python environment management):  
   [Anaconda Download Link](https://www.anaconda.com/download)  

2. **Install Ollama** (to run the DeepSeek model locally):  
   - **Windows**: [Ollama Windows Installer](https://ollama.com/download/OllamaSetup.exe)  
   - **macOS**: [Ollama macOS Installer](https://ollama.com/download/Ollama-darwin.pkg)  
   - **Linux**:  
     ```bash
     curl -fsSL https://ollama.com/install.sh | sh
     ```  

3. **Download Node.js** (for running the React frontend):  
   [Node.js Download Link](https://nodejs.org/)  

4. **Download an Editor** (if you don’t have one already).  

---

## Setup + Run  

### 0. **Ollama Setup**  
1. Open a terminal/PowerShell and run:  
   ```bash
   ollama pull deepseek-r1:1.5b
   ```  
2. **Keep Ollama running in the background**:  
   - **Windows**:  
     - From Start Menu → Search for "Ollama" → Launch app  
     - *OR* in PowerShell:  
       ```powershell
       ollama serve
       ```  
   - **macOS/Linux**:  
     ```bash
     ollama serve
     ```  

---

### 1. **Backend Setup**  
1. Open a new terminal and navigate to the `backend` folder.  
2. Create a virtual environment:  
   ```bash
   conda create -n AI_Interviewer python=3.10.10 -y
   conda activate AI_Interviewer
   ```  
3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```  
4. Run the Flask server:  
   ```bash
   flask run --port=5000
   ```  
   The backend will now be running at `http://localhost:5000`.  

---

### 2. **Frontend Setup**  
1. Open a **new terminal** and navigate to the `frontend` folder.  
2. Install Node.js dependencies:  
   ```bash
   npm install vite @vitejs/plugin-react react react-dom
   ```  
3. Run the React app:  
   ```bash
   npm run dev
   ```  
   The frontend will now be running at `http://localhost:5173`.  

---

## Using the App  
1. Open your browser and go to `http://localhost:5173`.  
2. Upload your resume (PDF format).  
3. The app will:  
   - Generate interview questions based on your resume.  
   - Speak the questions aloud.  
   - Allow you to answer via audio or text input.  
   - Provide a score and feedback.  

---

## ⚠️ Important Notes  
1. **Ollama Must Be Running**  
   - Keep the Ollama terminal/PowerShell window open throughout usage  
   - If you see connection errors, restart Ollama  

2. **System Requirements**  
   - Minimum 8GB RAM recommended for running the AI model  .
   - Stable internet connection required for initial setup. 
   - Enough storage space for downloading and using LLM locallly.

---

## Comments  
Feel free to contribute to the project! If you encounter any issues, please open an issue on GitHub.  

--- 
