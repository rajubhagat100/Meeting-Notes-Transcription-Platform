"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { 
  fetchMeetings, 
  createMeeting, 
  MeetingBrief, 
  fetchMeetings as fetchApiMeetings 
} from "@/lib/api";
import { 
  Search, 
  Plus, 
  Video, 
  Calendar, 
  Clock, 
  Filter, 
  Moon, 
  Sun, 
  Loader2, 
  X,
  Upload
} from "lucide-react";

export default function Dashboard() {
  const [meetings, setMeetings] = useState<MeetingBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedParticipant, setSelectedParticipant] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");
  const [sortBy, setSortBy] = useState("recency");
  const [isThemeLight, setIsThemeLight] = useState(false);
  
  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formTitle, setFormTitle] = useState("");
  const [formDate, setFormDate] = useState("");
  const [formDuration, setFormDuration] = useState(600); // 10 minutes default
  const [formParticipants, setFormParticipants] = useState("");
  const [formTranscript, setFormTranscript] = useState("");
  const [formFile, setFormFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load meetings
  const loadMeetings = async () => {
    try {
      setLoading(true);
      const data = await fetchMeetings(
        search,
        selectedParticipant || undefined,
        selectedTopic || undefined,
        sortBy
      );
      setMeetings(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMeetings();
  }, [search, selectedParticipant, selectedTopic, sortBy]);

  // Handle Theme Toggle
  const toggleTheme = () => {
    const isLight = !isThemeLight;
    setIsThemeLight(isLight);
    if (isLight) {
      document.body.classList.add("light-theme");
    } else {
      document.body.classList.remove("light-theme");
    }
  };

  // Handle Submit New Meeting
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle || !formDate) {
      alert("Please fill out Title and Date fields");
      return;
    }
    
    try {
      setIsSubmitting(true);
      const formData = new FormData();
      formData.append("title", formTitle);
      formData.append("date", formDate);
      formData.append("duration_seconds", formDuration.toString());
      
      // Parse participants
      const parts = formParticipants.split(",").map(p => p.trim()).filter(Boolean);
      formData.append("participants", JSON.stringify(parts));

      if (formFile) {
        formData.append("file", formFile);
      } else if (formTranscript) {
        formData.append("transcript_text", formTranscript);
      }

      await createMeeting(formData);
      setIsModalOpen(false);
      
      // Reset form
      setFormTitle("");
      setFormDate("");
      setFormDuration(600);
      setFormParticipants("");
      setFormTranscript("");
      setFormFile(null);
      
      // Refresh list
      loadMeetings();
    } catch (err) {
      console.error(err);
      alert("Failed to create meeting. Make sure the backend server is running.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    return `${minutes} min`;
  };

  // Get unique list of participants and tags for selectors from fetched meetings
  // (We'll hardcode some options based on our seed data, but dynamically add ones from state if matches found)
  const participantOptions = ["Alice", "Bob", "Carol", "David"];
  const topicOptions = [
    "Product Strategy", 
    "Next.js Architecture", 
    "UI Design System", 
    "Audio Sync API",
    "Database Schema",
    "SQLite Configuration"
  ];

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        
        {/* Header */}
        <header className="header">
          <div className="search-bar-container" id="global-search-container">
            <Search size={18} className="search-icon-inside" />
            <input 
              type="text" 
              className="search-bar-input" 
              id="global-search-input"
              placeholder="Search meetings by title or participant..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          
          <div className="header-actions">
            <button 
              className="theme-toggle-btn" 
              id="theme-toggle"
              onClick={toggleTheme}
              title="Toggle theme"
            >
              {isThemeLight ? <Moon size={18} /> : <Sun size={18} />}
            </button>
            <button 
              className="btn-primary" 
              id="new-meeting-btn"
              onClick={() => setIsModalOpen(true)}
              style={{ display: "flex", alignItems: "center", gap: "8px" }}
            >
              <Plus size={16} />
              <span>Transcribe Meeting</span>
            </button>
          </div>
        </header>

        {/* Content Body */}
        <main className="content-body">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
            <div>
              <h1 style={{ fontSize: "28px", fontWeight: 700, letterSpacing: "-0.5px" }}>Meetings Library</h1>
              <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
                Browse, search transcripts, and review AI notes from past meetings.
              </p>
            </div>
          </div>

          {/* Filtering and Sorting Controls */}
          <div style={{ 
            display: "flex", 
            gap: "16px", 
            flexWrap: "wrap", 
            alignItems: "center",
            backgroundColor: "var(--bg-secondary)",
            padding: "16px",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border-color)",
            marginBottom: "24px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Filter size={16} style={{ color: "var(--text-muted)" }} />
              <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>Filters:</span>
            </div>

            {/* Participant Filter */}
            <select 
              className="form-select" 
              id="participant-filter"
              style={{ width: "160px", padding: "6px 12px" }}
              value={selectedParticipant}
              onChange={(e) => setSelectedParticipant(e.target.value)}
            >
              <option value="">All Participants</option>
              {participantOptions.map(p => <option key={p} value={p}>{p}</option>)}
            </select>

            {/* Topic/Tag Filter */}
            <select 
              className="form-select" 
              id="topic-filter"
              style={{ width: "180px", padding: "6px 12px" }}
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
            >
              <option value="">All Topics</option>
              {topicOptions.map(t => <option key={t} value={t}>{t}</option>)}
            </select>

            {/* Sorting */}
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Sort by:</span>
              <select 
                className="form-select" 
                id="sort-select"
                style={{ width: "130px", padding: "6px 12px" }}
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="recency">Most Recent</option>
                <option value="duration">Duration</option>
                <option value="title">Alphabetical</option>
              </select>
            </div>
          </div>

          {/* Loader */}
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 0" }}>
              <Loader2 size={36} className="animate-spin" style={{ color: "var(--color-accent)", animation: "spin 1s linear infinite" }} />
              <span style={{ marginTop: "12px", color: "var(--text-secondary)" }}>Loading meetings...</span>
            </div>
          ) : meetings.length === 0 ? (
            <div style={{ 
              textAlign: "center", 
              padding: "60px", 
              backgroundColor: "var(--bg-secondary)", 
              border: "1px dashed var(--border-color)",
              borderRadius: "var(--radius-md)" 
            }}>
              <Video size={48} style={{ color: "var(--text-muted)", margin: "0 auto 16px auto" }} />
              <h3>No meetings found</h3>
              <p style={{ color: "var(--text-secondary)", marginTop: "8px", fontSize: "14px" }}>
                Try adjusting your search criteria or transcribe a new meeting.
              </p>
            </div>
          ) : (
            /* Meeting Cards Grid */
            <div className="meeting-grid">
              {meetings.map((meeting) => (
                <Link key={meeting.id} href={`/meetings/${meeting.id}`}>
                  <div className="meeting-card" id={`meeting-card-${meeting.id}`}>
                    <div className="meeting-card-header">
                      <div className="meeting-card-duration">
                        {formatDuration(meeting.duration_seconds)}
                      </div>
                      <span className="meeting-card-date">
                        <Calendar size={12} />
                        {meeting.date}
                      </span>
                    </div>

                    <h3 className="meeting-card-title">{meeting.title}</h3>

                    <div className="meeting-card-participants">
                      {meeting.participants.map((part, index) => (
                        <span key={index} className="participant-tag">
                          {part}
                        </span>
                      ))}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </main>

        {/* Create Meeting / Transcribe Modal */}
        {isModalOpen && (
          <div className="modal-overlay" id="new-meeting-modal">
            <div className="modal-content">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h2 className="modal-title">Transcribe New Meeting</h2>
                <button 
                  onClick={() => setIsModalOpen(false)} 
                  style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
                >
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div className="form-group">
                  <label className="form-label">Meeting Title *</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    id="meeting-title-input"
                    placeholder="e.g. Weekly Design Sync"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    required 
                  />
                </div>

                <div className="form-group" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div>
                    <label className="form-label">Date *</label>
                    <input 
                      type="date" 
                      className="form-input" 
                      id="meeting-date-input"
                      value={formDate}
                      onChange={(e) => setFormDate(e.target.value)}
                      required 
                    />
                  </div>
                  <div>
                    <label className="form-label">Duration (seconds)</label>
                    <input 
                      type="number" 
                      className="form-input" 
                      id="meeting-duration-input"
                      value={formDuration}
                      onChange={(e) => setFormDuration(Number(e.target.value))}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Participants (comma-separated)</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    id="meeting-participants-input"
                    placeholder="Alice, Bob, Carol"
                    value={formParticipants}
                    onChange={(e) => setFormParticipants(e.target.value)}
                  />
                </div>

                <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "12px" }}>
                  <span className="form-label" style={{ marginBottom: "8px", display: "block" }}>Add Transcript Content (Choose One):</span>
                  
                  {/* File Upload Option */}
                  <div className="form-group" style={{ marginBottom: "12px" }}>
                    <label className="form-label" style={{ fontSize: "11px", color: "var(--text-muted)" }}>Upload Transcript File (.vtt, .txt)</label>
                    <div style={{ 
                      border: "1px dashed var(--border-color)", 
                      padding: "12px", 
                      borderRadius: "var(--radius-sm)", 
                      textAlign: "center",
                      backgroundColor: "var(--bg-primary)"
                    }}>
                      <input 
                        type="file" 
                        accept=".txt,.vtt" 
                        style={{ display: "none" }} 
                        id="transcript-file-uploader" 
                        onChange={(e) => setFormFile(e.target.files?.[0] || null)}
                      />
                      <label htmlFor="transcript-file-uploader" style={{ cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
                        <Upload size={20} style={{ color: "var(--color-accent)" }} />
                        <span style={{ fontSize: "12px", fontWeight: 500 }}>
                          {formFile ? formFile.name : "Select VTT or text file"}
                        </span>
                      </label>
                    </div>
                  </div>

                  <div style={{ textAlign: "center", margin: "8px 0", fontSize: "11px", color: "var(--text-muted)" }}>- OR -</div>

                  {/* Manual Paste Option */}
                  <div className="form-group">
                    <label className="form-label" style={{ fontSize: "11px", color: "var(--text-muted)" }}>Paste Raw Transcript Lines</label>
                    <textarea 
                      className="form-textarea" 
                      id="transcript-paste-input"
                      rows={4}
                      placeholder="e.g.&#10;Alice: Hello everyone.&#10;Bob: Hi Alice, the backend is ready."
                      value={formTranscript}
                      onChange={(e) => setFormTranscript(e.target.value)}
                      disabled={formFile !== null}
                    />
                  </div>
                </div>

                <div className="modal-buttons">
                  <button 
                    type="button" 
                    className="btn-secondary" 
                    onClick={() => setIsModalOpen(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="btn-primary" 
                    id="submit-meeting-form"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? "Transcribing..." : "Transcribe"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
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
