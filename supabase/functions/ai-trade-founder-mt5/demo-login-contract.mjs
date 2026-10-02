/** Pure, fail-closed validation for the existing Founder's MetaQuotes-Demo login.
 * No persistence, no HTTP and no broker access. The password stays transient. */
export function parseFounderDemoLogin(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new Error("INVALID_DEMO_CREDENTIAL_FORMAT");
  }
  const { login, server, password } = body;
  if (typeof login !== "string" || !/^[1-9][0-9]{4,14}$/.test(login)
      || server !== "MetaQuotes-Demo"
      || typeof password !== "string"
      || password.length < 4 || password.length > 32
      || /[\u0000-\u001F\u007F]/.test(password)) {
    throw new Error("INVALID_DEMO_CREDENTIAL_FORMAT");
  }
  return { login, server, password };
}
