import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Mail, Send, X, Loader2, Sparkles, ArrowRight } from 'lucide-react';
import { InboxItem } from './components/InboxItem';

interface Email {
  thread_id: string;
  subject: string;
  sender: string;
  history: string;
}

const API_BASE = ''; // Use relative path for unified port deployment

const parseMessage = (text: string) => {
  let time = '';
  const lines = text.split('\n');
  let foundHeader = false;
  
  const cleanedLines = lines.filter(line => {
    const trimmed = line.trim();
    
    // Skip completely blank lines that follow a header
    if (foundHeader && trimmed === '') {
      return false;
    }
    
    // Match email headers: "On [Date] at [Time] [Sender Name] <email> wrote:"
    const isHeader = trimmed.startsWith('On ') && trimmed.includes('wrote:');

    if (isHeader) {
      foundHeader = true;
      // Extract time from: "On [Date] at [Time] [Sender] wrote:"
      const timeMatch = trimmed.match(/at\s+(\d{1,2}:\d{2}\s?(?:AM|PM|am|pm))/i);
      if (timeMatch) {
        time = timeMatch[1];
      }
      return false; // Remove header line
    }
    
    foundHeader = false;
    return !trimmed.startsWith('>'); // Remove quote lines
  });

  return {
    text: cleanedLines.join('\n').trim(),
    time
  };
};

const App: React.FC = () => {
  // ... (unchanged state hooks) ...

  // ... (unchanged useEffects and handlers) ...
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [draft, setDraft] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const draftEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchEmails();
  }, []);

  useEffect(() => {
    if ((isGenerating || draft) && draftEndRef.current) {
      draftEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isGenerating, draft]);

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/emails`);
      setEmails(res.data);
    } catch (err) {
      console.error("Error fetching emails", err);
    } finally {
      setLoading(false);
    }
  };

  const selectEmail = async (email: Email) => {
    if (selectedEmail?.thread_id === email.thread_id) return;

    setSelectedEmail(email);
    setDraft('');
    setError(null);
    setIsGenerating(true);

    const contentContainer = document.getElementById('content-container');
    if (contentContainer) contentContainer.scrollTo(0, 0);

    try {
      const res = await axios.post(`${API_BASE}/generate_draft`, email);
      setDraft(res.data.draft);
    } catch (err: any) {
      console.error("Error generating draft", err);
      setError(err.response?.data?.detail || "Failed to generate draft.");
    } finally {
      setIsGenerating(false);
    }
  };

  const sendDraft = async () => {
    if (!selectedEmail || !draft) return;
    setIsSending(true);
    try {
      await axios.post(`${API_BASE}/send_email`, {
        thread_id: selectedEmail.thread_id,
        response: draft,
        recipient: selectedEmail.sender,
        subject: selectedEmail.subject
      });
      setEmails(emails.filter(e => e.thread_id !== selectedEmail.thread_id));
      setSelectedEmail(null);
      setDraft('');
    } catch (err) {
      console.error("Error sending draft", err);
    } finally {
      setIsSending(false);
    }
  };

  const cancelDraft = () => {
    setDraft('');
    setError(null);
  };

  const getSenderInitials = (sender: string) => {
    return sender.split('<')[0].trim()[0].toUpperCase();
  };

  const getSenderName = (sender: string) => {
    return sender.split('<')[0].trim();
  };

  return (
    <div className="flex w-full h-screen bg-[#F9F8F6] text-[#121212] overflow-hidden selection:bg-black selection:text-white">

      {/* Left Panel: Inbox */}
      <div className="w-[380px] min-w-[320px] bg-white border-r border-[#EFEFEF] flex flex-col h-full z-20 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
        <div className="p-6 pb-4 flex items-baseline justify-between sticky top-0 bg-white/95 backdrop-blur-sm z-10 border-b border-gray-50">
          <h1 className="font-display text-4xl font-extrabold tracking-tight">Inbox</h1>
          <span className="text-xs font-bold tracking-widest text-gray-400">{emails.length} UNREAD</span>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-hide space-y-1">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-40 gap-3">
              <Loader2 className="animate-spin text-gray-300" />
              <span className="text-xs text-gray-400 font-medium tracking-wide">FETCHING UNREAD EMAILS...</span>
            </div>
          ) : emails.length === 0 ? (
            <div className="p-10 text-center">
              <p className="text-sm text-gray-400 font-medium">All caught up. No new emails.</p>
            </div>
          ) : (
            emails.map((email) => (
              <InboxItem
                key={email.thread_id}
                sender={getSenderName(email.sender)}
                subject={email.subject}
                preview={email.history.split('\n')[0]}
                isActive={selectedEmail?.thread_id === email.thread_id}
                onClick={() => selectEmail(email)}
              />
            ))
          )}
        </div>
      </div>

      {/* Right Panel: Content */}
      <div className="flex-1 flex flex-col relative h-full bg-[#F9F8F6]">
        {selectedEmail ? (
          <>
            <div id="content-container" className="flex-1 overflow-y-auto scrollbar-hide">
              <div className="max-w-4xl mx-auto w-full p-6 pb-6">

                {/* Header */}
                <header className="mb-4 animate-fade-in space-y-2">
                  <h2 className="font-display text-3xl font-bold leading-tight tracking-tight text-black">
                    {selectedEmail.subject}
                  </h2>

                  <div className="flex items-center gap-3 pt-1">
                    <div className="w-8 h-8 rounded-full bg-black text-white flex items-center justify-center font-display font-bold text-sm ring-2 ring-gray-100">
                      {getSenderInitials(selectedEmail.sender)}
                    </div>
                    <div className="flex flex-col">
                      <span className="font-bold text-lg">{getSenderName(selectedEmail.sender)}</span>
                    </div>
                  </div>
                </header>

                {/* History */}
                <div className="mb-4 animate-fade-in space-y-3" style={{ animationDelay: '0.1s' }}>
                  {selectedEmail.history.split('---').map((msg, i, arr) => {
                    if (i % 2 === 0) {
                      const { text: cleanQuestion, time: questionTime } = parseMessage(msg);
                      // Look ahead for response
                      const rawResponse = arr[i + 1] || '';
                      const { text: cleanResponse, time: responseTime } = parseMessage(rawResponse);
                      const hasResponse = !!cleanResponse;

                      return (
                        <div key={i} className="space-y-2">
                          {/* Email/Question Box */}
                          <div className="bg-gray-100 border border-gray-200 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start gap-3 mb-2">
                              {questionTime && (
                                <span className="text-[10px] font-bold text-gray-400 tracking-wide">
                                  {questionTime}
                                </span>
                              )}
                            </div>
                            <div className="text-[15px] leading-relaxed text-gray-800 font-body">
                              {cleanQuestion}
                            </div>
                          </div>

                          {/* Response Box */}
                          {hasResponse && (
                            <div className="bg-white border border-gray-100 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow ml-4">
                              <div className="flex justify-between items-start gap-3 mb-2">
                                <span className="text-xs font-bold tracking-wider uppercase text-gray-600">Your Response</span>
                                {responseTime && (
                                  <span className="text-[10px] font-bold text-gray-400 tracking-wide">
                                    {responseTime}
                                  </span>
                                )}
                              </div>
                              <div className="text-[15px] leading-relaxed text-gray-700 font-body">
                                {cleanResponse}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            </div>

            {/* Draft Section - Sticky at Bottom */}
            <div className="border-t border-gray-200 bg-[#F9F8F6]">
              <div ref={draftEndRef} className={`
                  sticky bottom-0 relative overflow-hidden rounded-[24px] bg-white m-4
                  ${isGenerating ? 'shadow-none border border-gray-200' : 'shadow-[0_20px_40px_-12px_rgba(0,0,0,0.1)] border border-gray-100'}
                  transition-all duration-500
              `}>

                {/* AI Status Bar */}
                <div className="flex items-center justify-between px-4 py-1 border-b border-gray-100 bg-gray-50/50">
                  <div className="flex items-center gap-2">
                    <Sparkles size={16} className={isGenerating ? "animate-pulse text-blue-600" : "text-black"} />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">
                      {isGenerating ? 'Reviewing context & drafting...' : error ? 'Generation Error' : 'AI Draft'}
                    </span>
                  </div>
                  {(draft || error) && !isGenerating && (
                    <button onClick={cancelDraft} className="p-1 hover:bg-gray-200 rounded-full transition-colors">
                      <X size={14} />
                    </button>
                  )}
                </div>

                {/* Content Area */}
                <div className="p-2">
                  {isGenerating ? (
                    <div className="h-48 flex flex-col items-center justify-center gap-4">
                      <Loader2 className="animate-spin text-black" size={32} />
                    </div>
                  ) : error ? (
                    <div className="p-6 text-center">
                      <p className="text-red-500 font-medium mb-4">{error}</p>
                      <button onClick={() => selectEmail(selectedEmail!)} className="underline font-bold text-sm">Try Again</button>
                    </div>
                  ) : (
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      className="w-full min-h-[160px] p-3 text-[15px] leading-relaxed text-gray-900 bg-transparent border-none focus:ring-0 resize-none font-body placeholder:text-gray-300"
                      placeholder="Draft will appear here..."
                    />
                  )}
                </div>

                {/* Actions */}
                {!isGenerating && !error && draft && (
                  <div className="p-1.5 bg-gray-50/50 flex justify-end gap-2 border-t border-gray-100">
                    <button
                      onClick={sendDraft}
                      disabled={isSending}
                      className="bg-black text-white px-4 py-1.5 rounded-full font-bold text-xs flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-md hover:shadow-lg disabled:opacity-70 disabled:hover:scale-100"
                    >
                      {isSending ? <Loader2 className="animate-spin" size={14} /> : <Send size={14} />}
                      <span>Send Reply</span>
                      <ArrowRight size={14} className="opacity-60" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-300 gap-6 animate-fade-in">
            <div className="w-24 h-24 rounded-full bg-gray-100 flex items-center justify-center">
              <Mail size={48} strokeWidth={1} className="text-gray-400" />
            </div>
            <p className="font-display text-2xl font-bold text-gray-400">Select a message</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
