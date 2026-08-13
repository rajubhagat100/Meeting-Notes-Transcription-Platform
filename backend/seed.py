import json
from datetime import datetime, timedelta
from app.database import engine, SessionLocal, Base
from app import models

# Recreate database tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Meeting 1: Q3 Product Strategy Sync
m1 = models.Meeting(
    title="Q3 Product Strategy Sync",
    date="2026-08-10",
    duration_seconds=1200,
    participants=json.dumps(["Alice", "Bob", "Carol"]),
    video_url="https://www.w3schools.com/html/mov_bbb.mp4",  # Sample video placeholder
)
db.add(m1)
db.commit()
db.refresh(m1)

# Seed Transcript for Meeting 1
t1_segs = [
    ("Alice", 0.0, 10.0, "Hello everyone! Welcome to our Q3 Strategy Sync. Today we are looking at our transcription tool roadmap."),
    ("Bob", 10.0, 25.0, "Hi Alice, yes. I've prepared the architectural draft. We will use Next.js on the frontend, FastAPI for the API layer, and SQLite to persist transcripts."),
    ("Carol", 25.0, 42.0, "Nice! For the interface, I am designing a custom dark theme resembling Fireflies. We need high-contrast accents, a glassmorphic sidebar, and interactive components."),
    ("Alice", 42.0, 58.0, "That sounds amazing. The core feature is transcript seeking: users must click a sentence to seek the media player, and vice versa. Bob, is that feasible?"),
    ("Bob", 58.0, 75.0, "Absolutely. We'll synchronize the HTML5 audio/video element's currentTime property with the start and end timestamps of each transcript segment."),
    ("Carol", 75.0, 92.0, "Perfect. I'll also add a commenting system. Users can hover over any transcript sentence, click a comment bubble, and discuss specific segments."),
    ("Alice", 92.0, 110.0, "Excellent. Let's make sure we generate action items. Bob, can you work on setting up database models? Carol, finish the detail page design. I'll seed transcription data."),
    ("Bob", 110.0, 120.0, "Understood. I will start on the models today and have them ready by tomorrow."),
]

for speaker, start, end, text in t1_segs:
    seg = models.TranscriptSegment(
        meeting_id=m1.id,
        speaker=speaker,
        start_time=start,
        end_time=end,
        text=text,
        highlighted=(start == 42.0)  # highlight Alice's core requirement
    )
    db.add(seg)
db.commit()

# Seed Comments for Meeting 1
# Get Alice's segment
alice_seg = db.query(models.TranscriptSegment).filter(models.TranscriptSegment.meeting_id == m1.id, models.TranscriptSegment.start_time == 42.0).first()
if alice_seg:
    c1 = models.Comment(
        segment_id=alice_seg.id,
        author="Bob",
        text="I have researched the HTML Media Element API and this is 100% possible to sync in real-time.",
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    db.add(c1)
db.commit()

# Seed Summary for Meeting 1
s1 = models.Summary(
    meeting_id=m1.id,
    overview="Kickoff sync to outline the product roadmap, technical architecture, and visual aesthetics of the upcoming Meeting Notes & Transcription Platform (Fireflies.ai clone).",
    key_topics=json.dumps(["Product Strategy", "Next.js Architecture", "UI Design System", "Audio Sync API"]),
    chapters=json.dumps([
        {"title": "Introduction & Welcome", "summary": "Alice welcomes the team and outlines the Q3 strategy goals.", "start_time": 0.0, "end_time": 10.0},
        {"title": "Tech Stack Definition", "summary": "Bob reviews the selected backend (FastAPI) and database structure (SQLite).", "start_time": 10.0, "end_time": 25.0},
        {"title": "UI Aesthetics Design", "summary": "Carol highlights plans for a dark-mode, modern glassmorphic interface.", "start_time": 25.0, "end_time": 42.0},
        {"title": "Interactive Player Syncing", "summary": "Discussion on seeking synchronization and comment features.", "start_time": 42.0, "end_time": 92.0},
        {"title": "Action Items & Wrap-up", "summary": "Distribution of responsibilities across the team.", "start_time": 92.0, "end_time": 120.0}
    ])
)
db.add(s1)

# Seed Action Items for Meeting 1
ai1_1 = models.ActionItem(meeting_id=m1.id, text="Setup FastAPI backend project and define SQLAlchemy database models.", completed=False, assignee="Bob")
ai1_2 = models.ActionItem(meeting_id=m1.id, text="Create glassmorphic Dark/Light mode theme system using Vanilla CSS.", completed=True, assignee="Carol")
ai1_3 = models.ActionItem(meeting_id=m1.id, text="Generate high-fidelity seed transcript files.", completed=False, assignee="Alice")
db.add(ai1_1)
db.add(ai1_2)
db.add(ai1_3)
db.commit()


# Meeting 2: Backend DB Schema Review & API Specs
m2 = models.Meeting(
    title="Backend DB Schema Review & API Specs",
    date="2026-08-11",
    duration_seconds=600,
    participants=json.dumps(["Bob", "David"]),
    video_url=None,
)
db.add(m2)
db.commit()
db.refresh(m2)

t2_segs = [
    ("Bob", 0.0, 15.0, "Hey David, thanks for hopping on. I want to review the relational layout of our tables before we finalize CRUD routes."),
    ("David", 15.0, 30.0, "Happy to help. Let's look at the CASCADE settings first. If a meeting gets deleted, we want all transcripts, summaries, and action items wiped automatically."),
    ("Bob", 30.0, 48.0, "Good point. I've set ondelete='CASCADE' on the ForeignKey definitions and cascade='all, delete-orphan' in SQLAlchemy relationships."),
    ("David", 48.0, 62.0, "Excellent. What about the participants? Creating a separate junction table might be overkill. Comma-separated or JSON list is simpler for SQLite."),
    ("Bob", 62.0, 80.0, "Yes, we'll store participants as a JSON string in SQLite and parse them using Pydantic's validators on the API layer."),
    ("David", 80.0, 95.0, "Perfect. Looks very clean. Let's make sure we expose a simple search endpoint that filters by keyword or participant name."),
]

for speaker, start, end, text in t2_segs:
    seg = models.TranscriptSegment(
        meeting_id=m2.id,
        speaker=speaker,
        start_time=start,
        end_time=end,
        text=text,
        highlighted=False
    )
    db.add(seg)
db.commit()

s2 = models.Summary(
    meeting_id=m2.id,
    overview="Engineering review focusing on SQLite database schema optimization, cascading delete policies, and JSON string serialization strategies for simple fields.",
    key_topics=json.dumps(["Database Schema", "SQLite Configuration", "SQLAlchemy Cascade", "JSON Serialization"]),
    chapters=json.dumps([
        {"title": "Introduction", "summary": "Review agenda for relational schema layout.", "start_time": 0.0, "end_time": 15.0},
        {"title": "Cascading Deletes", "summary": "Agreement to use cascade deleting on meeting deletion.", "start_time": 15.0, "end_time": 48.0},
        {"title": "Participant Data Structure", "summary": "Deciding on JSON string serialization in SQLite rather than junction tables.", "start_time": 48.0, "end_time": 95.0}
    ])
)
db.add(s2)

ai2_1 = models.ActionItem(meeting_id=m2.id, text="Implement cascading delete on foreign keys in database models.", completed=True, assignee="Bob")
ai2_2 = models.ActionItem(meeting_id=m2.id, text="Write utility functions to serialize/deserialize list fields.", completed=True, assignee="David")
db.add(ai2_1)
db.add(ai2_2)
db.commit()


# Meeting 3: Dashboard UI Review & Seeking Sync
m3 = models.Meeting(
    title="Dashboard UI Review & Seeking Sync",
    date="2026-08-12",
    duration_seconds=900,
    participants=json.dumps(["Alice", "Carol", "Bob"]),
    video_url=None,
)
db.add(m3)
db.commit()
db.refresh(m3)

t3_segs = [
    ("Carol", 0.0, 12.0, "Okay, here is the new dashboard mockup. Notice the left sidebar with global navigation, and the main grid showing meeting cards."),
    ("Alice", 12.0, 24.0, "I like it, Carol. It looks super clean. The tags showing the key topics at a glance on each card is a great touch."),
    ("Bob", 24.0, 42.0, "Agreed. In terms of implementation, we can fetch all meetings with a single lightweight API endpoint, and get detailed views on click."),
    ("Carol", 42.0, 58.0, "For the detail view, I've split the screen. Left side is player and transcript, right side is AI summaries, action items, and Q&A chat."),
    ("Alice", 58.0, 75.0, "This layout is perfect. It keeps all context visible. Let's make sure the transcript search highlights the matches in real-time."),
    ("Bob", 75.0, 90.0, "Yes, we can do client-side transcript filtering and wrap matching words in a styled span tag to highlight them."),
]

for speaker, start, end, text in t3_segs:
    seg = models.TranscriptSegment(
        meeting_id=m3.id,
        speaker=speaker,
        start_time=start,
        end_time=end,
        text=text,
        highlighted=False
    )
    db.add(seg)
db.commit()

s3 = models.Summary(
    meeting_id=m3.id,
    overview="Frontend alignment session reviewing dashboard card design, search and tag filtering, split-pane layout for detail view, and text highlighting implementation.",
    key_topics=json.dumps(["Frontend Dashboard", "Split-pane Layout", "Text Highlighting", "Next.js Routing"]),
    chapters=json.dumps([
        {"title": "Dashboard Design", "summary": "Carol shows mockups of sidebar and cards.", "start_time": 0.0, "end_time": 24.0},
        {"title": "Detail View Split-Screen", "summary": "Carol presents the split-pane layout.", "start_time": 24.0, "end_time": 58.0},
        {"title": "Interactive Search Highlighting", "summary": "Discussion on regex-based string highlighting on the client side.", "start_time": 58.0, "end_time": 90.0}
    ])
)
db.add(s3)

ai3_1 = models.ActionItem(meeting_id=m3.id, text="Write hook to bind audio playback timeline with active transcript line.", completed=False, assignee="Bob")
ai3_2 = models.ActionItem(meeting_id=m3.id, text="Implement word match highlighting inside transcript viewer.", completed=False, assignee="Carol")
ai3_3 = models.ActionItem(meeting_id=m3.id, text="Design 'Ask AI' chat layout.", completed=True, assignee="Carol")
db.add(ai3_1)
db.add(ai3_2)
db.add(ai3_3)
db.commit()

db.close()
print("Database seeded successfully with 3 rich meetings!")
