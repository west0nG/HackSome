// Foundagent mail ingress — Cloudflare Email Worker (07-08 agent-email, design §2.1).
//
// DELIBERATELY DUMB: stream the raw MIME into R2 and stop. No MIME parsing
// (Workers Free caps CPU at 10ms/invocation — parsing risks EXCEEDED_CPU) and
// no Company routing knowledge in the cloud — the platform singleton router
// (peripheral/email/poller.py) owns parsing and global Company resolution.
//
// R2 object contract (design §2.2): `inbox/<epoch-ms>-<uuid>.eml` with the
// SMTP envelope in customMetadata — `to` is the envelope RCPT TO, the
// poller's sole routing key (more reliable than the To: header: BCC/alias
// delivery never shows the address in headers); `from` is MAIL FROM.

// Self-contained structural types: no npm packages by design (plain wrangler
// bundles TS without type-checking; these only document the shapes we use).
interface Env {
  MAIL_BUCKET: {
    put(
      key: string,
      value: ReadableStream,
      options?: { customMetadata?: Record<string, string> },
    ): Promise<unknown>;
  };
}

interface InboundEmailMessage {
  readonly from: string; // envelope MAIL FROM
  readonly to: string; // envelope RCPT TO — the routing key
  readonly raw: ReadableStream;
  readonly rawSize: number;
}

// Workers runtime global (not in lib.dom).
declare const FixedLengthStream: new (length: number) => {
  readable: ReadableStream;
  writable: WritableStream;
};

export default {
  async email(message: InboundEmailMessage, env: Env): Promise<void> {
    const key = `inbox/${Date.now()}-${crypto.randomUUID()}.eml`;
    // R2 put() requires a stream of KNOWN length; message.raw does not
    // advertise one by itself, so pipe through FixedLengthStream(rawSize).
    const body = message.raw.pipeThrough(new FixedLengthStream(message.rawSize));
    await env.MAIL_BUCKET.put(key, body, {
      customMetadata: { to: message.to, from: message.from },
    });
  },
};
