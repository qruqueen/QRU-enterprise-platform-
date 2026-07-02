import { useAuth } from "@/context/AuthContext";
import { PageHeader } from "@/components/shared";
import { Boxes, User, ShieldCheck, Sparkles } from "lucide-react";

export default function Settings() {
  const { user } = useAuth();
  return (
    <div>
      <PageHeader overline="Settings" title="Enterprise Settings" description="Your profile and the QRU Factory operating configuration." />

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-card border rounded-md p-6">
          <div className="flex items-center gap-2 mb-4"><User className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">Profile</h3></div>
          <dl className="text-sm space-y-3">
            <div className="flex justify-between"><dt className="text-muted-foreground">Name</dt><dd className="font-medium">{user?.name}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Email</dt><dd className="font-medium">{user?.email}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Role</dt><dd><span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-sm font-medium">{user?.role}</span></dd></div>
          </dl>
        </div>

        <div className="bg-card border rounded-md p-6">
          <div className="flex items-center gap-2 mb-4"><Sparkles className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">AI Configuration</h3></div>
          <dl className="text-sm space-y-3">
            <div className="flex justify-between"><dt className="text-muted-foreground">Command Model</dt><dd className="font-medium">GPT-5.5</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Manufacturing Model</dt><dd className="font-medium">GPT-5.5</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Human Approval</dt><dd className="font-medium text-success">Required for publication</dd></div>
          </dl>
        </div>

        <div className="bg-card border rounded-md p-6 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4"><ShieldCheck className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">AI Philosophy</h3></div>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-3xl">
            AI exists to assist humans. Humans remain responsible for truth, ethics, governance, and final approval.
            No product is published without human approval. QRU does not simplify the truth — QRU simplifies the path to understanding the truth.
          </p>
        </div>

        <div className="bg-[#0A0A0A] text-white rounded-md p-6 lg:col-span-2 flex items-center gap-4">
          <div className="w-11 h-11 rounded-sm bg-primary flex items-center justify-center shrink-0"><Boxes className="w-6 h-6" /></div>
          <div>
            <p className="font-heading font-bold">QRU FACTORY™ · Knowledge Manufacturing OS</p>
            <p className="text-white/50 text-sm">Quest for Real Understanding · Built to evolve for decades.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
