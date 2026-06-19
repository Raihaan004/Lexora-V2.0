'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Plus, MessageSquare, Trash2, Upload, FileText, Send, 
  Square, Copy, Check, Sparkles, Database, Sun, Moon, 
  AlertCircle, Loader2, RefreshCw
} from 'lucide-react';
import { api, Message, ChatSession, DocumentInfo } from '@/lib/api';
import Markdown from '@/components/chat/Markdown';

export default function Home() {
  // Theme & Layout state
  const [isDark, setIsDark] = useState(true);
  
  // App Domain state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [useRag, setUseRag] = useState(true);
  
  // UI input & execution states
  const [inputText, setInputText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  
  // Clipboard copied indicator
  const [copiedId, setCopiedId] = useState<number | null>(null);
  
  // Refs
  const abortControllerRef = useRef<AbortController | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // 1. App Startup: Check backend sanity, sync local documents list, and pull chat history
  useEffect(() => {
    checkHealth();
    fetchDocuments();
    loadSessionsFromLocalStorage();
  }, []);

  // 2. Scroll chat box to bottom on new message chunk
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions, currentSessionId, isGenerating]);

  // Load chat session logs from localStorage
  const loadSessionsFromLocalStorage = () => {
    try {
      const saved = localStorage.getItem('lexora_sessions');
      if (saved) {
        const parsed = JSON.parse(saved);
        setSessions(parsed);
        if (parsed.length > 0) {
          setCurrentSessionId(parsed[0].id);
        }
      } else {
        // Create initial default chat
        createNewSession("New Conversation");
      }
    } catch (e) {
      console.error('Failed to parse saved sessions: ', e);
    }
  };

  // Persist session history helper
  const saveSessions = (updatedSessions: ChatSession[]) => {
    setSessions(updatedSessions);
    localStorage.setItem('lexora_sessions', JSON.stringify(updatedSessions));
  };

  const checkHealth = async () => {
    try {
      const res = await fetch('http://localhost:8000/health');
      if (res.ok) {
        setBackendHealthy(true);
      } else {
        setBackendHealthy(false);
      }
    } catch {
      setBackendHealthy(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch (e) {
      console.error('Failed to load documents list: ', e);
    }
  };

  const createNewSession = (title?: string) => {
    const newSession: ChatSession = {
      id: `session-${Date.now()}`,
      title: title || `Chat ${sessions.length + 1}`,
      messages: [],
      created_at: new Date().toISOString()
    };
    const updated = [newSession, ...sessions];
    saveSessions(updated);
    setCurrentSessionId(newSession.id);
  };

  const deleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = sessions.filter(s => s.id !== id);
    saveSessions(updated);
    
    if (currentSessionId === id) {
      if (updated.length > 0) {
        setCurrentSessionId(updated[0].id);
      } else {
        setCurrentSessionId(null);
      }
    }
  };

  // Stream send message handler
  const handleSendMessage = async (textToSend?: string) => {
    const messageText = textToSend || inputText;
    if (!messageText.trim() || isGenerating || !currentSessionId) return;

    if (!textToSend) setInputText('');

    // Locate active session
    const activeSessionIdx = sessions.findIndex(s => s.id === currentSessionId);
    if (activeSessionIdx === -1) return;

    const activeSession = sessions[activeSessionIdx];
    
    // Auto-update default title on first question
    let newTitle = activeSession.title;
    if (activeSession.messages.length === 0 && newTitle.startsWith("New Conversation")) {
      newTitle = messageText.length > 25 ? `${messageText.slice(0, 22)}...` : messageText;
    }

    // Structure messages
    const userMsg: Message = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };

    const assistantMsg: Message = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    };

    // Update state synchronously for UI feedback
    const updatedMessages = [...activeSession.messages, userMsg, assistantMsg];
    const updatedSessions = sessions.map((s, idx) => {
      if (idx === activeSessionIdx) {
        return { ...s, title: newTitle, messages: updatedMessages };
      }
      return s;
    });
    saveSessions(updatedSessions);
    setIsGenerating(true);

    // Initialize Abort Signal for Stop Generation button
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let responseAccumulator = '';
    try {
      await api.sendMessageStream(
        currentSessionId,
        messageText,
        useRag,
        (chunk: string) => {
          responseAccumulator += chunk;
          // Dynamically stream chunk increments
          setSessions(prevSessions => 
            prevSessions.map(s => {
              if (s.id === currentSessionId) {
                const msgs = [...s.messages];
                msgs[msgs.length - 1] = {
                  ...msgs[msgs.length - 1],
                  content: responseAccumulator
                };
                return { ...s, messages: msgs };
              }
              return s;
            })
          );
        },
        controller.signal
      );
    } catch (e: any) {
      if (e.name === 'AbortError') {
        responseAccumulator += '\n\n*(Generation stopped by user)*';
      } else {
        responseAccumulator += `\n\n*(Inference connection error: ${e.message})*`;
      }
      // Set final message block
      setSessions(prevSessions => 
        prevSessions.map(s => {
          if (s.id === currentSessionId) {
            const msgs = [...s.messages];
            msgs[msgs.length - 1] = {
              ...msgs[msgs.length - 1],
              content: responseAccumulator
            };
            return { ...s, messages: msgs };
          }
          return s;
        })
      );
    } finally {
      // Sync local storage state on generation complete
      const finalSessions = sessions.map(s => {
        if (s.id === currentSessionId) {
          const msgs = [...s.messages];
          msgs[msgs.length - 1] = {
            ...msgs[msgs.length - 1],
            content: responseAccumulator
          };
          return { ...s, title: newTitle, messages: msgs };
        }
        return s;
      });
      saveSessions(finalSessions);
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopGenerating = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsUploading(true);

    try {
      await api.uploadDocument(file);
      await fetchDocuments(); // Reload registry list
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteDocument = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this document from Lexora knowledge base?')) return;

    try {
      await api.deleteDocument(id);
      await fetchDocuments();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const copyToClipboard = async (text: string, msgIdx: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(msgIdx);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy message text: ', err);
    }
  };

  const activeSession = sessions.find(s => s.id === currentSessionId);
  const activeMessages = activeSession ? activeSession.messages : [];

  return (
    <div className={`flex h-screen w-screen overflow-hidden ${isDark ? 'dark bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      
      {/* 1. LEFT SIDEBAR */}
      <aside className="hidden md:flex flex-col w-72 shrink-0 border-r border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-900/60 backdrop-blur-md">
        
        {/* Sidebar Header Title */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <div className="p-1 rounded-md bg-indigo-600 text-white">
              <Sparkles size={18} />
            </div>
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
              Lexora RAG
            </span>
          </div>
          
          {/* Health indicator */}
          <div className="flex items-center gap-1.5" title={backendHealthy ? "Backend connected" : "Backend offline"}>
            <span className={`h-2.5 w-2.5 rounded-full ${backendHealthy ? 'bg-emerald-500 shadow-md' : 'bg-rose-500 shadow-md animate-pulse'}`} />
            {!backendHealthy && (
              <button onClick={checkHealth} className="hover:text-slate-400">
                <RefreshCw size={12} className="animate-spin" style={{ animationDuration: '4s' }} />
              </button>
            )}
          </div>
        </div>

        {/* Action: Create New Conversation */}
        <div className="p-3">
          <button
            onClick={() => createNewSession("New Conversation")}
            className="flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-[14px] shadow-lg shadow-indigo-600/10 transition-all active:scale-[0.98]"
          >
            <Plus size={16} />
            <span>New Chat</span>
          </button>
        </div>

        {/* Chat Conversations Registry Lists */}
        <div className="flex-1 overflow-y-auto px-2 space-y-1 scrollbar-thin">
          <div className="px-3 py-1 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Conversations
          </div>
          {sessions.map(s => {
            const isActive = s.id === currentSessionId;
            return (
              <div
                key={s.id}
                onClick={() => setCurrentSessionId(s.id)}
                className={`flex items-center justify-between group cursor-pointer py-2 px-3 rounded-lg text-[13.5px] transition-colors ${
                  isActive 
                    ? 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-slate-100 font-medium' 
                    : 'text-slate-500 hover:bg-slate-200/50 dark:hover:bg-slate-800/50 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2 overflow-hidden mr-2">
                  <MessageSquare size={14} className="shrink-0 text-slate-400" />
                  <span className="truncate">{s.title}</span>
                </div>
                <button
                  onClick={(e) => deleteSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-500 transition-opacity"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })}
          {sessions.length === 0 && (
            <div className="text-center py-8 text-xs text-slate-400 italic">
              No active conversations
            </div>
          )}
        </div>

        {/* Knowledge Base Uploaded Documents section */}
        <div className="border-t border-slate-200 dark:border-slate-800 p-4 min-h-[160px] flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
              Documents Library
            </span>
            {isUploading && <Loader2 size={12} className="animate-spin text-indigo-500" />}
          </div>

          {/* Hidden File Picker */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.docx,.txt,.csv"
            className="hidden"
          />

          {/* Quick upload trigger zone */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center justify-center gap-2 border border-dashed border-slate-300 dark:border-slate-700 hover:border-indigo-500 dark:hover:border-indigo-500 py-3 rounded-lg text-xs text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-3 active:scale-[0.98]"
          >
            <Upload size={14} />
            <span>Upload Document</span>
          </button>

          {/* Scrollable list of files */}
          <div className="flex-1 overflow-y-auto space-y-1.5 max-h-[180px] scrollbar-thin">
            {documents.map(doc => (
              <div
                key={doc.id}
                className="flex items-center justify-between py-1.5 px-2 rounded bg-slate-200/50 dark:bg-slate-800/40 text-xs border border-slate-200 dark:border-slate-800/60"
                title={`${doc.filename} (${(doc.file_size_bytes || 0) / 1020} KB) - ${doc.chunk_count} chunks`}
              >
                <div className="flex items-center gap-1.5 overflow-hidden mr-2">
                  <FileText size={12} className="text-indigo-500 shrink-0" />
                  <span className="truncate max-w-[130px] font-medium text-slate-600 dark:text-slate-300">{doc.filename}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] text-slate-400 font-mono">
                    {doc.chunk_count}c
                  </span>
                  <button
                    onClick={(e) => handleDeleteDocument(doc.id, e)}
                    className="text-slate-400 hover:text-rose-500"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              </div>
            ))}
            {documents.length === 0 && (
              <div className="text-center py-4 text-[11px] text-slate-400 italic">
                Library is empty
              </div>
            )}
          </div>
        </div>

        {/* Global theme controls footer */}
        <div className="border-t border-slate-200 dark:border-slate-800 p-4 flex items-center justify-between text-xs text-slate-400">
          <span>Offline mode</span>
          <button 
            onClick={() => setIsDark(!isDark)}
            className="p-1.5 rounded-full hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-100"
          >
            {isDark ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </aside>

      {/* 2. MAIN CHAT AREA */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative bg-white dark:bg-slate-950">
        
        {/* Top Header controls (Mobile layouts support + toggle switches) */}
        <header className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setIsDark(!isDark)}
              className="md:hidden p-1.5 rounded-full hover:bg-slate-200 dark:hover:bg-slate-800"
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <span className="md:hidden font-bold tracking-tight text-slate-800 dark:text-slate-100">Lexora</span>
          </div>

          {/* RAG Context Retrieval Mode Toggle Switch */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setUseRag(!useRag)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold tracking-wide transition-all ${
                useRag 
                  ? 'bg-indigo-600/10 text-indigo-600 border-indigo-600/20 dark:bg-indigo-500/10 dark:text-indigo-400 dark:border-indigo-500/20' 
                  : 'text-slate-400 border-slate-200 dark:border-slate-800'
              }`}
            >
              <Database size={13} />
              <span>Use Document RAG {useRag ? '(ON)' : '(OFF)'}</span>
            </button>
          </div>
        </header>

        {/* Message Logs Feed Scroll View */}
        <div className="flex-1 overflow-y-auto px-4 md:px-12 py-6 scrollbar-thin">
          
          {/* Default suggestion dashboard when chat is empty */}
          {activeMessages.length === 0 && (
            <div className="max-w-2xl mx-auto py-16 flex flex-col items-center justify-center text-center">
              <div className="h-16 w-16 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-500 mb-6 border border-indigo-500/20 shadow-xl shadow-indigo-500/5 animate-pulse">
                <Sparkles size={32} />
              </div>
              <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-slate-800 to-slate-400 dark:from-slate-100 dark:to-slate-400 bg-clip-text text-transparent mb-2">
                Lexora Offline Document Assistant
              </h2>
              <p className="text-[14px] text-slate-500 dark:text-slate-400 max-w-md mb-8">
                Ask questions about your uploaded PDFs, DOCX files, spreadsheets, or plain text document records. Fully local and private.
              </p>

              {/* Suggester buttons */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-xl">
                {[
                  "Summarize key aspects of my document.",
                  "Analyze trends and list data values.",
                  "Extract core definitions and concepts.",
                  "Explain equations or code snippets present."
                ].map((sug, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setInputText(sug);
                    }}
                    className="text-left py-3 px-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100/40 dark:bg-slate-900/40 hover:bg-slate-200/50 dark:hover:bg-slate-800/50 hover:border-slate-300 dark:hover:border-slate-700 transition-colors text-xs text-slate-600 dark:text-slate-300 font-medium cursor-pointer"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Render bubbles */}
          {activeMessages.map((msg, index) => {
            const isUser = msg.role === 'user';
            const isLatestMsg = index === activeMessages.length - 1;
            
            return (
              <div key={index} className={`flex gap-4 max-w-3xl mx-auto mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
                
                {/* Assistant avatar bubble */}
                {!isUser && (
                  <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-lg shadow-indigo-600/10">
                    <Sparkles size={14} />
                  </div>
                )}

                {/* Text body area container */}
                <div className={`flex flex-col group ${isUser ? 'max-w-[80%]' : 'max-w-[90%] flex-1'}`}>
                  <div className={`py-3 px-4 rounded-2xl ${
                    isUser 
                      ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/10' 
                      : 'bg-slate-100 dark:bg-slate-900 rounded-bl-none border border-slate-200 dark:border-slate-800/80'
                  }`}>
                    {isUser ? (
                      <p className="text-[14.5px] whitespace-pre-wrap select-text">{msg.content}</p>
                    ) : (
                      <div className="relative">
                        {/* Markdown Parser formatting */}
                        <Markdown content={msg.content} />
                        
                        {/* Generation loading cursor blinking */}
                        {isLatestMsg && isGenerating && msg.content === '' && (
                          <div className="flex items-center gap-1 text-slate-400 dark:text-slate-500 py-1 text-sm font-medium">
                            <Loader2 size={13} className="animate-spin text-indigo-500" />
                            <span>Lexora is writing...</span>
                          </div>
                        )}
                        {isLatestMsg && isGenerating && msg.content !== '' && (
                          <span className="inline-block h-3.5 w-1.5 bg-indigo-500 dark:bg-indigo-400 ml-1 animate-pulse" />
                        )}
                      </div>
                    )}
                  </div>

                  {/* Actions (Copy response action button) */}
                  {!isUser && msg.content && (
                    <div className="flex items-center gap-2 mt-1.5 ml-2 text-xs text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => copyToClipboard(msg.content, index)}
                        className="flex items-center gap-1 hover:text-slate-200 transition-colors py-0.5 px-1.5 rounded hover:bg-slate-800"
                        title="Copy entire response"
                      >
                        {copiedId === index ? (
                          <>
                            <Check size={11} className="text-emerald-400" />
                            <span className="text-emerald-400 text-[11px]">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy size={11} />
                            <span className="text-[11px]">Copy response</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>

                {/* User avatar */}
                {isUser && (
                  <div className="h-8 w-8 rounded-lg bg-slate-300 dark:bg-slate-800 flex items-center justify-center font-bold text-xs text-slate-600 dark:text-slate-300 shrink-0">
                    U
                  </div>
                )}
              </div>
            );
          })}
          
          <div ref={chatBottomRef} />
        </div>

        {/* Message Input and controls Area container */}
        <div className="px-4 md:px-12 py-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
          
          {/* Connect check overlay notice */}
          {!backendHealthy && backendHealthy !== null && (
            <div className="max-w-3xl mx-auto flex items-center gap-2 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-500 dark:text-rose-400 mb-3">
              <AlertCircle size={14} className="shrink-0" />
              <span>Lexora backend could not be reached. Ensure the FastAPI backend is running locally at port 8000.</span>
            </div>
          )}

          <div className="max-w-3xl mx-auto relative flex flex-col">
            
            {/* Input field and actions */}
            <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800/80 rounded-2xl p-2 relative shadow-inner">
              
              {/* Mobile upload toggle */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="md:hidden p-2 rounded-xl text-slate-400 hover:text-indigo-500 hover:bg-slate-200/50 dark:hover:bg-slate-800/50 transition-colors"
              >
                <Upload size={16} />
              </button>

              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={isUploading ? "Uploading file..." : "Message Lexora..."}
                disabled={isUploading}
                rows={1}
                className="flex-1 bg-transparent border-0 outline-0 ring-0 focus:ring-0 focus:outline-none py-2 px-3 text-[14px] text-slate-800 dark:text-slate-100 placeholder-slate-400 max-h-36 resize-none scrollbar-none"
              />

              {/* Executing actions button: Submit or Abort stream */}
              <div className="flex items-center self-end">
                {isGenerating ? (
                  <button
                    onClick={handleStopGenerating}
                    className="p-2.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-white shadow transition-all active:scale-[0.96]"
                    title="Stop generating"
                  >
                    <Square size={14} fill="currentColor" />
                  </button>
                ) : (
                  <button
                    onClick={() => handleSendMessage()}
                    disabled={!inputText.trim() || isUploading}
                    className={`p-2.5 rounded-xl text-white shadow-lg transition-all active:scale-[0.96] ${
                      inputText.trim() && !isUploading
                        ? 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-600/10'
                        : 'bg-slate-300 dark:bg-slate-800 text-slate-400 dark:text-slate-600 shadow-none cursor-default'
                    }`}
                  >
                    <Send size={14} />
                  </button>
                )}
              </div>
            </div>
            
            {/* Disclaimer footer */}
            <span className="text-[10px] text-slate-400 text-center mt-2 tracking-wide font-sans">
              Lexora is completely offline and private. Powered by Qwen3:4b and BGE-small-en-v1.5.
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}
