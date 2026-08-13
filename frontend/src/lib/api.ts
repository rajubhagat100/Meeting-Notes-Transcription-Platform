const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface Comment {
  id: number;
  segment_id: number;
  author: string;
  text: string;
  created_at: string;
}

export interface TranscriptSegment {
  id: number;
  meeting_id: number;
  speaker: string;
  start_time: number;
  end_time: number;
  text: string;
  highlighted: boolean;
  comments: Comment[];
}

export interface Chapter {
  title: string;
  summary: string;
  start_time: number;
  end_time: number;
}

export interface Summary {
  id: number;
  meeting_id: number;
  overview: string;
  chapters: Chapter[];
  key_topics: string[];
}

export interface ActionItem {
  id: number;
  meeting_id: number;
  text: string;
  completed: boolean;
  assignee: string | null;
}

export interface ChatMessage {
  id: number;
  meeting_id: number;
  sender: "user" | "ai";
  message: string;
  created_at: string;
}

export interface MeetingBrief {
  id: number;
  title: string;
  date: string;
  duration_seconds: number;
  participants: string[];
  video_url: string | null;
  created_at: string;
}

export interface MeetingDetail extends MeetingBrief {
  transcript_segments: TranscriptSegment[];
  summary: Summary | null;
  action_items: ActionItem[];
  chat_messages: ChatMessage[];
}

export async function fetchMeetings(
  search?: string,
  participant?: string,
  topic?: string,
  sortBy: string = "recency"
): Promise<MeetingBrief[]> {
  const params = new URLSearchParams();
  if (search) params.append("search", search);
  if (participant) params.append("participant", participant);
  if (topic) params.append("topic", topic);
  params.append("sort_by", sortBy);

  const res = await fetch(`${API_BASE_URL}/api/meetings?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch meetings");
  return res.json();
}

export async function fetchMeetingDetail(id: number): Promise<MeetingDetail> {
  const res = await fetch(`${API_BASE_URL}/api/meetings/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch meeting detail for id ${id}`);
  return res.json();
}

export async function createMeeting(formData: FormData): Promise<MeetingDetail> {
  const res = await fetch(`${API_BASE_URL}/api/meetings`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to create meeting");
  return res.json();
}

export async function updateMeeting(
  id: number,
  data: { title?: string; date?: string; participants?: string[] }
): Promise<MeetingDetail> {
  const res = await fetch(`${API_BASE_URL}/api/meetings/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update meeting");
  return res.json();
}

export async function deleteMeeting(id: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/meetings/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete meeting");
}

export async function toggleSegmentHighlight(
  meetingId: number,
  segmentId: number,
  highlighted: boolean
): Promise<TranscriptSegment> {
  const res = await fetch(
    `${API_BASE_URL}/api/meetings/${meetingId}/segments/${segmentId}?highlighted=${highlighted}`,
    {
      method: "PATCH",
    }
  );
  if (!res.ok) throw new Error("Failed to toggle segment highlight");
  return res.json();
}

export async function addComment(
  meetingId: number,
  segmentId: number,
  author: string,
  text: string
): Promise<Comment> {
  const res = await fetch(
    `${API_BASE_URL}/api/meetings/${meetingId}/segments/${segmentId}/comments`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ author, text }),
    }
  );
  if (!res.ok) throw new Error("Failed to add comment");
  return res.json();
}

export async function deleteComment(commentId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/comments/${commentId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete comment");
}

export async function addActionItem(
  meetingId: number,
  text: string,
  assignee: string | null
): Promise<ActionItem> {
  const res = await fetch(`${API_BASE_URL}/api/meetings/${meetingId}/action-items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, assignee }),
  });
  if (!res.ok) throw new Error("Failed to add action item");
  return res.json();
}

export async function updateActionItem(
  actionItemId: number,
  data: { completed?: boolean; text?: string; assignee?: string | null }
): Promise<ActionItem> {
  const res = await fetch(`${API_BASE_URL}/api/action-items/${actionItemId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update action item");
  return res.json();
}

export async function deleteActionItem(actionItemId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/action-items/${actionItemId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete action item");
}

export async function askAI(meetingId: number, question: string): Promise<ChatMessage> {
  const res = await fetch(`${API_BASE_URL}/api/meetings/${meetingId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Failed to ask AI");
  return res.json();
}

export async function fetchChatHistory(meetingId: number): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE_URL}/api/meetings/${meetingId}/chat/history`);
  if (!res.ok) throw new Error("Failed to fetch chat history");
  return res.json();
}

export function getExportUrl(meetingId: number, format: "txt" | "md" | "pdf"): string {
  return `${API_BASE_URL}/api/meetings/${meetingId}/export?format=${format}`;
}
