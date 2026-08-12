import { describe, expect, it } from "vitest";

import { countByEntity, filterRecords, normalizeEntityLabel } from "./domain";

const records = [
  { id: 1, entity: "account", name: "Acme", status: "active" },
  { id: 2, entity: "deal", name: "Renewal", status: "review" }
];

describe("domain helpers", () => {
  it("normalizes entity labels", () => expect(normalizeEntityLabel("usage_event")).toBe("Usage Event"));
  it("counts tenant records by entity", () => expect(countByEntity(records, "deal")).toBe(1));
  it("filters records by business fields", () => expect(filterRecords(records, "renew")).toEqual([records[1]]));
});
