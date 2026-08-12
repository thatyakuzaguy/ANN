export type DomainRecord = { id: number; entity: string; name: string; status: string };

export function normalizeEntityLabel(entity: string): string {
  return entity.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function countByEntity(records: DomainRecord[], entity: string): number {
  return records.filter((record) => record.entity === entity).length;
}

export function filterRecords(records: DomainRecord[], query: string): DomainRecord[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return records;
  return records.filter((record) =>
    `${record.entity} ${record.name} ${record.status}`.toLowerCase().includes(normalized)
  );
}
