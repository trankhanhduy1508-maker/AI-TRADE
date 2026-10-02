import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseFounderDemoLogin } from "../../supabase/functions/ai-trade-founder-mt5/demo-login-contract.mjs";

const sample = () => ({
  login: "123456", server: "MetaQuotes-Demo", password: "mock-password-only",
});

test("exact DEMO credentials passed through without mutation", () => {
  assert.deepEqual(parseFounderDemoLogin(sample()), sample());
});
test("reject invalid accounts and wrong broker or LIVE server", () => {
  for (const login of ["", "012345", "123", "1234567890123456", "123 456", 123456]) {
    assert.throws(() => parseFounderDemoLogin({ ...sample(), login }),
      /INVALID_DEMO_CREDENTIAL_FORMAT/);
  }
  for (const server of ["Other-Demo", "Broker-Live", "MetaQuotes-Demo ", "", null]) {
    assert.throws(() => parseFounderDemoLogin({ ...sample(), server }),
      /INVALID_DEMO_CREDENTIAL_FORMAT/);
  }
});
test("reject missing, non-string, oversized and control-character passwords", () => {
  for (const password of [undefined, null, 42, "", "abc", "x".repeat(33),
                          "mock\npassword", "mock\u0000password"]) {
    assert.throws(() => parseFounderDemoLogin({ ...sample(), password }),
      /INVALID_DEMO_CREDENTIAL_FORMAT/);
  }
});
test("reject null, array and forged payloads", () => {
  for (const value of [null, [], "123456", undefined]) {
    assert.throws(() => parseFounderDemoLogin(value),
      /INVALID_DEMO_CREDENTIAL_FORMAT/);
  }
});

test("Founder login uses transient broker input without a Vault shortcut", () => {
  const founder = readFileSync(new URL(
    "../../supabase/functions/ai-trade-founder-mt5/index.ts", import.meta.url),
    "utf8");
  const verifier = readFileSync(new URL(
    "../../supabase/functions/ai-trade-mt5-demo-validate/index.ts", import.meta.url),
    "utf8");
  const current = founder.split("async function verifyStoredDemo(")[1]
    .split("async function freshSnapshot(")[0];
  assert.ok(current);
  assert.equal(current.includes("vault.decrypted_secrets"), false);
  assert.equal(current.includes("samePassword("), false);
  assert.ok(current.includes('readback:"founder_verify",verifyPassword:password'));
  assert.ok(current.includes("connection_state='DISCONNECTED'"));
  assert.ok(verifier.includes("direct?body.verifyPassword"));
  assert.ok(verifier.includes("a.account_login=${BigInt(requested)}"));
  assert.equal(current.includes("order_send"), false);
  assert.equal(current.includes("trade_request"), false);
});
