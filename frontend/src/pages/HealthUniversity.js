import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { HeartPulse, ArrowUpRight } from "lucide-react";

const OFFERINGS = ["QRU Health Journey™", "Posters", "Workbooks", "Presentations", "AI Tutors", "Caregiver Resources"];

export default function HealthUniversity() {
  const [colleges, setColleges] = useState([]);
  useEffect(() => { api.get("/health-university/colleges").then((r) => setColleges(r.data)).catch(() => {}); }, []);

  return (
    <div>
      <PageHeader
        overline="QRU Health University™"
        title="Colleges of Understanding"
        description="Health education organized into colleges. Each college manufactures journeys, posters, workbooks, presentations, AI tutors, and caregiver resources."
      />

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {colleges.map((c) => (
          <div key={c.id} data-testid={`college-${c.id}`} className="bg-card border rounded-md overflow-hidden hover:-translate-y-1 hover:shadow-sm transition-all">
            <div className="h-2" style={{ backgroundColor: c.color }} />
            <div className="p-5">
              <div className="flex items-start justify-between">
                <div className="w-10 h-10 rounded-sm flex items-center justify-center" style={{ backgroundColor: `${c.color}1a`, color: c.color }}>
                  <HeartPulse className="w-5 h-5" />
                </div>
                <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
              </div>
              <h3 className="font-heading font-semibold text-lg mt-3">{c.name}</h3>
              <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{c.description}</p>
              <div className="flex flex-wrap gap-1.5 mt-4">
                {OFFERINGS.slice(0, 4).map((o) => (
                  <span key={o} className="text-[10px] bg-muted px-2 py-0.5 rounded-sm">{o}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
