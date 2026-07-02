import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { GraduationCap, ArrowUpRight, Lock } from "lucide-react";

export default function Colleges() {
  const [colleges, setColleges] = useState([]);
  const navigate = useNavigate();
  useEffect(() => { api.get("/colleges").then((r) => setColleges(r.data)).catch(() => {}); }, []);

  const divisions = [...new Set(colleges.map((c) => c.division))];

  return (
    <div>
      <PageHeader
        overline="Understanding Colleges"
        title="Colleges of the Understanding OS"
        description="Every division plugs into the same operating system. Knowledge, research, and products are manufactured per college — Health today, with Trading, Finance, AI, Programming, Parenting, Business and Government joining the same factory."
      />

      {divisions.map((div) => (
        <div key={div} className="mb-8">
          <p className="overline text-primary mb-3">{div} Division</p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {colleges.filter((c) => c.division === div).map((c) => {
              const active = c.status === "Active";
              return (
                <div key={c.id} data-testid={`college-${c.id}`}
                  onClick={() => active && navigate(`/colleges/${c.id}`)}
                  className={`bg-card border rounded-md overflow-hidden transition-all ${active ? "hover:-translate-y-1 hover:shadow-sm cursor-pointer" : "opacity-70"}`}>
                  <div className="h-2" style={{ backgroundColor: c.color }} />
                  <div className="p-5">
                    <div className="flex items-start justify-between">
                      <div className="w-10 h-10 rounded-sm flex items-center justify-center" style={{ backgroundColor: `${c.color}1a`, color: c.color }}>
                        <GraduationCap className="w-5 h-5" />
                      </div>
                      {active ? <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
                        : <span className="text-[10px] flex items-center gap-1 text-muted-foreground border rounded-sm px-1.5 py-0.5"><Lock className="w-3 h-3" />Coming Soon</span>}
                    </div>
                    <h3 className="font-heading font-semibold text-lg mt-3">{c.name}</h3>
                    <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{c.description}</p>
                    {active && (
                      <div className="flex gap-4 mt-4 text-xs text-muted-foreground">
                        <span><b className="text-foreground">{c.records}</b> records</span>
                        <span><b className="text-foreground">{c.products}</b> products</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
