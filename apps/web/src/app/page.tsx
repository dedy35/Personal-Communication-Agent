type HealthResponse = {
  status: string;
  service: string;
  environment: string;
  version: string;
};

type HealthView = {
  label: string;
  detail: string;
  toneClass: string;
};

const PLATFORM_CARDS: Array<{ name: string; colorClass: string; hint: string }> = [
  {
    name: "Slack",
    colorClass: "bg-sky-100 text-sky-700",
    hint: "Workspace threads and DMs"
  },
  {
    name: "WhatsApp",
    colorClass: "bg-emerald-100 text-emerald-700",
    hint: "Personal and group chats"
  },
  {
    name: "LINE",
    colorClass: "bg-lime-100 text-lime-700",
    hint: "Japanese daily communication"
  }
];

const INBOX_PLACEHOLDERS = [
  "[High] Message requiring reply from senior",
  "[Medium] Clarification requested in team channel",
  "[Low] FYI update, no direct action yet"
];

const AGENT_CHIPS = ["Summarize urgent items", "Draft safe reply", "Explain Japanese nuance"];

async function getApiHealthView(): Promise<HealthView> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(`${baseUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(1200)
    });

    if (!response.ok) {
      return {
        label: "API not ready",
        detail: `HTTP ${response.status}`,
        toneClass: "bg-amber-100 text-amber-700"
      };
    }

    const data = (await response.json()) as HealthResponse;

    return {
      label: "API healthy",
      detail: `${data.environment} · v${data.version}`,
      toneClass: "bg-emerald-100 text-emerald-700"
    };
  } catch {
    return {
      label: "API unreachable",
      detail: "Start FastAPI on :8000",
      toneClass: "bg-rose-100 text-rose-700"
    };
  }
}

export default async function HomePage() {
  const health = await getApiHealthView();

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 pb-6 pt-5 sm:px-6 lg:px-10">
      <header className="mb-6 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white/80 p-5 backdrop-blur sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Personal Communication Agent
            </p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">Dashboard Shell</h1>
          </div>
          <div className={`inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-medium ${health.toneClass}`}>
            {health.label}
            <span className="ml-2 text-[11px] opacity-80">{health.detail}</span>
          </div>
        </div>
        <p className="max-w-3xl text-sm text-slate-600">
          Responsive placeholder UI for desktop, tablet, and phone. Connectors are intentionally not implemented yet.
        </p>
      </header>

      <section className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {PLATFORM_CARDS.map((card) => (
          <article key={card.name} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">{card.name}</h2>
              <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${card.colorClass}`}>Pending setup</span>
            </div>
            <p className="mb-3 text-sm text-slate-600">{card.hint}</p>
            <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div className="rounded-xl bg-slate-100 px-3 py-2">Unread: -</div>
              <div className="rounded-xl bg-slate-100 px-3 py-2">Need reply: -</div>
            </div>
          </article>
        ))}
      </section>

      <section className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1.2fr]">
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Priority Inbox</h2>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">Placeholder</span>
          </div>
          <ul className="space-y-3">
            {INBOX_PLACEHOLDERS.map((item) => (
              <li key={item} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                {item}
              </li>
            ))}
          </ul>
        </article>

        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Conversation Detail</h2>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">Placeholder</span>
          </div>
          <div className="grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Original Message</p>
              <p>Waiting for selected thread.</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Translation + Intent</p>
              <p>Will appear after message analysis.</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Nuance + Hierarchy</p>
              <p>Risk and social-context insights placeholder.</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Suggested Draft</p>
              <p>Draft output will be shown here before approval.</p>
            </div>
          </div>
        </article>
      </section>

      <section className="sticky bottom-3 mt-auto rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-lg backdrop-blur sm:p-5">
        <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Agent Chat Panel</h2>
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">Placeholder</span>
        </div>

        <div className="mb-3 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
          Agent will answer commands like urgent summary, draft revision, and context explanation.
        </div>

        <div className="mb-3 flex flex-wrap gap-2">
          {AGENT_CHIPS.map((chip) => (
            <button
              key={chip}
              type="button"
              disabled
              className="rounded-full border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-500"
            >
              {chip}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            disabled
            placeholder="Type command (placeholder)"
            className="h-11 w-full rounded-xl border border-slate-300 bg-slate-100 px-3 text-sm text-slate-500 outline-none"
          />
          <button
            type="button"
            disabled
            className="h-11 rounded-xl bg-slate-300 px-4 text-sm font-semibold text-slate-600"
          >
            Send
          </button>
        </div>
      </section>
    </main>
  );
}
