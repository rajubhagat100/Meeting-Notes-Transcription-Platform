from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import io
import os
from datetime import datetime
from fpdf import FPDF

from .database import engine, Base, get_db
from . import models, schemas, crud, ai_service

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Notes & Transcription Platform API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

# Meetings
@app.get("/api/meetings", response_model=List[schemas.MeetingBrief])
def read_meetings(
    search: Optional[str] = None,
    participant: Optional[str] = None,
    topic: Optional[str] = None,
    sort_by: str = "recency",
    db: Session = Depends(get_db)
):
    return crud.get_meetings(db, search=search, participant=participant, topic=topic, sort_by=sort_by)

@app.get("/api/meetings/{meeting_id}", response_model=schemas.MeetingDetail)
def read_meeting(meeting_id: int, db: Session = Depends(get_db)):
    db_meeting = crud.get_meeting(db, meeting_id=meeting_id)
    if db_meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return db_meeting

@app.post("/api/meetings", response_model=schemas.MeetingDetail)
async def create_meeting(
    title: str = Form(...),
    date: str = Form(...),
    duration_seconds: int = Form(...),
    participants: str = Form("[]"),  # JSON array string
    transcript_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Parse participants JSON
    try:
        parts_list = json.loads(participants)
    except Exception:
        parts_list = [p.strip() for p in participants.split(",") if p.strip()]

    # Read transcript either from uploaded file or text field
    final_transcript = ""
    if file:
        file_bytes = await file.read()
        final_transcript = file_bytes.decode("utf-8", errors="ignore")
    elif transcript_text:
        final_transcript = transcript_text

    # Parse transcript into segments
    segments = []
    if final_transcript:
        segments = ai_service.parse_transcript(final_transcript)

    # 1. Create meeting record
    meeting_create = schemas.MeetingCreate(
        title=title,
        date=date,
        duration_seconds=duration_seconds,
        participants=parts_list,
        video_url=None
    )
    db_meeting = crud.create_meeting(db, meeting=meeting_create)

    # 2. Add transcript segments
    for seg in segments:
        seg_create = schemas.TranscriptSegmentCreate(
            speaker=seg["speaker"],
            start_time=seg["start_time"],
            end_time=seg["end_time"],
            text=seg["text"],
            highlighted=False
        )
        crud.create_transcript_segment(db, meeting_id=db_meeting.id, segment=seg_create)

    # 3. Generate AI summary, key topics, chapters, and action items
    if segments:
        ai_data = ai_service.generate_ai_summary(segments)
        
        # Save summary
        sum_create = schemas.SummaryCreate(
            overview=ai_data["overview"],
            chapters=[schemas.ChapterSchema(**c) for c in ai_data["chapters"]],
            key_topics=ai_data["key_topics"]
        )
        crud.create_summary(db, meeting_id=db_meeting.id, summary=sum_create)
        
        # Save action items
        for action in ai_data["action_items"]:
            action_create = schemas.ActionItemCreate(
                text=action["text"],
                completed=False,
                assignee=action.get("assignee")
            )
            crud.create_action_item(db, meeting_id=db_meeting.id, action_item=action_create)
    else:
        # Save empty summary & action items if no transcript
        sum_create = schemas.SummaryCreate(
            overview="No transcript provided for this meeting. AI Summary could not be generated.",
            chapters=[],
            key_topics=[]
        )
        crud.create_summary(db, meeting_id=db_meeting.id, summary=sum_create)

    db.refresh(db_meeting)
    return db_meeting

@app.put("/api/meetings/{meeting_id}", response_model=schemas.MeetingDetail)
def update_meeting(meeting_id: int, meeting_update: schemas.MeetingUpdate, db: Session = Depends(get_db)):
    db_meeting = crud.update_meeting(db, meeting_id=meeting_id, meeting_update=meeting_update)
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return db_meeting

@app.delete("/api/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    success = crud.delete_meeting(db, meeting_id=meeting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Transcript Segment Highlight
@app.patch("/api/meetings/{meeting_id}/segments/{segment_id}", response_model=schemas.TranscriptSegment)
def toggle_highlight(meeting_id: int, segment_id: int, highlighted: bool, db: Session = Depends(get_db)):
    db_segment = crud.update_transcript_segment(db, segment_id=segment_id, highlighted=highlighted)
    if not db_segment:
        raise HTTPException(status_code=404, detail="Transcript segment not found")
    return db_segment


# Comments
@app.post("/api/meetings/{meeting_id}/segments/{segment_id}/comments", response_model=schemas.Comment)
def add_comment(meeting_id: int, segment_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    return crud.create_comment(db, segment_id=segment_id, comment=comment)

@app.delete("/api/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    success = crud.delete_comment(db, comment_id=comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Action Items
@app.post("/api/meetings/{meeting_id}/action-items", response_model=schemas.ActionItem)
def add_action_item(meeting_id: int, action_item: schemas.ActionItemCreate, db: Session = Depends(get_db)):
    return crud.create_action_item(db, meeting_id=meeting_id, action_item=action_item)

@app.patch("/api/action-items/{action_item_id}", response_model=schemas.ActionItem)
def update_action_item(
    action_item_id: int, 
    completed: Optional[bool] = None, 
    text: Optional[str] = None, 
    assignee: Optional[str] = None,
    db: Session = Depends(get_db)
):
    item = crud.update_action_item(db, action_item_id=action_item_id, completed=completed, text=text, assignee=assignee)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item

@app.delete("/api/action-items/{action_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action_item(action_item_id: int, db: Session = Depends(get_db)):
    success = crud.delete_action_item(db, action_item_id=action_item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Action item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Chat Q&A
@app.post("/api/meetings/{meeting_id}/chat", response_model=schemas.ChatMessage)
def ask_question(meeting_id: int, req: schemas.ChatRequest, db: Session = Depends(get_db)):
    db_meeting = crud.get_meeting(db, meeting_id=meeting_id)
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # 1. Save user query
    user_msg = schemas.ChatMessageCreate(sender="user", message=req.question)
    crud.create_chat_message(db, meeting_id=meeting_id, message=user_msg)
    
    # 2. Generate answer
    segments_list = [
        {"speaker": seg.speaker, "start_time": seg.start_time, "end_time": seg.end_time, "text": seg.text}
        for seg in db_meeting.transcript_segments
    ]
    overview = db_meeting.summary.overview if db_meeting.summary else "Meeting Notes"
    
    answer_text = ai_service.ask_ai_about_meeting(req.question, segments_list, overview)
    
    # 3. Save AI response
    ai_msg = schemas.ChatMessageCreate(sender="ai", message=answer_text)
    db_ai_message = crud.create_chat_message(db, meeting_id=meeting_id, message=ai_msg)
    
    return db_ai_message

@app.get("/api/meetings/{meeting_id}/chat/history", response_model=List[schemas.ChatMessage])
def get_chat_history(meeting_id: int, db: Session = Depends(get_db)):
    return crud.get_chat_history(db, meeting_id=meeting_id)


# Export API
@app.get("/api/meetings/{meeting_id}/export")
def export_meeting(meeting_id: int, format: str = "md", db: Session = Depends(get_db)):
    db_meeting = crud.get_meeting(db, meeting_id=meeting_id)
    if not db_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    participants_list = json.loads(db_meeting.participants) if db_meeting.participants else []
    participants_str = ", ".join(participants_list)

    if format == "txt":
        content = f"MEETING: {db_meeting.title}\n"
        content += f"DATE: {db_meeting.date}\n"
        content += f"PARTICIPANTS: {participants_str}\n"
        content += "=" * 40 + "\n\n"
        
        if db_meeting.summary:
            content += "AI SUMMARY OVERVIEW:\n"
            content += db_meeting.summary.overview + "\n\n"
            
        content += "TRANSCRIPT:\n"
        for seg in db_meeting.transcript_segments:
            mins = int(seg.start_time // 60)
            secs = int(seg.start_time % 60)
            content += f"[{mins:02d}:{secs:02d}] {seg.speaker}: {seg.text}\n"
            
        response = Response(content=content, media_type="text/plain")
        response.headers["Content-Disposition"] = f"attachment; filename=meeting_{meeting_id}_export.txt"
        return response

    elif format == "md":
        content = f"# {db_meeting.title}\n\n"
        content += f"- **Date**: {db_meeting.date}\n"
        content += f"- **Participants**: {participants_str}\n\n"
        
        if db_meeting.summary:
            content += "## AI Overview\n"
            content += f"{db_meeting.summary.overview}\n\n"
            
            # Key topics
            topics = json.loads(db_meeting.summary.key_topics) if db_meeting.summary.key_topics else []
            if topics:
                content += "## Key Topics\n"
                content += ", ".join([f"`{t}`" for t in topics]) + "\n\n"

            # Chapters
            chapters = json.loads(db_meeting.summary.chapters) if db_meeting.summary.chapters else []
            if chapters:
                content += "## Chapters / Outline\n"
                for ch in chapters:
                    start_mins = int(ch['start_time'] // 60)
                    start_secs = int(ch['start_time'] % 60)
                    content += f"- **[{start_mins:02d}:{start_secs:02d}] {ch['title']}**: {ch['summary']}\n"
                content += "\n"

        if db_meeting.action_items:
            content += "## Action Items\n"
            for item in db_meeting.action_items:
                status_box = "[x]" if item.completed else "[ ]"
                assignee_str = f" (Assignee: {item.assignee})" if item.assignee else ""
                content += f"- {status_box} {item.text}{assignee_str}\n"
            content += "\n"

        content += "## Transcript\n"
        for seg in db_meeting.transcript_segments:
            mins = int(seg.start_time // 60)
            secs = int(seg.start_time % 60)
            highlight_prefix = "⭐ " if seg.highlighted else ""
            content += f"**[{mins:02d}:{secs:02d}] {seg.speaker}**: {highlight_prefix}{seg.text}\n\n"
            
        response = Response(content=content, media_type="text/markdown")
        response.headers["Content-Disposition"] = f"attachment; filename=meeting_{meeting_id}_export.md"
        return response

    elif format == "pdf":
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Use core Helvetica fonts
            pdf.set_font("Helvetica", size=16, style='B')
            pdf.cell(200, 10, txt=db_meeting.title, ln=True, align='L')
            
            pdf.set_font("Helvetica", size=10, style='I')
            pdf.cell(200, 8, txt=f"Date: {db_meeting.date}  |  Participants: {participants_str}", ln=True, align='L')
            pdf.ln(5)
            
            if db_meeting.summary:
                pdf.set_font("Helvetica", size=12, style='B')
                pdf.cell(200, 8, txt="AI Overview", ln=True, align='L')
                pdf.set_font("Helvetica", size=10)
                pdf.multi_cell(0, 5, txt=db_meeting.summary.overview)
                pdf.ln(5)
            
            if db_meeting.action_items:
                pdf.set_font("Helvetica", size=12, style='B')
                pdf.cell(200, 8, txt="Action Items", ln=True, align='L')
                pdf.set_font("Helvetica", size=10)
                for item in db_meeting.action_items:
                    status = "[Done]" if item.completed else "[ ]"
                    assignee_str = f" ({item.assignee})" if item.assignee else ""
                    pdf.cell(0, 5, txt=f"{status} {item.text}{assignee_str}", ln=True)
                pdf.ln(5)

            pdf.set_font("Helvetica", size=12, style='B')
            pdf.cell(200, 8, txt="Transcript", ln=True, align='L')
            pdf.set_font("Helvetica", size=10)
            
            for seg in db_meeting.transcript_segments:
                mins = int(seg.start_time // 60)
                secs = int(seg.start_time % 60)
                seg_text = f"[{mins:02d}:{secs:02d}] {seg.speaker}: {seg.text}"
                
                # Check for page break space
                if pdf.get_y() > 270:
                    pdf.add_page()
                pdf.multi_cell(0, 5, txt=seg_text)
                pdf.ln(2)

            pdf_output = pdf.output()
            # In fpdf2, output() without a path returns bytes (if we pass dest='S') or we can just access output.
            # In fpdf2, output() returns bytes directly if we don't supply a filepath. Let's make sure.
            if isinstance(pdf_output, bytearray):
                pdf_bytes = bytes(pdf_output)
            elif isinstance(pdf_output, str):
                pdf_bytes = pdf_output.encode('latin1')
            else:
                pdf_bytes = pdf_output
                
            return Response(content=pdf_bytes, media_type="application/pdf", headers={
                "Content-Disposition": f"attachment; filename=meeting_{meeting_id}_export.pdf"
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail="Invalid format. Supported: txt, md, pdf")
