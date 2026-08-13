import os
import json
import re
import requests
from typing import List, Dict, Any, Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def parse_transcript(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parses a raw transcript string into structured segments.
    Supports:
    - WebVTT format (.vtt)
    - Timestamp prefixes e.g. [00:12:30] Speaker Name: Text or 00:12:30 Speaker Name: Text
    - Speaker line format e.g. Speaker Name: Text
    """
    segments = []
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    
    # 1. Check if it's WebVTT
    if lines and "WEBVTT" in lines[0]:
        # Simple VTT parser
        current_time = None
        current_speaker = "Unknown"
        text_lines = []
        
        time_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})")
        
        for line in lines[1:]:
            match = time_pattern.search(line)
            if match:
                # If we have accumulated text for a previous segment, save it
                if current_time and text_lines:
                    full_text = " ".join(text_lines)
                    speaker, clean_text = extract_speaker(full_text)
                    segments.append({
                        "speaker": speaker,
                        "start_time": current_time[0],
                        "end_time": current_time[1],
                        "text": clean_text,
                        "highlighted": False
                    })
                    text_lines = []
                
                # Parse timestamps to seconds
                start_str, end_str = match.groups()
                current_time = (time_to_seconds(start_str), time_to_seconds(end_str))
            else:
                if not line.startswith("NOTE") and not line.isdigit():
                    text_lines.append(line)
        
        # Add last segment
        if current_time and text_lines:
            full_text = " ".join(text_lines)
            speaker, clean_text = extract_speaker(full_text)
            segments.append({
                "speaker": speaker,
                "start_time": current_time[0],
                "end_time": current_time[1],
                "text": clean_text,
                "highlighted": False
            })
            
        if segments:
            return segments

    # 2. Match standard line patterns: [00:00] Speaker: Text or Speaker: Text
    current_time_offset = 0.0
    for line in lines:
        # Check for timestamp pattern like [01:23] or [01:23:45] or 01:23:45
        time_match = re.match(r"\[?(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d{3})?)\]?\s*(.*)", line)
        if time_match:
            time_str, content = time_match.groups()
            seconds = time_to_seconds(time_str)
            speaker, text = extract_speaker(content)
            segments.append({
                "speaker": speaker,
                "start_time": seconds,
                "end_time": seconds + 10.0,  # assume 10s duration
                "text": text,
                "highlighted": False
            })
        else:
            # No timestamp, just Speaker: Text
            speaker, text = extract_speaker(line)
            segments.append({
                "speaker": speaker,
                "start_time": current_time_offset,
                "end_time": current_time_offset + 10.0,
                "text": text,
                "highlighted": False
            })
            current_time_offset += 10.0

    # Adjust end_times to be start_time of next segment to avoid overlap/gaps
    for i in range(len(segments) - 1):
        segments[i]["end_time"] = segments[i + 1]["start_time"]
    
    return segments

def extract_speaker(text: str) -> tuple:
    """Helper to extract speaker name from text like 'Bob: hello' or '<v Bob> hello'"""
    # Remove WebVTT voice tag <v Speaker>Text</v>
    text = re.sub(r"<v\s+([^>]+)>", r"\1: ", text)
    text = re.sub(r"</v>", "", text)
    
    match = re.match(r"^([^:]+):\s*(.*)", text)
    if match:
        speaker, content = match.groups()
        return speaker.strip(), content.strip()
    return "Speaker", text.strip()

def time_to_seconds(time_str: str) -> float:
    """Converts HH:MM:SS.mmm or MM:SS.mmm to seconds (float)"""
    time_str = time_str.replace("[", "").replace("]", "").strip()
    parts = time_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        s_parts = s.split(".")
        seconds = float(s_parts[0])
        millis = float(s_parts[1]) / 1000.0 if len(s_parts) > 1 else 0.0
        return int(h) * 3600 + int(m) * 60 + seconds + millis
    elif len(parts) == 2:
        m, s = parts
        s_parts = s.split(".")
        seconds = float(s_parts[0])
        millis = float(s_parts[1]) / 1000.0 if len(s_parts) > 1 else 0.0
        return int(m) * 60 + seconds + millis
    else:
        try:
            return float(time_str)
        except ValueError:
            return 0.0

def generate_ai_summary(transcript_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates summary, outline/chapters, action items, and tags from a transcript.
    Uses Gemini if key is available, else does smart rule-based extraction.
    """
    transcript_text = "\n".join([f"{seg['speaker']}: {seg['text']}" for seg in transcript_segments])
    
    if GEMINI_API_KEY:
        try:
            prompt = f"""
            You are an AI meeting assistant. Analyze the following meeting transcript.
            Generate a detailed summary, outline chapters, key topics, and action items.
            Provide your response ONLY as a JSON object matching this schema:
            {{
                "overview": "Detailed overview summary of the meeting",
                "key_topics": ["topic1", "topic2", ...],
                "chapters": [
                    {{
                        "title": "Chapter Title",
                        "summary": "Summary of this chapter",
                        "start_time": 0.0,
                        "end_time": 120.0
                    }}
                ],
                "action_items": [
                    {{
                        "text": "Specific task to complete",
                        "assignee": "Name of person assigned, or null if unassigned"
                    }}
                ]
            }}
            
            Meeting Transcript:
            {transcript_text}
            """
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                res_data = response.json()
                text_response = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_response)
        except Exception as e:
            print(f"Error calling Gemini: {e}. Falling back to mock generator.")

    # Fallback Smart Mock Generator
    # Overview
    total_segments = len(transcript_segments)
    speakers = list(set([seg["speaker"] for seg in transcript_segments]))
    speakers_str = ", ".join(speakers)
    
    overview = f"In this meeting, {speakers_str} discussed project updates, milestones, and upcoming tasks. "
    if total_segments > 0:
        first_few = " ".join([seg["text"] for seg in transcript_segments[:min(3, total_segments)]])
        overview += f"The discussion began with: '{first_few[:120]}...'"
    else:
        overview += "The meeting notes are empty or transcript was brief."
        
    # Heuristics for Action Items
    action_items = []
    action_keywords = ["need to", "action item", "todo", "should", "will do", "assign", "must", "task"]
    
    for seg in transcript_segments:
        text_lower = seg["text"].lower()
        if any(kw in text_lower for kw in action_keywords):
            # Attempt to find if speaker refers to themselves or someone else
            assignee = None
            for sp in speakers:
                if sp.lower() in text_lower:
                    assignee = sp
                    break
            if not assignee:
                assignee = seg["speaker"]
            
            action_items.append({
                "text": seg["text"],
                "assignee": assignee
            })
            
    # Add a fallback action item if none detected
    if not action_items and speakers:
        action_items.append({
            "text": "Review notes and follow up on next steps.",
            "assignee": speakers[0]
        })
        
    # Heuristics for Key Topics
    common_topics = ["Product Design", "Architecture", "Sprint Planning", "Database Schema", "UI/UX Review", "LLM Integration", "Next.js Frontend", "FastAPI Backend"]
    key_topics = []
    for topic in common_topics:
        if any(topic.lower() in seg["text"].lower() for seg in transcript_segments):
            key_topics.append(topic)
    if not key_topics:
        key_topics = ["General Alignment", "Sync", "Project Management"]
        
    # Chapters
    chapters = []
    duration = transcript_segments[-1]["end_time"] if transcript_segments else 0.0
    if duration > 0:
        chunk_size = max(1, len(transcript_segments) // 3)
        for i in range(0, len(transcript_segments), chunk_size):
            sub_segs = transcript_segments[i : i + chunk_size]
            if not sub_segs:
                continue
            start = sub_segs[0]["start_time"]
            end = sub_segs[-1]["end_time"]
            topics_in_chunk = [topic for topic in key_topics if any(topic.lower() in s["text"].lower() for s in sub_segs)]
            topic_str = topics_in_chunk[0] if topics_in_chunk else "General Discussion"
            
            chapters.append({
                "title": f"Discussion on {topic_str}",
                "summary": f"Discussion led by {sub_segs[0]['speaker']} covering: '{sub_segs[0]['text'][:80]}...'",
                "start_time": start,
                "end_time": end
            })
    else:
        chapters.append({
            "title": "Introduction & Sync",
            "summary": "Initial greeting and overview.",
            "start_time": 0.0,
            "end_time": 10.0
        })

    return {
        "overview": overview,
        "key_topics": key_topics[:5],
        "chapters": chapters,
        "action_items": action_items[:6]
    }

def ask_ai_about_meeting(question: str, transcript_segments: List[Dict[str, Any]], summary_overview: str) -> str:
    """
    Answers a question about the meeting using context from the transcript.
    Uses Gemini if key is available, else uses keyword-based extraction.
    """
    transcript_text = "\n".join([f"{seg['speaker']}: {seg['text']}" for seg in transcript_segments])
    
    if GEMINI_API_KEY:
        try:
            prompt = f"""
            You are a helpful AI meeting assistant. Answer the user's question about the following meeting.
            Use the provided transcript and summary overview to construct a clear, helpful response.
            If the answer cannot be found in the transcript, state that clearly.
            
            Summary Overview:
            {summary_overview}
            
            Meeting Transcript:
            {transcript_text}
            
            Question:
            {question}
            
            Answer:
            """
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                res_data = response.json()
                return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"Error calling Gemini in Chat: {e}. Falling back to rule-based chat.")

    # Rule-based fallback Q&A
    question_lower = question.lower()
    
    # 1. Action items / Todo question
    if any(w in question_lower for w in ["action item", "todo", "task", "assigned"]):
        action_keywords = ["need to", "action item", "todo", "should", "will do", "assign", "must", "task"]
        matching_lines = []
        for seg in transcript_segments:
            if any(kw in seg["text"].lower() for kw in action_keywords):
                matching_lines.append(f"- **{seg['speaker']}**: \"{seg['text']}\"")
        if matching_lines:
            return "Based on the transcript, here are the key action items and tasks mentioned:\n\n" + "\n".join(matching_lines[:5])
        return "I couldn't find any explicit tasks or action items mentioned in the transcript."
        
    # 2. Participants / Who attended question
    if any(w in question_lower for w in ["who", "participant", "attend", "present", "people"]):
        speakers = list(set([seg["speaker"] for seg in transcript_segments]))
        if speakers:
            return f"The meeting participants identified from the transcript are: {', '.join(speakers)}."
        return "I could not identify any participants from the transcript segments."

    # 3. Topic search / Keyword match
    matches = []
    for seg in transcript_segments:
        # Check if question keywords match the segment text
        words = [w for w in question_lower.split() if len(w) > 4]
        if any(word in seg["text"].lower() for word in words):
            matches.append(f"At {time_to_minutes(seg['start_time'])}, **{seg['speaker']}** said: \"{seg['text']}\"")
            
    if matches:
        return "Here is what I found in the conversation related to your question:\n\n" + "\n\n".join(matches[:3])
        
    return f"I searched the transcript but could not find a specific answer to: '{question}'. However, this meeting was about: '{summary_overview[:150]}...' featuring discussions between {', '.join(list(set([seg['speaker'] for seg in transcript_segments]))[:3])}."

def time_to_minutes(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"
