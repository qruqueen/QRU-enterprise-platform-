import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/api";
import { StatusBadge } from "@/components/shared";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ArrowLeft, Loader2, BookOpen, FlaskConical, Factory, FileText } from "lucide-react";

const WORKSPACE_TABS = [
  "Knowledge Records", "Research", "Posters", "Workbooks", "Presentations",
  "Teacher Guides", "AI Tutors", "Videos", "Manufacturing Orders", "Product Library",
];

const TAB_PRODUCT_TYPE = {
  Posters: "Poster", Workbooks: "Workbook", Presentations: "Presentation",
  "Teacher Guides": "Teacher Guide", "AI Tutors": "AI Tutor", Videos: "Video Script",
};

export default function CollegeWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ws, setWs] = useState(null);

  useEffect(() => { api.get(`/colleges/${id}/workspace`).then((r) => setWs(r.data)).catch(() => {}); }, [id]);

  if (!ws) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  const { college, knowledge_records: krs, products, manufacturing_orders: mos, stats } = ws;

  const productsOfType = (type) => products.filter((p) => p.product_type === type);

  return (
    <div className="animate-fade-up">
      <button onClick={() => navigate("/colleges")} data-testid="cw-back" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="w-4 h-4" /> Understanding Colleges
      </button>

      <div className="rounded-md p-6 mb-6 text-white" style={{ background: "hsl(var(--navy))" }}>
        <p className="overline text-gold mb-1">{college.division} Division</p>
        <h1 className="font-heading text-3xl font-bold tracking-tight">{college.name}</h1>
        <p className="text-white/70 mt-2 max-w-2xl">{college.description}</p>
        <div className="flex gap-6 mt-5">
          {[["Records", stats.records], ["Verified", stats.verified], ["Products", stats.products], ["Orders", stats.orders]].map(([l, v]) => (
            <div key={l}><p className="font-heading text-2xl font-bold text-gold">{v}</p><p className="text-xs text-white/60">{l}</p></div>
          ))}
        </div>
      </div>

      <Tabs defaultValue="Knowledge Records">
        <TabsList className="flex flex-wrap h-auto gap-1 bg-muted/50 p-1">
          {WORKSPACE_TABS.map((t) => (
            <TabsTrigger key={t} value={t} data-testid={`cw-tab-${t.toLowerCase().replace(/\s/g, "-")}`} className="text-xs">{t}</TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="Knowledge Records" className="mt-5">
          <WorkspaceList items={krs} empty="No knowledge records in this college yet." icon={BookOpen}
            render={(r) => (
              <Link key={r.id} to={`/knowledge/${r.id}`} className="bg-card border rounded-md p-4 hover:border-primary transition-colors block">
                <div className="flex items-center gap-2 mb-1"><span className="font-mono text-[11px] text-muted-foreground">{r.kr_code}</span><StatusBadge status={r.verification_status} /></div>
                <p className="font-medium">{r.title}</p>
              </Link>
            )} />
        </TabsContent>

        <TabsContent value="Research" className="mt-5">
          <div className="bg-card border border-dashed rounded-md p-10 text-center">
            <FlaskConical className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
            <p className="font-heading font-semibold">Research workspace</p>
            <p className="text-sm text-muted-foreground mt-1">Launch new investigations in the <Link to="/research" className="text-primary hover:underline">Research Center</Link>.</p>
          </div>
        </TabsContent>

        {["Posters", "Workbooks", "Presentations", "Teacher Guides", "AI Tutors", "Videos"].map((t) => (
          <TabsContent key={t} value={t} className="mt-5">
            <WorkspaceList items={productsOfType(TAB_PRODUCT_TYPE[t])} empty={`No ${t.toLowerCase()} manufactured yet.`} icon={FileText}
              render={(p) => (
                <Link key={p.id} to={`/products/${p.id}`} className="bg-card border rounded-md p-4 hover:border-primary transition-colors block">
                  <span className="font-mono text-[11px] text-muted-foreground">{p.product_code}</span>
                  <p className="font-medium mt-1">{p.title}</p>
                </Link>
              )} />
          </TabsContent>
        ))}

        <TabsContent value="Manufacturing Orders" className="mt-5">
          <WorkspaceList items={mos} empty="No manufacturing orders for this college." icon={Factory}
            render={(o) => (
              <Link key={o.id} to="/manufacturing" className="bg-card border rounded-md p-4 hover:border-primary transition-colors block">
                <div className="flex items-center gap-2 mb-1"><span className="font-mono text-[11px] text-muted-foreground">{o.mo_code}</span><StatusBadge status={o.status} /></div>
                <p className="font-medium">{o.topic}</p>
              </Link>
            )} />
        </TabsContent>

        <TabsContent value="Product Library" className="mt-5">
          <WorkspaceList items={products} empty="No products yet." icon={FileText}
            render={(p) => (
              <Link key={p.id} to={`/products/${p.id}`} className="bg-card border rounded-md p-4 hover:border-primary transition-colors block">
                <p className="text-xs text-primary font-medium">{p.product_type}</p>
                <p className="font-medium mt-1">{p.title}</p>
              </Link>
            )} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function WorkspaceList({ items, empty, icon: Icon, render }) {
  if (!items || items.length === 0)
    return (
      <div className="bg-card border border-dashed rounded-md p-10 text-center">
        <Icon className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">{empty}</p>
      </div>
    );
  return <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">{items.map(render)}</div>;
}
