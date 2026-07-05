import React from "react";

// Lightweight markdown renderer (no external deps)
export function Markdown({ text }) {
  if (!text) return null;
  const lines = text.split("\n");
  const blocks = [];
  let list = null;
  let listType = null;

  const inline = (s) =>
    s
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, "<code>$1</code>");

  const flush = () => {
    if (list) {
      blocks.push({ type: listType, items: list });
      list = null;
      listType = null;
    }
  };

  lines.forEach((raw) => {
    const line = raw.trimEnd();
    if (/^#{1,6}\s/.test(line)) {
      flush();
      const level = line.match(/^#+/)[0].length;
      blocks.push({ type: "h", level, content: line.replace(/^#+\s/, "") });
    } else if (/^\s*[-*]\s/.test(line)) {
      if (listType !== "ul") { flush(); listType = "ul"; list = []; }
      list.push(line.replace(/^\s*[-*]\s/, ""));
    } else if (/^\s*\d+\.\s/.test(line)) {
      if (listType !== "ol") { flush(); listType = "ol"; list = []; }
      list.push(line.replace(/^\s*\d+\.\s/, ""));
    } else if (line.trim() === "---") {
      flush();
      blocks.push({ type: "hr" });
    } else if (line.trim() === "") {
      flush();
    } else {
      flush();
      blocks.push({ type: "p", content: line });
    }
  });
  flush();

  return (
    <div className="prose-qru text-[15px] text-foreground">
      {blocks.map((b, i) => {
        if (b.type === "h") {
          const Tag = `h${Math.min(b.level, 4)}`;
          return <Tag key={i} dangerouslySetInnerHTML={{ __html: inline(b.content) }} />;
        }
        if (b.type === "p") return <p key={i} dangerouslySetInnerHTML={{ __html: inline(b.content) }} />;
        if (b.type === "hr") return <hr key={i} />;
        if (b.type === "ul")
          return <ul key={i}>{b.items.map((it, j) => <li key={j} dangerouslySetInnerHTML={{ __html: inline(it) }} />)}</ul>;
        if (b.type === "ol")
          return <ol key={i}>{b.items.map((it, j) => <li key={j} dangerouslySetInnerHTML={{ __html: inline(it) }} />)}</ol>;
        return null;
      })}
    </div>
  );
}

const STATUS_STYLES = {
  Verified: "bg-success/10 text-success border-success/20",
  Approved: "bg-success/10 text-success border-success/20",
  Published: "bg-success/10 text-success border-success/20",
  Active: "bg-success/10 text-success border-success/20",
  Draft: "bg-muted text-muted-foreground border-border",
  Queued: "bg-muted text-muted-foreground border-border",
  Pending: "bg-warning/10 text-warning border-warning/20",
  "In Review": "bg-warning/10 text-warning border-warning/20",
  "Quality Review": "bg-warning/10 text-warning border-warning/20",
  Research: "bg-primary/10 text-primary border-primary/20",
  Manufacturing: "bg-primary/10 text-primary border-primary/20",
  Ready: "bg-success/10 text-success border-success/20",
  "Needs Review": "bg-warning/10 text-warning border-warning/20",
  "Needs Regeneration": "bg-destructive/10 text-destructive border-destructive/20",
  Generating: "bg-primary/10 text-primary border-primary/20",
  Paused: "bg-warning/10 text-warning border-warning/20",
  High: "bg-destructive/10 text-destructive border-destructive/20",
  Medium: "bg-warning/10 text-warning border-warning/20",
  Low: "bg-muted text-muted-foreground border-border",
};

export function StatusBadge({ status, testid }) {
  const cls = STATUS_STYLES[status] || "bg-muted text-muted-foreground border-border";
  return (
    <span
      data-testid={testid}
      className={`inline-flex items-center px-2 py-0.5 rounded-sm border text-xs font-medium ${cls}`}
    >
      {status}
    </span>
  );
}

export function PageHeader({ overline, title, description, actions }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8 animate-fade-up">
      <div className="pl-4 border-l-2 border-gold">
        {overline && <p className="overline text-royal mb-2">{overline}</p>}
        <h1 className="font-heading text-4xl sm:text-5xl font-bold tracking-tight text-navy leading-[1.05]">{title}</h1>
        {description && <p className="text-muted-foreground mt-3 max-w-2xl text-[15px] leading-relaxed">{description}</p>}
      </div>
      {actions && <div className="flex gap-2 shrink-0">{actions}</div>}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center border border-dashed rounded-md bg-card">
      {Icon && <Icon className="w-10 h-10 text-muted-foreground mb-4" strokeWidth={1.5} />}
      <h3 className="font-heading text-lg font-semibold">{title}</h3>
      {description && <p className="text-muted-foreground text-sm mt-1 max-w-sm">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function TreasureBadge({ testid }) {
  return (
    <span
      data-testid={testid}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm border border-gold bg-gold/10 text-[11px] font-semibold"
      style={{ color: "hsl(var(--navy))" }}
    >
      <svg width="11" height="11" viewBox="0 0 24 24" fill="hsl(var(--gold))"><path d="M12 2l2.9 6.1 6.6.9-4.8 4.6 1.2 6.6L12 18.6 6.1 21.8l1.2-6.6L2.5 9l6.6-.9z"/></svg>
      Treasure Standard™
    </span>
  );
}

const QRU_METHOD = [
  { key: "the_question", label: "The Question" },
  { key: "simple_answer", label: "Simple Answer" },
  { key: "why_it_matters", label: "Why It Matters" },
  { key: "real_world_example", label: "Real-World Example" },
  { key: "qru_translation", label: "QRU Translation™" },
  { key: "everyday_analogy", label: "Everyday Analogy" },
  { key: "memory_sentence", label: "Memory Sentence™", highlight: true },
  { key: "practice_application", label: "Practice / Application", list: true },
  { key: "key_vocabulary", label: "Key Vocabulary", vocab: true },
  { key: "deep_roots", label: "Deep Roots™" },
];

function isFilled(v) {
  if (Array.isArray(v)) return v.length > 0;
  return !!(v && String(v).trim());
}

export function QRUMethodology({ record, sectionStatus = {} }) {
  return (
    <div className="space-y-3">
      {QRU_METHOD.map(({ key, label, highlight, list, vocab }) => {
        const val = record[key];
        const filled = isFilled(val);
        const status = sectionStatus[key] || (filled ? "Verified" : "Empty");
        if (highlight && filled) {
          return (
            <div key={key} className="rounded-md p-5 text-white" style={{ background: "hsl(var(--royal))" }} data-testid={`qru-${key}`}>
              <div className="flex items-center justify-between mb-2">
                <p className="overline text-gold">{label}</p>
                <SectionStatusPill status={status} />
              </div>
              <p className="font-heading text-lg font-semibold leading-snug">{val}</p>
            </div>
          );
        }
        return (
          <div key={key} className="bg-card border rounded-md p-5" data-testid={`qru-${key}`}>
            <div className="flex items-center justify-between mb-2">
              <p className="overline text-primary">{label}</p>
              <SectionStatusPill status={status} />
            </div>
            {!filled ? (
              <p className="text-sm text-muted-foreground italic">Not yet manufactured.</p>
            ) : vocab ? (
              <dl className="grid sm:grid-cols-2 gap-2 text-sm">
                {val.map((v, i) => (
                  <div key={i} className="border rounded-sm p-2">
                    <dt className="font-semibold">{v.term}</dt>
                    <dd className="text-muted-foreground">{v.definition}</dd>
                  </div>
                ))}
              </dl>
            ) : list ? (
              <ul className="space-y-1.5 text-sm">
                {val.map((v, i) => (
                  <li key={i} className="flex gap-2"><span className="text-gold font-heading font-bold">{i + 1}</span>{v}</li>
                ))}
              </ul>
            ) : (
              <p className="text-[15px] leading-relaxed">{val}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function SectionStatusPill({ status }) {
  const map = {
    Verified: "bg-success/10 text-success border-success/20",
    Approved: "bg-success/10 text-success border-success/20",
    Draft: "bg-warning/15 border-warning/30",
    Empty: "bg-muted text-muted-foreground border-border",
  };
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded-sm border ${map[status] || map.Empty}`}
      style={status === "Draft" ? { color: "hsl(var(--navy))" } : {}}>
      {status}
    </span>
  );
}

const FIELD_LABELS = {
  the_question: "The Question", simple_answer: "Simple Answer", why_it_matters: "Why It Matters",
  real_world_example: "Real-World Example", qru_translation: "QRU Translation™", everyday_analogy: "Everyday Analogy",
  memory_sentence: "Memory Sentence™", practice_application: "Practice / Application", key_vocabulary: "Key Vocabulary",
  deep_roots: "Deep Roots™", summary: "Summary", conversation_starter: "Conversation Starter™", cheat_sheet: "Cheat Sheet™",
  common_misconceptions: "Common Misconceptions", step_by_step: "Step-by-Step", applications: "Applications",
  benefits: "Benefits", risks: "Risks", vocabulary_decoder: "Vocabulary Decoder™", faq: "FAQ",
  practice_questions: "Practice Questions", reflection_questions: "Reflection Questions",
  kingdom_lion_questions: "Kingdom Lion Verification Questions™", quiz: "Quiz", certification_questions: "Certification Questions",
  story_version: "Story Version", children_version: "Children's Version", teen_version: "Teen Version",
  adult_version: "Adult Version", professional_version: "Professional Version", teacher_notes: "Teacher Notes",
  parent_notes: "Parent Notes", student_notes: "Student Notes", call_to_action: "Call to Action",
  visual_description: "Visual Description", image_prompt: "Image Prompt", infographic_text: "Infographic Text",
  poster_text: "Poster Text", presentation_outline: "Presentation Outline", presentation_script: "Presentation Script",
  podcast_script: "Podcast Script", video_script: "Video Script", social_media_pack: "Social Media Pack",
  lesson_plan: "Lesson Plan", workbook_activities: "Workbook Activities",
};

export function fieldLabel(k) {
  return FIELD_LABELS[k] || k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function FieldValue({ value }) {
  if (value == null || (Array.isArray(value) && value.length === 0) || value === "")
    return <p className="text-sm text-muted-foreground italic">Not yet manufactured.</p>;
  if (Array.isArray(value)) {
    return (
      <ul className="space-y-1.5 text-sm">
        {value.map((it, i) => {
          if (it && typeof it === "object") {
            if ("term" in it) return <li key={i}><b>{it.term}</b> — <span className="text-muted-foreground">{it.definition}</span></li>;
            if ("question" in it) return (
              <li key={i}>
                <b>{it.question}</b>
                {it.options && <ul className="pl-4 list-disc text-muted-foreground">{it.options.map((o, j) => <li key={j}>{o}</li>)}</ul>}
                {it.answer && <span className="text-success text-xs"> Answer: {it.answer}</span>}
              </li>
            );
            return <li key={i}>{JSON.stringify(it)}</li>;
          }
          return <li key={i} className="flex gap-2"><span className="text-gold font-heading font-bold">{i + 1}</span>{it}</li>;
        })}
      </ul>
    );
  }
  return <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{value}</p>;
}
