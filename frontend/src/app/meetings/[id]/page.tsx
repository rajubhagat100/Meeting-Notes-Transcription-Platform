"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import {
  fetchMeetingDetail,
  toggleSegmentHighlight,
  addComment,
  deleteComment,
  addActionItem,
  updateActionItem,
  deleteActionItem,
  askAI,
  fetchChatHistory,
  getExportUrl,
  MeetingDetail,
  TranscriptSegment,
  Comment,
  ActionItem,
  ChatMessage
} from "@/lib/api";
import {
  ArrowLeft,
  Calendar,
  Clock,
  Download,
  MessageSquare,
  Star,
  Send,
  Plus,
  Loader2,
  Trash2,
  CheckCircle,
  Play,
  Pause,
  ChevronDown,
  Moon,
  Sun,
  Search
} from "lucide-react";

export default function MeetingPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Interactive Filters
  const [activeTab, setActiveTab] = useState<"ai-notes" | "ask-ai" | "comments">("ai-notes");
  const [transcriptSearch, setTranscriptSearch] = useState("");
  const [isThemeLight, setIsThemeLight] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  // Chatbot state
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  // Inline Comment State
  const [commentingSegmentId, setCommentingSegmentId] = useState<number | null>(null);
  const [commentAuthor, setCommentAuthor] = useState("Raju Bhagat"); // Default User
  const [commentText, setCommentText] = useState("");

  // Action Item Editor State
  const [newActionText, setNewActionText] = useState("");
  const [newActionAssignee, setNewActionAssignee] = useState("");

  // Audio/Video player reference
  const mediaRef = useRef<HTMLVideoElement | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  // Load meeting details
  const loadMeeting = async () => {
    try {
      const data = await fetchMeetingDetail(id);
      setMeeting(data);
      setDuration(data.duration_seconds || 120);
      setChatHistory(data.chat_messages || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadMeeting();
    }
  }, [id]);

  // Scroll to bottom of chat
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory, activeTab]);

  // Theme switch handler
  const toggleTheme = () => {
    const isLight = !isThemeLight;
    setIsThemeLight(isLight);
    if (isLight) {
      document.body.classList.add("light-theme");
    } else {
      document.body.classList.remove("light-theme");
    }
  };

  // Video playback time updates
  const handleTimeUpdate = () => {
    if (mediaRef.current) {
      setCurrentTime(mediaRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (mediaRef.current) {
      setDuration(mediaRef.current.duration || meeting?.duration_seconds || 120);
    }
  };

  const togglePlay = () => {
    if (mediaRef.current) {
      if (isPlaying) {
        mediaRef.current.pause();
      } else {
        mediaRef.current.play().catch(e => console.log("Play failed: ", e));
      }
      setIsPlaying(!isPlaying);
    }
  };

  // Click on segment seeks player
  const handleSegmentClick = (startTime: number) => {
    if (mediaRef.current) {
      mediaRef.current.currentTime = startTime;
      setCurrentTime(startTime);
      if (mediaRef.current.paused) {
        mediaRef.current.play().catch(() => {});
        setIsPlaying(true);
      }
    }
  };

  // Timeline Slider binding
  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setCurrentTime(val);
    if (mediaRef.current) {
      mediaRef.current.currentTime = val;
    }
  };

  // Formatter utilities
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Toggle Highlight
  const handleToggleHighlight = async (segmentId: number, currentStatus: boolean) => {
    try {
      const updatedSegment = await toggleSegmentHighlight(id, segmentId, !currentStatus);
      if (meeting) {
        setMeeting({
          ...meeting,
          transcript_segments: meeting.transcript_segments.map(seg =>
            seg.id === segmentId ? { ...seg, highlighted: updatedSegment.highlighted } : seg
          )
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Add Comment
  const handleAddComment = async (segmentId: number) => {
    if (!commentText.trim()) return;
    try {
      const newComment = await addComment(id, segmentId, commentAuthor, commentText);
      if (meeting) {
        setMeeting({
          ...meeting,
          transcript_segments: meeting.transcript_segments.map(seg =>
            seg.id === segmentId ? { ...seg, comments: [...seg.comments, newComment] } : seg
          )
        });
      }
      setCommentingSegmentId(null);
      setCommentText("");
    } catch (err) {
      console.error(err);
    }
  };

  // Delete Comment
  const handleDeleteComment = async (commentId: number, segmentId: number) => {
    try {
      await deleteComment(commentId);
      if (meeting) {
        setMeeting({
          ...meeting,
          transcript_segments: meeting.transcript_segments.map(seg =>
            seg.id === segmentId ? { ...seg, comments: seg.comments.filter(c => c.id !== commentId) } : seg
          )
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Update Action Item Complete
  const handleToggleAction = async (itemId: number, currentCompleted: boolean) => {
    try {
      const updatedItem = await updateActionItem(itemId, { completed: !currentCompleted });
      if (meeting) {
        setMeeting({
          ...meeting,
          action_items: meeting.action_items.map(item =>
            item.id === itemId ? { ...item, completed: updatedItem.completed } : item
          )
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Add Action Item Manually
  const handleAddAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newActionText.trim()) return;
    try {
      const newItem = await addActionItem(id, newActionText, newActionAssignee || null);
      if (meeting) {
        setMeeting({
          ...meeting,
          action_items: [...meeting.action_items, newItem]
        });
      }
      setNewActionText("");
      setNewActionAssignee("");
    } catch (err) {
      console.error(err);
    }
  };

  // Delete Action Item
  const handleDeleteAction = async (itemId: number) => {
    try {
      await deleteActionItem(itemId);
      if (meeting) {
        setMeeting({
          ...meeting,
          action_items: meeting.action_items.filter(item => item.id !== itemId)
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Ask AI Chat trigger
  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;
    
    const userQuery = chatInput;
    setChatInput("");
    setChatLoading(true);

    // Append local user message first
    const tempUserMsg: ChatMessage = {
      id: Date.now(),
      meeting_id: id,
      sender: "user",
      message: userQuery,
      created_at: new Date().toISOString()
    };
    setChatHistory(prev => [...prev, tempUserMsg]);

    try {
      const aiResponse = await askAI(id, userQuery);
      setChatHistory(prev => [...prev, aiResponse]);
    } catch (err) {
      console.error(err);
      const errResponse: ChatMessage = {
        id: Date.now() + 1,
        meeting_id: id,
        sender: "ai",
        message: "Failed to communicate with AI chat backend. Make sure FastAPI server is running.",
        created_at: new Date().toISOString()
      };
      setChatHistory(prev => [...prev, errResponse]);
    } finally {
      setChatLoading(false);
    }
  };

  // Transcript string highlight parser
  const highlightSearchMatches = (text: string, search: string) => {
    if (!search.trim()) return text;
    
    const escapedSearch = search.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
    const parts = text.split(new RegExp(`(${escapedSearch})`, "gi"));
    
    return parts.map((part, index) => 
      part.toLowerCase() === search.toLowerCase() ? (
        <span key={index} className="highlight-match">{part}</span>
      ) : part
    );
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <Loader2 size={36} className="animate-spin" style={{ color: "var(--color-accent)", animation: "spin 1s linear infinite" }} />
        <span style={{ marginTop: "12px", color: "var(--text-secondary)" }}>Analyzing transcript...</span>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div style={{ padding: "40px", textAlign: "center" }}>
        <h2>Meeting not found</h2>
        <Link href="/" className="btn-primary" style={{ marginTop: "20px", display: "inline-block" }}>
          Return to Dashboard
        </Link>
      </div>
    );
  }

  // Extract all inline comments for unified list view
  const allComments = meeting.transcript_segments.flatMap(seg => 
    seg.comments.map(c => ({
      ...c,
      segmentText: seg.text,
      speaker: seg.speaker,
      startTime: seg.start_time
    }))
  );

  // Extract all starred segments
  const starredSegments = meeting.transcript_segments.filter(seg => seg.highlighted);

  // Determine current active transcript segment based on video currentTime
  const activeSegment = meeting.transcript_segments.find(
    seg => currentTime >= seg.start_time && currentTime < seg.end_time
  );

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        
        {/* Header */}
        <header className="header">
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <button 
              onClick={() => router.push("/")}
              style={{ background: "none", border: "none", color: "var(--text-primary)", cursor: "pointer" }}
              title="Go Back"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 700 }}>{meeting.title}</h2>
              <div style={{ display: "flex", gap: "12px", alignItems: "center", fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px" }}>
                <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <Calendar size={11} /> {meeting.date}
                </span>
                <span>•</span>
                <span>{meeting.participants.join(", ")}</span>
              </div>
            </div>
          </div>

          <div className="header-actions">
            <button className="theme-toggle-btn" onClick={toggleTheme}>
              {isThemeLight ? <Moon size={18} /> : <Sun size={18} />}
            </button>

            {/* Export Dropdown */}
            <div className="export-menu-container">
              <button 
                className="btn-secondary" 
                onClick={() => setExportOpen(!exportOpen)}
                style={{ display: "flex", alignItems: "center", gap: "8px" }}
                id="export-dropdown-btn"
              >
                <Download size={14} />
                <span>Export</span>
                <ChevronDown size={12} />
              </button>

              {exportOpen && (
                <div className="export-menu-options" id="export-options-list">
                  <a 
                    href={getExportUrl(meeting.id, "md")} 
                    className="export-option-btn" 
                    onClick={() => setExportOpen(false)}
                    download
                  >
                    Markdown (.md)
                  </a>
                  <a 
                    href={getExportUrl(meeting.id, "txt")} 
                    className="export-option-btn" 
                    onClick={() => setExportOpen(false)}
                    download
                  >
                    Text (.txt)
                  </a>
                  <a 
                    href={getExportUrl(meeting.id, "pdf")} 
                    className="export-option-btn" 
                    onClick={() => setExportOpen(false)}
                    download
                  >
                    PDF (.pdf)
                  </a>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content layout split screen */}
        <main className="content-body" style={{ height: "calc(100vh - var(--header-height))", padding: "24px 32px 0 32px" }}>
          <div className="detail-layout">
            
            {/* Left Panel: Media Player & Transcript */}
            <section className="left-panel">
              
              {/* HTML5 Media Player */}
              <div className="player-container">
                <video 
                  ref={mediaRef}
                  className="video-element"
                  src={meeting.video_url || "https://www.w3schools.com/html/mov_bbb.mp4"}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onClick={togglePlay}
                />
                
                <div className="audio-player-wrapper">
                  <button className="play-button" onClick={togglePlay} id="media-play-pause-btn">
                    {isPlaying ? <Pause size={18} /> : <Play size={18} fill="white" />}
                  </button>

                  <div className="timeline-slider-container">
                    <input 
                      type="range" 
                      className="timeline-slider"
                      min={0}
                      max={duration || 100}
                      step={0.1}
                      value={currentTime}
                      onChange={handleSliderChange}
                      id="media-timeline-slider"
                    />
                    <div className="time-display">
                      <span>{formatTime(currentTime)}</span>
                      <span>{formatTime(duration)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Interactive Transcript */}
              <div className="transcript-container">
                <div className="transcript-header">
                  <h3 style={{ fontSize: "16px", fontWeight: 700 }}>Interactive Transcript</h3>
                  
                  {/* Search inside transcript */}
                  <div className="transcript-search-wrapper">
                    <Search size={14} className="search-icon-inside" />
                    <input 
                      type="text" 
                      className="transcript-search-input"
                      id="transcript-search-input"
                      placeholder="Search within transcript..." 
                      value={transcriptSearch}
                      onChange={(e) => setTranscriptSearch(e.target.value)}
                    />
                  </div>
                </div>

                <div className="transcript-list" id="transcript-list-viewer">
                  {meeting.transcript_segments.map((seg) => {
                    const isActive = activeSegment?.id === seg.id;
                    const matchesSearch = transcriptSearch.trim() && 
                      seg.text.toLowerCase().includes(transcriptSearch.toLowerCase());
                    
                    return (
                      <div 
                        key={seg.id} 
                        className={`transcript-item ${isActive ? "active" : ""}`}
                        id={`transcript-segment-${seg.id}`}
                        onClick={() => handleSegmentClick(seg.start_time)}
                        style={{ borderLeft: isActive ? "3px solid var(--color-accent)" : matchesSearch ? "3px dashed var(--color-warning)" : "3px solid transparent" }}
                      >
                        <div className="transcript-meta">
                          <span className="transcript-speaker">{seg.speaker}</span>
                          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                            <span className="transcript-time">{formatTime(seg.start_time)}</span>
                            
                            {/* Star / Highlight Segment Button */}
                            <button 
                              className={`segment-star-btn ${seg.highlighted ? "starred" : ""}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleToggleHighlight(seg.id, seg.highlighted);
                              }}
                              title="Star segment"
                            >
                              <Star size={13} fill={seg.highlighted ? "currentColor" : "none"} />
                            </button>

                            {/* Comment Button */}
                            <button 
                              className="segment-comment-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                setCommentingSegmentId(commentingSegmentId === seg.id ? null : seg.id);
                              }}
                              title="Add Comment"
                            >
                              <MessageSquare size={13} />
                            </button>
                          </div>
                        </div>

                        {/* Text showing highlighted matches if searched */}
                        <p className="transcript-text">
                          {highlightSearchMatches(seg.text, transcriptSearch)}
                        </p>

                        {/* Segment Comments */}
                        {seg.comments && seg.comments.length > 0 && (
                          <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "6px" }}>
                            {seg.comments.map((comm) => (
                              <div key={comm.id} className="comment-bubble-item" style={{ margin: 0, padding: "8px 12px" }}>
                                <div className="comment-meta">
                                  <span className="comment-author" style={{ fontSize: "11px" }}>{comm.author}</span>
                                  <button 
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteComment(comm.id, seg.id);
                                    }} 
                                    style={{ background: "none", border: "none", color: "var(--color-danger)", cursor: "pointer" }}
                                  >
                                    <Trash2 size={11} />
                                  </button>
                                </div>
                                <p className="comment-text" style={{ fontSize: "12px" }}>{comm.text}</p>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Inline Comment Input Box */}
                        {commentingSegmentId === seg.id && (
                          <div 
                            style={{ display: "flex", gap: "8px", marginTop: "10px" }}
                            onClick={(e) => e.stopPropagation()} // Prevent clicking input seeking video
                          >
                            <input 
                              type="text" 
                              className="form-input" 
                              style={{ padding: "6px 10px", fontSize: "12px" }}
                              placeholder="Write a comment..." 
                              value={commentText}
                              onChange={(e) => setCommentText(e.target.value)}
                            />
                            <button 
                              className="btn-primary" 
                              style={{ padding: "6px 12px", fontSize: "12px" }}
                              onClick={() => handleAddComment(seg.id)}
                            >
                              Add
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            {/* Right Panel: Tabs (AI Notes, Ask AI chatbot, Comments tracker) */}
            <section className="right-panel">
              <div className="tabs-header">
                <button 
                  className={`tab-btn ${activeTab === "ai-notes" ? "active" : ""}`}
                  onClick={() => setActiveTab("ai-notes")}
                  id="tab-ai-notes"
                >
                  AI Notes
                </button>
                <button 
                  className={`tab-btn ${activeTab === "ask-ai" ? "active" : ""}`}
                  onClick={() => setActiveTab("ask-ai")}
                  id="tab-ask-ai"
                >
                  Ask AI
                </button>
                <button 
                  className={`tab-btn ${activeTab === "comments" ? "active" : ""}`}
                  onClick={() => setActiveTab("comments")}
                  id="tab-comments-highlights"
                >
                  Comments & Starred
                </button>
              </div>

              <div className="tab-content">
                
                {/* 1. AI NOTES TAB */}
                {activeTab === "ai-notes" && (
                  <div id="ai-notes-tab-content">
                    {meeting.summary ? (
                      <>
                        <h4 className="summary-heading" style={{ marginTop: 0 }}>Overview Summary</h4>
                        <div className="summary-overview">
                          {meeting.summary.overview}
                        </div>

                        {/* Chapters Outline */}
                        {meeting.summary.chapters && meeting.summary.chapters.length > 0 && (
                          <>
                            <h4 className="summary-heading">Chapters Outline</h4>
                            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                              {meeting.summary.chapters.map((ch, idx) => (
                                <div 
                                  key={idx} 
                                  className="chapter-item"
                                  style={{ cursor: "pointer" }}
                                  onClick={() => handleSegmentClick(ch.start_time)}
                                >
                                  <div className="chapter-title-row">
                                    <span className="chapter-title">{ch.title}</span>
                                    <span className="chapter-time">{formatTime(ch.start_time)}</span>
                                  </div>
                                  <p className="chapter-summary">{ch.summary}</p>
                                </div>
                              ))}
                            </div>
                          </>
                        )}
                      </>
                    ) : (
                      <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>No AI Summary generated.</p>
                    )}

                    {/* Action Items List */}
                    <div style={{ marginTop: "24px" }}>
                      <h4 className="summary-heading">Action Items & Tasks</h4>
                      <div className="action-items-list">
                        {meeting.action_items.map((item) => (
                          <div key={item.id} className="action-item-row" id={`action-item-row-${item.id}`}>
                            <input 
                              type="checkbox" 
                              className="action-checkbox"
                              checked={item.completed}
                              onChange={() => handleToggleAction(item.id, item.completed)}
                            />
                            <div className="action-text-container">
                              <span className={`action-text ${item.completed ? "completed" : ""}`}>
                                {item.text}
                              </span>
                              {item.assignee && (
                                <div>
                                  <span className="action-assignee">{item.assignee}</span>
                                </div>
                              )}
                            </div>
                            <button 
                              onClick={() => handleDeleteAction(item.id)}
                              style={{ background: "none", border: "none", color: "var(--color-danger)", cursor: "pointer", opacity: 0.7 }}
                              title="Delete task"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        ))}

                        {/* Add action item form */}
                        <form onSubmit={handleAddAction} style={{ 
                          display: "grid", 
                          gridTemplateColumns: "1.2fr 0.8fr auto", 
                          gap: "8px", 
                          marginTop: "16px",
                          alignItems: "center"
                        }}>
                          <input 
                            type="text" 
                            className="form-input" 
                            style={{ padding: "8px" }}
                            placeholder="Add action item..."
                            value={newActionText}
                            onChange={(e) => setNewActionText(e.target.value)}
                            required
                          />
                          <input 
                            type="text" 
                            className="form-input" 
                            style={{ padding: "8px" }}
                            placeholder="Assignee (optional)"
                            value={newActionAssignee}
                            onChange={(e) => setNewActionAssignee(e.target.value)}
                          />
                          <button type="submit" className="btn-primary" style={{ padding: "8px 12px" }}>
                            <Plus size={16} />
                          </button>
                        </form>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. ASK AI CHAT TAB */}
                {activeTab === "ask-ai" && (
                  <div className="chat-container" id="ask-ai-tab-content">
                    <div className="chat-history">
                      {chatHistory.length === 0 ? (
                        <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px 10px" }}>
                          <p style={{ fontSize: "14px" }}>Ask questions about this meeting, e.g.:</p>
                          <p style={{ fontSize: "12px", fontStyle: "italic", marginTop: "8px" }}>
                            \"What were the main engineering decisions?\"<br />
                            \"Summarize Bob's statements about architecture.\"
                          </p>
                        </div>
                      ) : (
                        chatHistory.map((msg) => (
                          <div 
                            key={msg.id} 
                            className={`chat-bubble ${msg.sender}`}
                          >
                            <strong>{msg.sender === "user" ? "You: " : "AI: "}</strong>
                            {msg.message}
                          </div>
                        ))
                      )}
                      
                      {chatLoading && (
                        <div className="chat-bubble ai" style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                          <Loader2 size={14} className="animate-spin" style={{ animation: "spin 1s linear infinite" }} />
                          <span>Thinking...</span>
                        </div>
                      )}
                      <div ref={chatBottomRef} />
                    </div>

                    <form onSubmit={handleAskQuestion} className="chat-input-form">
                      <input 
                        type="text" 
                        className="chat-input"
                        id="chat-input-box"
                        placeholder="Type question about this meeting..." 
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        disabled={chatLoading}
                      />
                      <button type="submit" className="chat-submit-btn" id="chat-submit-btn" disabled={chatLoading}>
                        <Send size={16} />
                      </button>
                    </form>
                  </div>
                )}

                {/* 3. COMMENTS & HIGH LIGHTS TAB */}
                {activeTab === "comments" && (
                  <div id="comments-tab-content" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                    
                    {/* Comments Tracker */}
                    <div>
                      <h4 className="summary-heading" style={{ marginTop: 0 }}>Comments Tracker</h4>
                      {allComments.length === 0 ? (
                        <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>No comments have been added to transcript segments yet.</p>
                      ) : (
                        allComments.map((comm) => (
                          <div key={comm.id} className="comment-bubble-item">
                            <div className="comment-meta">
                              <span className="comment-author">{comm.author}</span>
                              <span style={{ cursor: "pointer", color: "var(--color-accent)" }} onClick={() => handleSegmentClick(comm.startTime)}>
                                Seek to Segment
                              </span>
                            </div>
                            <p style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "8px" }}>
                              Regarding <strong>{comm.speaker}</strong>: \"{comm.segmentText}\"
                            </p>
                            <p className="comment-text">{comm.text}</p>
                          </div>
                        ))
                      )}
                    </div>

                    {/* Starred Segments Tracker */}
                    <div>
                      <h4 className="summary-heading">Starred Transcript Segments</h4>
                      {starredSegments.length === 0 ? (
                        <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>No transcript segments have been starred yet.</p>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                          {starredSegments.map((seg) => (
                            <div 
                              key={seg.id} 
                              className="comment-bubble-item" 
                              style={{ borderLeft: "3px solid var(--color-warning)", cursor: "pointer" }}
                              onClick={() => handleSegmentClick(seg.start_time)}
                            >
                              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "6px" }}>
                                <strong style={{ color: "var(--color-accent)" }}>{seg.speaker}</strong>
                                <span style={{ color: "var(--text-muted)" }}>{formatTime(seg.start_time)}</span>
                              </div>
                              <p className="comment-text" style={{ fontStyle: "italic" }}>\"{seg.text}\"</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                  </div>
                )}

              </div>
            </section>

          </div>
        </main>

      </div>
      
      <style jsx global>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
