import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(new URL(
  "../../supabase/functions/ai-trade-founder-mt5/index.ts",
  import.meta.url), "utf8");
const between = (start, end) => {
  assert.ok(source.includes(start) && source.includes(end));
  return source.split(start)[1].split(end)[0];
};
const verify = between("async function verifyStoredDemo(", "async function freshSnapshot(");
const investor = between("async function freshSnapshot(", "\nDeno.serve(");

test("investor readback does not restore password-verified CONNECTED state", () => {
  assert.ok(investor.includes('readback:"investor_snapshot"'));
  assert.equal(investor.includes("update ai_trade.account_mt5_bindings"), false);
  assert.equal(investor.includes("connection_state='CONNECTED'"), false);
  assert.ok(investor.includes("select b.id,b.account_login,b.server"));
  assert.ok(investor.includes("b.connection_state!='REVOKED'"));
});

test("investor readback rechecks exact binding and the same Founder after broker IO", () => {
  assert.ok(investor.includes("const current=await sql"));
  assert.ok(investor.indexOf("const current=await sql")
    > investor.indexOf("const observed="));
  assert.ok(investor.includes("where b.id=${binding.id} and b.access_token_id=${id}"));
  assert.ok(investor.includes("g.user_id=${userId}::uuid and g.active=true"));
  assert.ok(investor.includes("d.revoked_at is null"));
  assert.ok(investor.includes("d.expires_at>now()"));
  assert.ok(investor.includes("d.entitlement_state not in ('SUSPENDED','REVOKED')"));
  assert.ok(investor.includes('status:"BINDING_OR_FOUNDER_CHANGED"'));
  assert.ok(investor.indexOf("if(current.length!==1)") <
    investor.indexOf('status:"DEMO_SNAPSHOT_READ_ONLY"'));
});

test("master-password verification still requires Founder and exactly one DISCONNECTED binding", () => {
  assert.ok(verify.includes('readback:"founder_verify",verifyPassword:password'));
  assert.ok(verify.includes("connection_state='DISCONNECTED'"));
  assert.ok(verify.includes("connection_state='CONNECTED',last_verified_at=now()"));
  assert.ok(verify.includes("and exists ("));
  assert.ok(verify.includes("g.user_id=${userId}::uuid"));
  assert.ok(verify.includes("g.active=true and d.access_role='FOUNDER'"));
  assert.ok(verify.includes("d.revoked_at is null and d.expires_at>now()"));
  assert.ok(verify.includes("if(updated.length!==1)"));
});

test("Google entitlement remains mandatory; no anonymous DEMO fallback", () => {
  assert.ok(source.includes("return rows[0]?{id:Number(rows[0].id),userId:uid}:null;"));
  assert.ok(source.includes("freshSnapshot(person.id,person.userId)"));
  assert.ok(source.includes("verifyStoredDemo(req,person.id,person.userId)"));
  assert.ok(source.includes('status:"GOOGLE_FOUNDER_REQUIRED"'));
});
