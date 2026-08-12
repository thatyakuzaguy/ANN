"use client";

import { useMemo, useState } from "react";
import { Activity, Building2, CircleDollarSign, Database, GitBranch, Plus, ShieldCheck, Workflow } from "lucide-react";

const productName = "LMS SaaS";
const description = "Courses, lessons, modules, enrollments, student progress, certificates, and billing.";
const domainId = "lms";
const entities: string[] = ["course", "lesson", "module", "enrollment", "student", "progress", "certificate"];
const workflows: string[] = ["course completion", "drip schedule", "assessment review", "certificate issue"];
const integrations: string[] = ["video", "email", "analytics", "payments"];
const primaryEntity = "course";
const primaryActionLabel = "New course";

type DemoRecord = { id: number; entity: string; name: string; status: string };

const initialRecords: DemoRecord[] = entities.map((entity, index) => ({
  id: index + 1,
  entity,
  name: `Demo ${entity.replaceAll("_", " ")}`,
  status: index % 3 === 0 ? "review" : "active"
}));

const operatingModules = [
  { title: "Tenant isolation", detail: "Every domain query is scoped by authenticated tenant membership.", icon: Building2 },
  { title: "Granular RBAC", detail: "Owner, admin, manager, contributor, and viewer permissions.", icon: ShieldCheck },
  { title: "Subscription billing", detail: "Stripe checkout, portal, and signed webhook boundaries.", icon: CircleDollarSign },
  { title: "Workflow engine", detail: workflows.join(", "), icon: Workflow },
  { title: "Integrations", detail: integrations.join(", "), icon: GitBranch },
  { title: "Audit trail", detail: "Tenant, identity, and business events retain actor context.", icon: Activity }
];

export default function Home() {
  const [records, setRecords] = useState(initialRecords);
  const [query, setQuery] = useState("");
  const filtered = useMemo(
    () => records.filter((record) => `${record.entity} ${record.name} ${record.status}`.toLowerCase().includes(query.toLowerCase())),
    [query, records]
  );

  function addRecord() {
    setRecords((current) => [
      ...current,
      { id: Date.now(), entity: primaryEntity, name: `New ${primaryEntity.replaceAll("_", " ")}`, status: "draft" }
    ]);
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <h1>{productName}</h1>
        <p>{description}</p>
        <div className="tenant-pill">Tenant: enterprise-demo</div>
        <p>Domain API: /{domainId}</p>
      </aside>
      <section className="main">
        <div className="toolbar">
          <input
            aria-label={`Search ${productName}`}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={`Search ${entities.slice(0, 3).join(", ")}...`}
            value={query}
          />
          <button type="button" onClick={addRecord}><Plus size={16} /> {primaryActionLabel}</button>
        </div>
        <div className="grid">
          {entities.slice(0, 6).map((entity) => (
            <article className="card" key={entity}>
              <Database size={18} />
              <h2>{records.filter((record) => record.entity === entity).length}</h2>
              <p>{entity.replaceAll("_", " ")}</p>
            </article>
          ))}
        </div>
        <div className="modules">
          {operatingModules.map((module) => {
            const Icon = module.icon;
            return (
              <article className="module" key={module.title}>
                <Icon size={18} />
                <div><h2>{module.title}</h2><p>{module.detail}</p></div>
              </article>
            );
          })}
        </div>
        <div className="pipeline" aria-label={`${productName} records`}>
          {entities.slice(0, 4).map((entity) => (
            <section className="stage" key={entity}>
              <h2>{entity.replaceAll("_", " ")}</h2>
              {filtered.filter((record) => record.entity === entity).map((record) => (
                <button
                  className="deal"
                  key={record.id}
                  onClick={() => setRecords((current) => current.map((item) => item.id === record.id ? { ...item, status: "active" } : item))}
                  type="button"
                >
                  {record.name} · {record.status}
                </button>
              ))}
            </section>
          ))}
        </div>
      </section>
    </main>
  );
}
