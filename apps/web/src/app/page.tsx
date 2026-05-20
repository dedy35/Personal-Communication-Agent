"use client";

import { useEffect, useMemo, useState } from "react";

type StatusKey = "need_reply" | "draft_ready" | "waiting_reply" | "fyi_only" | "sensitive" | "archived";

type HealthResponse = {
  status: string;
  service: string;
  environment: string;
  version: string;
};

type PlatformStatusItem = {
  platform_account_id: number;
  platform_name: string;
  account_label: string;
  is_active: boolean;
  statuses: Record<StatusKey, number>;
  total_conversations: number;
};

type PlatformStatusesResponse = { items: PlatformStatusItem[] };

type ConversationItem = {
  id: number;
  platform_name: string;
  title: string;
  status: StatusKey;
  urgency: string | null;
  requires_reply: boolean;
  sensitive_topic_detected: boolean;
  contact_name: string | null;
  language: string | null;
  last_message_at: string | null;
  last_message_preview: string | null;
};

type ConversationsResponse = { items: ConversationItem[]; total: number };

type MessageItem = {
  id: number;
  conversation_id: number;
  direction: string;
  language: string | null;
  body_original: string;
  body_translated: string | null;
  urgency: string | null;
  requires_reply: boolean;
  tone: string | null;
  sensitive_topic_detected: boolean;
  source_message_ts: string | null;
};

type MessagesResponse = { items: MessageItem[] };

type DraftItem = {
  id: number;
  target_conversation_id: number;
  status: string;
  language: string | null;
  body_original: string;
  body_translated: string | null;
  exact_message_body: string;
  tone: string | null;
  urgency: string | null;
  requires_reply: boolean;
  sensitive_topic_detected: boolean;
};

type DraftsResponse = { items: DraftItem[]; total: number };

type DashboardCountsResponse = {
  statuses: Record<StatusKey, number>;
  total_conversations: number;
  total_messages: number;
  total_drafts: number;
  draft_ready_count: number;
  sensitive_count: number;
};

type AgentChatMessageView = {
  role: string;
  body: string;
  language: string | null;
  created_at: string;
};

type AgentChatResponse = {
  session_key: string;
  matched_intent: string;
  reply: string;
  messages: AgentChatMessageView[];
};

const STATUS_LABELS: Record<StatusKey, string> = {
  need_reply: "Need Reply",
  draft_ready: "Draft Ready",
  waiting_reply: "Waiting Reply",
  fyi_only: "FYI Only",
  sensitive: "Sensitive",
  archived: "Archived"
};

const STATUS_TONE: Record<StatusKey, string> = {
  need_reply: "bg-amber-100 text-amber-700",
  draft_ready: "bg-indigo-100 text-indigo-700",
  waiting_reply: "bg-cyan-100 text-cyan-700",
  fyi_only: "bg-slate-100 text-slate-700",
  sensitive: "bg-rose-100 text-rose-700",
  archived: "bg-zinc-100 text-zinc-700"
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    throw new Error(`${path} failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export default function HomePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [platforms, setPlatforms] = useState<PlatformStatusItem[]>([]);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [drafts, setDrafts] = useState<DraftItem[]>([]);
  const [counts, setCounts] = useState<DashboardCountsResponse | null>(null);

  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [chatSessionKey, setChatSessionKey] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<AgentChatMessageView[]>([]);
  const [chatSending, setChatSending] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadInitial() {
      setLoading(true);
      setError(null);

      try {
        const [healthData, platformData, conversationData, draftData, countsData] = await Promise.all([
          fetchJson<HealthResponse>("/health"),
          fetchJson<PlatformStatusesResponse>("/platforms/statuses"),
          fetchJson<ConversationsResponse>("/conversations"),
          fetchJson<DraftsResponse>("/drafts"),
          fetchJson<DashboardCountsResponse>("/dashboard/counts")
        ]);

        if (!active) return;

        setHealth(healthData);
        setPlatforms(platformData.items);
        setConversations(conversationData.items);
        setDrafts(draftData.items);
        setCounts(countsData);
        setSelectedConversationId(conversationData.items[0]?.id ?? null);
      } catch (loadError) {
        if (!active) return;
        setError(loadError instanceof Error ? loadError.message : "Failed to load dashboard data");
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadInitial();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedConversationId) {
      setMessages([]);
      return;
    }

    let active = true;

    async function loadMessages() {
      setMessagesLoading(true);
      setMessagesError(null);

      try {
        const data = await fetchJson<MessagesResponse>(`/conversations/${selectedConversationId}/messages`);
        if (!active) return;
        setMessages(data.items);
      } catch (loadError) {
        if (!active) return;
        setMessagesError(loadError instanceof Error ? loadError.message : "Failed to load messages");
      } finally {
        if (active) setMessagesLoading(false);
      }
    }

    void loadMessages();

    return () => {
      active = false;
    };
  }, [selectedConversationId]);

  const healthBadgeClass = health?.status === "ok" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700";

  const selectedConversation = useMemo(
    () => conversations.find((item) => item.id === selectedConversationId) ?? null,
    [conversations, selectedConversationId]
  );

  async function sendAgentMessage(text: string): Promise<void> {
    const trimmed = text.trim();
    if (!trimmed) return;

    setChatSending(true);
    setChatError(null);

    try {
      const response = await fetchJson<AgentChatResponse>("/agent/chat", {
        method: "POST",
        body: JSON.stringify({
          message: trimmed,
          session_key: chatSessionKey,
          language: "en"
        })
      });

      setChatSessionKey(response.session_key);
      setChatMessages(response.messages);
      setChatInput("");
    } catch (sendError) {
      setChatError(sendError instanceof Error ? sendError.message : "Failed to send message");
    } finally {
      setChatSending(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 pb-6 pt-5 sm:px-6 lg:px-10">
      <header className="mb-6 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white/80 p-5 backdrop-blur sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Personal Communication Agent</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">Dashboard</h1>
          </div>
          <div className={`inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-medium ${healthBadgeClass}`}>
            {health ? `API ${health.status}` : "API status unknown"}
            <span className="ml-2 text-[11px] opacity-80">
              {health ? `${health.environment} · v${health.version}` : "connect API"}
            </span>
          </div>
        </div>

        {counts && (
          <div className="grid grid-cols-2 gap-2 text-xs text-slate-700 sm:grid-cols-4 lg:grid-cols-6">
            {(Object.keys(STATUS_LABELS) as StatusKey[]).map((status) => (
              <div key={status} className="rounded-xl bg-slate-100 px-3 py-2">
                <div className="font-semibold">{STATUS_LABELS[status]}</div>
                <div>{counts.statuses[status] ?? 0}</div>
              </div>
            ))}
          </div>
        )}

        {error && <p className="rounded-lg bg-rose-100 px-3 py-2 text-sm text-rose-700">Load error: {error}</p>}
      </header>

      <section className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {loading
          ? [1, 2, 3].map((item) => (
              <article key={item} className="h-36 animate-pulse rounded-2xl border border-slate-200 bg-white" />
            ))
          : platforms.map((platform) => {
              const tone = STATUS_TONE.sensitive;
              const badgeTone = platform.is_active ? "bg-emerald-100 text-emerald-700" : "bg-zinc-100 text-zinc-700";
              return (
                <article key={platform.platform_account_id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="mb-3 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-slate-900">{platform.platform_name.toUpperCase()}</h2>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${badgeTone}`}>
                      {platform.is_active ? "Connected" : "Inactive"}
                    </span>
                  </div>
                  <p className="mb-3 text-sm text-slate-600">{platform.account_label}</p>
                  <div className="grid grid-cols-2 gap-2 text-xs text-slate-700">
                    <div className="rounded-xl bg-slate-100 px-3 py-2">Need Reply: {platform.statuses.need_reply ?? 0}</div>
                    <div className={`rounded-xl px-3 py-2 ${tone}`}>Sensitive: {platform.statuses.sensitive ?? 0}</div>
                    <div className="rounded-xl bg-slate-100 px-3 py-2">Draft Ready: {platform.statuses.draft_ready ?? 0}</div>
                    <div className="rounded-xl bg-slate-100 px-3 py-2">Total: {platform.total_conversations}</div>
                  </div>
                </article>
              );
            })}
      </section>

      <section className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1.2fr]">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Priority Inbox</h2>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
              {conversations.length} conversations
            </span>
          </div>

          {loading ? (
            <div className="h-40 animate-pulse rounded-xl bg-slate-100" />
          ) : (
            <ul className="space-y-3">
              {conversations.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedConversationId(item.id)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:bg-slate-100"
                  >
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_TONE[item.status]}`}>
                        {STATUS_LABELS[item.status]}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">
                      {item.platform_name.toUpperCase()} · {item.contact_name ?? "Unknown contact"}
                    </p>
                    <p className="mt-1 line-clamp-1 text-xs text-slate-500">{item.last_message_preview ?? "No message preview"}</p>
                  </button>
                </li>
              ))}
              {conversations.length === 0 && <li className="text-sm text-slate-500">No conversation data available.</li>}
            </ul>
          )}
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Conversation Detail</h2>
            {selectedConversation && (
              <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${STATUS_TONE[selectedConversation.status]}`}>
                {STATUS_LABELS[selectedConversation.status]}
              </span>
            )}
          </div>

          {messagesLoading ? (
            <div className="h-40 animate-pulse rounded-xl bg-slate-100" />
          ) : messagesError ? (
            <p className="rounded-lg bg-rose-100 px-3 py-2 text-sm text-rose-700">{messagesError}</p>
          ) : selectedConversation ? (
            <div className="space-y-3">
              <p className="text-sm text-slate-700">
                <span className="font-semibold">{selectedConversation.title}</span> · {selectedConversation.platform_name.toUpperCase()}
              </p>
              <div className="max-h-72 space-y-3 overflow-y-auto pr-1">
                {messages.map((message) => (
                  <div key={message.id} className="rounded-xl bg-slate-50 p-3">
                    <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                      <span>{message.direction}</span>
                      <span>{message.language ?? "-"}</span>
                    </div>
                    <p className="text-sm text-slate-800">{message.body_original}</p>
                    {message.body_translated && <p className="mt-1 text-xs text-slate-600">{message.body_translated}</p>}
                  </div>
                ))}
                {messages.length === 0 && <p className="text-sm text-slate-500">No messages yet.</p>}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Select a conversation from Priority Inbox.</p>
          )}
        </article>
      </section>

      <section className="sticky bottom-3 mt-auto rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-lg backdrop-blur sm:p-5">
        <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Agent Chat Panel</h2>
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
            Drafts Ready: {counts?.draft_ready_count ?? 0}
          </span>
        </div>

        <div className="mb-3 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
          Rule-based agent is active. Supported prompts: urgent messages today, daily narrative summary, older than 24h
          needing reply, draft-ready items, and FYI-only items.
        </div>

        <div className="mb-3 max-h-40 space-y-2 overflow-y-auto pr-1">
          {loading ? (
            <div className="h-20 animate-pulse rounded-xl bg-slate-100" />
          ) : drafts.length === 0 ? (
            <p className="text-sm text-slate-500">No drafts available.</p>
          ) : (
            drafts.map((draft) => (
              <div key={draft.id} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700">
                <div className="mb-1 flex items-center justify-between">
                  <span className="font-semibold">Draft #{draft.id}</span>
                  <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] text-indigo-700">{draft.status}</span>
                </div>
                <p className="line-clamp-2">{draft.exact_message_body}</p>
              </div>
            ))
          )}
        </div>

        <div className="mb-2 flex flex-wrap gap-2">
          {[
            "urgent messages today",
            "daily narrative summary",
            "conversations older than 24h needing reply",
            "draft-ready items",
            "FYI-only items"
          ].map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => void sendAgentMessage(prompt)}
              disabled={chatSending}
              className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 disabled:opacity-50"
            >
              {prompt}
            </button>
          ))}
        </div>

        <div className="mb-3 max-h-52 space-y-2 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50 p-3">
          {chatMessages.length === 0 ? (
            <p className="text-sm text-slate-500">Chat history will appear here.</p>
          ) : (
            chatMessages.map((message, index) => (
              <div
                key={`${message.role}-${message.created_at}-${index}`}
                className={`rounded-lg px-3 py-2 text-sm ${
                  message.role === "assistant" ? "bg-indigo-100 text-indigo-900" : "bg-white text-slate-800"
                }`}
              >
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide">{message.role}</p>
                <p className="whitespace-pre-wrap">{message.body}</p>
              </div>
            ))
          )}
        </div>

        {chatError && <p className="mb-2 rounded-lg bg-rose-100 px-3 py-2 text-sm text-rose-700">{chatError}</p>}

        <form
          className="flex items-center gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            void sendAgentMessage(chatInput);
          }}
        >
          <input
            type="text"
            value={chatInput}
            onChange={(event) => setChatInput(event.target.value)}
            disabled={chatSending}
            placeholder="Ask the agent..."
            className="h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-700 outline-none disabled:bg-slate-100"
          />
          <button
            type="submit"
            disabled={chatSending || chatInput.trim().length === 0}
            className="h-11 rounded-xl bg-slate-800 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {chatSending ? "Sending..." : "Send"}
          </button>
        </form>
      </section>
    </main>
  );
}
