import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasUploadedResume, setHasUploadedResume] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  function speakQuestion(question) {
    const speech = new SpeechSynthesisUtterance(question);
    speech.lang = 'en-US'; // Set language
    speech.rate = 1; // Adjust speed
    window.speechSynthesis.speak(speech);
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          type: 'bot',
          content: '👋 Welcome! Please upload your resume in PDF format to begin the interview process.',
        },
      ]);
    }
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    // Check if the browser supports speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';
      
      recognitionRef.current.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        // Update input field with final result
        if (finalTranscript !== '') {
          setInputText(prevText => prevText + finalTranscript + ' ');
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        setIsRecording(false);
      };
      
      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
    } else {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
          setIsRecording(true);
        } catch (error) {
          console.error("Couldn't start recording:", error);
        }
      } else {
        alert("Speech recognition is not supported in this browser.");
      }
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;
  
    if (!hasUploadedResume) {
      setMessages((prev) => [
        ...prev,
        {
          type: 'bot',
          content: 'Please upload your resume first to continue with the interview.',
        },
      ]);
      return;
    }
  
    const userMessage = { type: 'user', content: inputText };
    const currentInputText = inputText; // Store the current input
    
    setInputText(''); // Clear input immediately
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    
    try {
      // Retrieve the previous question from chat history
      const previousQuestion = messages
        .slice()
        .reverse()
        .find((msg) => msg.type === 'bot' && msg.content.startsWith('Question:'));
  
      const question = previousQuestion ? previousQuestion.content.replace('Question: ', '') : '';
      
      // Send answer and question to the backend
      const response = await axios.post('http://localhost:5000/evaluate-answer', {
        question,
        answer: currentInputText,
      });
       
      const { feedback, follow_up_question } = response.data;
  
      // Add feedback and follow-up question to the chat
      setMessages((prev) => [
        ...prev,
        { type: 'bot', content: `Feedback: ${feedback}` },
        { type: 'bot', content: `Follow-up Question: ${follow_up_question || 'No follow-up question generated.'}` },
      ]);
  
      // Speak follow-up question (if available)
      if (follow_up_question) {
        speakQuestion(follow_up_question);
      }
    } catch (error) {
      console.error('Error evaluating answer:', error);
      setMessages((prev) => [
        ...prev,
        { type: 'bot', content: 'An error occurred while evaluating your answer. Please try again.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      alert('Please upload only PDF files');
      fileInputRef.current.value = '';
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    setIsLoading(true);

    try {
      // Upload the resume
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.status === 200) {
        const { filename, question, message } = response.data;

        // Update messages with the upload and question details
        setMessages((prev) => [
          ...prev,
          { type: 'user', content: `Uploaded Resume: ${file.name}` },
          { type: 'bot', content: message },
          { type: 'bot', content: `Question: ${question}` },
        ]);

        // Mark resume as uploaded
        setHasUploadedResume(true);

        // Trigger Text-to-Speech (optional, handled by backend too)
        if (question) {
          speakQuestion(question);
        }
      } else {
        alert('An error occurred. Please try again.');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('An error occurred while uploading. Please try again.');
    } finally {
      setIsLoading(false); // Stop showing "Processing..."
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const handleStopInterview = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/stop');
      const { message } = response.data;
      setMessages((prev) => [
        ...prev,
        { type: 'bot', content: message },
      ]);
    } catch (error) {
      console.error('Error stopping interview:', error);
      setMessages((prev) => [
        ...prev,
        { type: 'bot', content: 'An error occurred while stopping the interview. Please try again.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0F1E] p-4 text-white">
      <div className="max-w-4xl mx-auto glass rounded-2xl shadow-2xl overflow-hidden transition-all duration-300 hover:shadow-blue-500/10">
        {/* Header */}
        <div className="p-4 border-b border-blue-500/10 bg-slate-900/50">
          <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600">
            AI Interviewer
          </h1>
        </div>

        {/* Chat Messages */}
        <div className={`overflow-y-auto p-6 space-y-4 transition-all duration-300 ${
          messages.length > 0 ? 'min-h-[200px] max-h-[600px]' : 'h-[100px]'
        }`}>
          {messages.map((message, index) => (
            <div
              key={index}
              className={`message-animation flex ${
                message.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] p-4 rounded-xl ${
                  message.type === 'user'
                    ? 'bg-blue-600/20 border border-blue-500/20 text-blue-100'
                    : 'bg-slate-800/50 border border-slate-700/50 text-slate-100'
                } shadow-lg backdrop-blur-sm`}
              >
                {message.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-center fade-in">
              <div className="bg-blue-500/10 text-blue-400 px-4 py-2 rounded-full border border-blue-500/20">
                Processing...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-slate-900/50 border-t border-blue-500/10">
          <form onSubmit={handleSendMessage} className="flex gap-2 items-center">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf"
              className="hidden"
            />
            <button
              type="button"
              onClick={triggerFileInput}
              className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400
                       hover:bg-blue-500/20 transition-all duration-200"
              title="Upload Resume (PDF)"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24" 
                strokeWidth={1.5} 
                stroke="currentColor" 
                className="w-6 h-6"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" 
                />
              </svg>
            </button>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={hasUploadedResume ? "Type your message or use voice feature..." : "Upload your resume to start the interview..."}
              className="flex-1 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-white
                       placeholder-blue-300/50 focus:outline-none focus:ring-2 focus:ring-blue-500/20
                       transition-all duration-200"
              disabled={isLoading || !hasUploadedResume}
            />
            
            {/* Voice Recording Button */}
            <button
              type="button"
              onClick={toggleRecording}
              disabled={isLoading || !hasUploadedResume}
              className={`p-3 rounded-lg border transition-all duration-200
                ${isRecording 
                  ? 'bg-red-500/20 border-red-500/40 text-red-400 animate-pulse' 
                  : 'bg-blue-500/10 border-blue-500/20 text-blue-400 hover:bg-blue-500/20'
                }
                disabled:bg-slate-800/50 disabled:border-slate-700/50
                disabled:text-slate-500 disabled:cursor-not-allowed`}
              title={isRecording ? "Stop Recording" : "Start Voice Recording"}
            >
              {isRecording ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <rect x="6" y="6" width="12" height="12" rx="2" strokeWidth="2" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>
            
            <button
              type="submit"
              disabled={isLoading || !hasUploadedResume}
              className="px-6 py-3 bg-blue-500/20 text-blue-300 rounded-lg border border-blue-500/20
                       hover:bg-blue-500/30 disabled:bg-slate-800/50 disabled:border-slate-700/50
                       disabled:text-slate-500 disabled:cursor-not-allowed
                       transition-all duration-200 font-medium"
            >
              Send
            </button>
            <button
              type="button"
              onClick={handleStopInterview}
              disabled={isLoading}
              className="px-6 py-3 bg-red-500/20 text-red-300 rounded-lg border border-red-500/20
                       hover:bg-red-500/30 disabled:bg-slate-800/50 disabled:border-slate-700/50
                       disabled:text-slate-500 disabled:cursor-not-allowed
                       transition-all duration-200 font-medium"
            >
              Stop
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default App