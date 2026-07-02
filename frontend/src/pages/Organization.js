import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Crown, Users2, Sparkles, Activity, Building2, Cpu } from "lucide-react";

function WorkloadBar({ value }) {
  return (
    <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
      <div className="h-full bg-gold" style={{ width: `${value}%` }} />
    </div>
  );
}

export default function Organization() {
  const [agents, setAgents] = useState([]);
  const [activity, setActivity] = useState([]);
  const [taskTypes, setTaskTypes] = useState([]);
  const [team, setTeam] = useState(null);
  const [taskType, setTaskType] = useState("");

  const loadActivity = () => api.get("/org-activity").then((r) => setActivity(r.data)).catch(() => {});

  useEffect(() => {
    api.get("/registry").then((r) => setAgents(r.data)).catch(() => {});
    api.get("/registry/task-types").then((r) => { setTaskTypes(r.data.task_types); setTaskType(r.data.task_types[0]); }).catch(() => {});
    loadActivity();
    const iv = setInterval(loadActivity, 5000);
    return () => clearInterval(iv);
  }, []);

  const assemble = async (t) => {
    setTaskType(t);
    const { data } = await api.post("/registry/assemble", { task_type: t });
    setTeam(data.team);
  };

  const board = agents.filter((a) => a.is_board);
  const emergent = agents.filter((a) => a.origin === "Emergent");

  return (
    <div>
      <PageHeader
        overline="QRU Enterprise Organization™"
        title="The Company at Work"
        description="Specialized AI departments that research, verify, manufacture, brand, and publish — collaborating in real time. QRU extends Emergent's platform specialists rather than replacing them."
      />

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-8">
          {/* Executive Board */}
          <div>
            <p className="overline text-primary mb-3 flex items-center gap-2"><Crown className="w-4 h-4" /> QRU Executive Board</p>
            <div className="grid sm:grid-cols-2 gap-3">
              {board.map((a) => (
                <div key={a.id} data-testid={`board-${a.id}`} className="bg-card border rounded-md p-4">
                  <div className="flex items-start gap-3">
                    {a.avatar ? <img src={a.avatar} alt="" className="w-10 h-10 rounded-sm object-cover" />
                      : <div className="w-10 h-10 rounded-sm bg-primary/10 text-primary flex items-center justify-center"><Building2 className="w-5 h-5" /></div>}
                    <div className="flex-1 min-w-0">
                      <p className="font-heading font-semibold text-sm leading-tight">{a.name}</p>
                      <p className="text-xs text-muted-foreground">{a.title}</p>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-sm border border-success/30 bg-success/10 text-success">{a.availability}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-3">
                    {a.expertise.slice(0, 3).map((e) => <span key={e} className="text-[10px] bg-muted px-1.5 py-0.5 rounded-sm">{e}</span>)}
                  </div>
                  <div className="mt-3">
                    <div className="flex justify-between text-[10px] text-muted-foreground mb-1"><span>Workload</span><span>{a.projects_assigned} projects</span></div>
                    <WorkloadBar value={a.workload} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Expertise Registry — Emergent specialists */}
          <div>
            <p className="overline text-primary mb-3 flex items-center gap-2"><Cpu className="w-4 h-4" /> Expertise Registry — Emergent Platform Specialists</p>
            <div className="bg-card border rounded-md overflow-hidden">
              <table className="w-full text-sm">
                <thead><tr className="border-b bg-muted/40 text-left">
                  <th className="px-4 py-2.5 overline text-muted-foreground">Specialist</th>
                  <th className="px-4 py-2.5 overline text-muted-foreground hidden sm:table-cell">Expertise</th>
                  <th className="px-4 py-2.5 overline text-muted-foreground">Workload</th>
                </tr></thead>
                <tbody>
                  {emergent.map((a) => (
                    <tr key={a.id} data-testid={`registry-${a.id}`} className="border-b last:border-0">
                      <td className="px-4 py-2.5"><span className="font-medium">{a.title}</span><span className="ml-2 text-[10px] px-1.5 py-0.5 rounded-sm border bg-primary/5 text-primary">Emergent</span></td>
                      <td className="px-4 py-2.5 text-muted-foreground hidden sm:table-cell">{a.expertise.join(", ")}</td>
                      <td className="px-4 py-2.5 w-32"><WorkloadBar value={a.workload} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Collaborative Review Team Assembler */}
          <div>
            <p className="overline text-primary mb-3 flex items-center gap-2"><Users2 className="w-4 h-4" /> Assemble a Collaborative Review Team</p>
            <div className="bg-card border rounded-md p-5">
              <div className="flex flex-wrap gap-2 mb-4">
                {taskTypes.map((t) => (
                  <button key={t} data-testid={`task-${t.replace(/\s|\//g, "-")}`} onClick={() => assemble(t)}
                    className={`text-xs px-3 py-1.5 rounded-sm border transition-colors ${taskType === t && team ? "bg-primary text-primary-foreground border-primary" : "hover:border-primary"}`}>
                    {t}
                  </button>
                ))}
              </div>
              {team ? (
                <div className="grid sm:grid-cols-2 gap-2" data-testid="assembled-team">
                  {team.map((a) => (
                    <div key={a.id} className="flex items-center gap-2 border rounded-sm px-3 py-2 text-sm">
                      <Sparkles className="w-3.5 h-3.5 text-gold" /> <span className="font-medium">{a.name || a.title}</span>
                      <span className="text-xs text-muted-foreground ml-auto">{a.department}</span>
                    </div>
                  ))}
                </div>
              ) : <p className="text-sm text-muted-foreground">Pick a task type to assemble the most qualified specialists.</p>}
            </div>
          </div>
        </div>

        {/* Live Organization Activity */}
        <div className="bg-card border rounded-md p-5 h-fit lg:sticky lg:top-24">
          <p className="overline text-primary mb-3 flex items-center gap-2"><Activity className="w-4 h-4" /> Live Organization Activity</p>
          <div className="space-y-3 max-h-[70vh] overflow-y-auto" data-testid="org-activity">
            {activity.length === 0 && <p className="text-sm text-muted-foreground">The organization is idle. Approve a Knowledge Record to see departments collaborate.</p>}
            {activity.map((a) => (
              <div key={a.id} className="flex items-start gap-2.5 text-sm">
                <span className={`w-1.5 h-1.5 rounded-full mt-2 shrink-0 ${a.level === "success" ? "bg-success" : "bg-gold"}`} />
                <div>
                  <span className="font-medium">{a.agent}</span>{" "}
                  <span className="text-muted-foreground">{a.action}</span>{" "}
                  {a.entity && <span className="font-mono text-xs">{a.entity}</span>}
                  <p className="text-[10px] text-muted-foreground">{a.department} Dept.</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
