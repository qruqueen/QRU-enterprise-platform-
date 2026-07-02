import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, LineChart, Line, Legend,
} from "recharts";

const COLORS = ["#0047FF", "#10B981", "#F59E0B", "#8B5CF6", "#06B6D4", "#EF4444", "#3B82F6"];

function ChartCard({ title, subtitle, children, testid }) {
  return (
    <div data-testid={testid} className="bg-card border rounded-md p-6">
      <h3 className="font-heading font-semibold text-lg">{title}</h3>
      {subtitle && <p className="text-sm text-muted-foreground mb-4">{subtitle}</p>}
      <div className="h-64 mt-2">{children}</div>
    </div>
  );
}

export default function Analytics() {
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/analytics/overview").then((r) => setD(r.data)).catch(() => {}); }, []);
  const data = d || {};

  return (
    <div>
      <PageHeader
        overline="Analytics"
        title="Enterprise Intelligence"
        description="Knowledge growth, manufacturing productivity, and digital workforce performance at a glance."
      />

      <div className="grid lg:grid-cols-2 gap-6">
        <ChartCard title="Knowledge Growth" subtitle="Verified records over time" testid="chart-growth">
          <ResponsiveContainer>
            <LineChart data={data.knowledge_growth || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#999" />
              <YAxis tick={{ fontSize: 12 }} stroke="#999" />
              <Tooltip />
              <Line type="monotone" dataKey="records" stroke="#0047FF" strokeWidth={2.5} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Products by Type" subtitle="Manufacturing output mix" testid="chart-products">
          <ResponsiveContainer>
            <BarChart data={data.products_by_type || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#999" interval={0} angle={-20} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 12 }} stroke="#999" allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#0047FF" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Knowledge by Category" subtitle="Distribution across colleges" testid="chart-category">
          <ResponsiveContainer>
            <PieChart>
              <Pie data={data.knowledge_by_category || []} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={{ fontSize: 11 }}>
                {(data.knowledge_by_category || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Digital Workforce Performance" subtitle="Tasks completed by AI employees" testid="chart-workforce">
          <ResponsiveContainer>
            <BarChart data={data.employee_performance || []} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12 }} stroke="#999" />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} stroke="#999" width={90} />
              <Tooltip />
              <Bar dataKey="tasks" fill="#10B981" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
