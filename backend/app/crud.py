from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from . import models, schemas
import json
from datetime import datetime

# Meeting CRUD
def get_meetings(
    db: Session,
    search: str = None,
    participant: str = None,
    topic: str = None,
    sort_by: str = "recency",  # "recency" | "duration" | "title"
):
    query = db.query(models.Meeting)
    
    # Apply search filter (title or participant)
    if search:
        query = query.filter(
            or_(
                models.Meeting.title.like(f"%{search}%"),
                models.Meeting.participants.like(f"%{search}%")
            )
        )
        
    if participant:
        query = query.filter(models.Meeting.participants.like(f"%{participant}%"))

    # Apply topic filter (requires joining the Summary table)
    if topic:
        query = query.join(models.Summary).filter(models.Summary.key_topics.like(f"%{topic}%"))

    # Apply sorting
    if sort_by == "recency":
        query = query.order_by(desc(models.Meeting.date))
    elif sort_by == "duration":
        query = query.order_by(desc(models.Meeting.duration_seconds))
    elif sort_by == "title":
        query = query.order_by(asc(models.Meeting.title))
    else:
        query = query.order_by(desc(models.Meeting.date))
        
    return query.all()

def get_meeting(db: Session, meeting_id: int):
    return db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()

def create_meeting(db: Session, meeting: schemas.MeetingCreate):
    db_meeting = models.Meeting(
        title=meeting.title,
        date=meeting.date,
        duration_seconds=meeting.duration_seconds,
        participants=json.dumps(meeting.participants),
        video_url=meeting.video_url,
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def update_meeting(db: Session, meeting_id: int, meeting_update: schemas.MeetingUpdate):
    db_meeting = get_meeting(db, meeting_id)
    if not db_meeting:
        return None
    
    update_data = meeting_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "participants":
            setattr(db_meeting, key, json.dumps(value))
        else:
            setattr(db_meeting, key, value)
            
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

def delete_meeting(db: Session, meeting_id: int):
    db_meeting = get_meeting(db, meeting_id)
    if not db_meeting:
        return False
    db.delete(db_meeting)
    db.commit()
    return True


# Transcript Segment CRUD
def create_transcript_segment(db: Session, meeting_id: int, segment: schemas.TranscriptSegmentCreate):
    db_segment = models.TranscriptSegment(
        meeting_id=meeting_id,
        speaker=segment.speaker,
        start_time=segment.start_time,
        end_time=segment.end_time,
        text=segment.text,
        highlighted=segment.highlighted
    )
    db.add(db_segment)
    db.commit()
    db.refresh(db_segment)
    return db_segment

def get_transcript_segment(db: Session, segment_id: int):
    return db.query(models.TranscriptSegment).filter(models.TranscriptSegment.id == segment_id).first()

def update_transcript_segment(db: Session, segment_id: int, highlighted: bool):
    db_segment = get_transcript_segment(db, segment_id)
    if not db_segment:
        return None
    db_segment.highlighted = highlighted
    db.commit()
    db.refresh(db_segment)
    return db_segment


# Comment CRUD
def create_comment(db: Session, segment_id: int, comment: schemas.CommentCreate):
    db_comment = models.Comment(
        segment_id=segment_id,
        author=comment.author,
        text=comment.text,
        created_at=datetime.utcnow()
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def delete_comment(db: Session, comment_id: int):
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not db_comment:
        return False
    db.delete(db_comment)
    db.commit()
    return True


# Summary CRUD
def create_summary(db: Session, meeting_id: int, summary: schemas.SummaryCreate):
    db_summary = models.Summary(
        meeting_id=meeting_id,
        overview=summary.overview,
        chapters=json.dumps([c.model_dump() for c in summary.chapters]),
        key_topics=json.dumps(summary.key_topics)
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary


# Action Item CRUD
def create_action_item(db: Session, meeting_id: int, action_item: schemas.ActionItemCreate):
    db_action_item = models.ActionItem(
        meeting_id=meeting_id,
        text=action_item.text,
        completed=action_item.completed,
        assignee=action_item.assignee
    )
    db.add(db_action_item)
    db.commit()
    db.refresh(db_action_item)
    return db_action_item

def update_action_item(db: Session, action_item_id: int, completed: bool = None, text: str = None, assignee: str = None):
    db_item = db.query(models.ActionItem).filter(models.ActionItem.id == action_item_id).first()
    if not db_item:
        return None
    if completed is not None:
        db_item.completed = completed
    if text is not None:
        db_item.text = text
    if assignee is not None:
        db_item.assignee = assignee
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_action_item(db: Session, action_item_id: int):
    db_item = db.query(models.ActionItem).filter(models.ActionItem.id == action_item_id).first()
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True


# Chat Message CRUD
def create_chat_message(db: Session, meeting_id: int, message: schemas.ChatMessageCreate):
    db_message = models.ChatMessage(
        meeting_id=meeting_id,
        sender=message.sender,
        message=message.message,
        created_at=datetime.utcnow()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_history(db: Session, meeting_id: int):
    return db.query(models.ChatMessage).filter(models.ChatMessage.meeting_id == meeting_id).order_by(models.ChatMessage.created_at.asc()).all()
