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
      <div>
        {overline && <p className="overline text-primary mb-2">{overline}</p>}
        <h1 className="font-heading text-3xl sm:text-4xl font-bold tracking-tight text-foreground">{title}</h1>
        {description && <p className="text-muted-foreground mt-2 max-w-2xl">{description}</p>}
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
