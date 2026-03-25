# Lab 07 — TLS Background

## What is TLS?

**Transport Layer Security (TLS)** is the cryptographic protocol that provides
the "S" in HTTPS.  It gives you three guarantees:

| Guarantee | Meaning |
|-----------|---------|
| **Confidentiality** | Data is encrypted; an eavesdropper on the network can't read it |
| **Integrity** | A tamper-detection MAC ensures data wasn't modified in transit |
| **Authentication** | The server proves its identity using a certificate signed by a trusted authority |

The older name for TLS is **SSL** (Secure Sockets Layer).  TLS 1.2 and TLS 1.3
are current; SSL 2/3 and TLS 1.0/1.1 are deprecated and should not be used.

---

## Certificates and Certificate Authorities

A TLS **certificate** binds a public key to an identity (domain name, organisation,
etc.) and is signed by a **Certificate Authority (CA)**.  Your browser ships with a
list of trusted CAs.  When it connects to a server:

1. The server sends its certificate.
2. The browser verifies the signature chain back to a trusted CA.
3. If the chain is valid and the domain matches, the browser shows the padlock icon.

### Self-Signed Certificates

A **self-signed** certificate is signed by the same key it contains — there is no
CA vouching for it.  Browsers (and curl without `-k`) will reject it with a warning
because they cannot verify the identity of the server.

Self-signed certificates are perfectly fine for:
- Local development environments
- Internal cluster-to-cluster communication (mTLS)
- Learning about TLS mechanics

They are **not** acceptable for any site accessed by end users.

---

## Generating a Self-Signed Certificate with openssl

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/key.pem \
    -out    certs/cert.pem \
    -subj "/CN=localhost/O=CSC420/C=US"
```

### What does each output file contain?

**`cert.pem`** — The certificate (public).  It includes:
- The server's public key
- Metadata: subject (CN, O, C), issuer, validity period, serial number
- A digital signature over all of the above (self-signed, so signed with its own private key)
- Encoded in PEM format (Base64 between `-----BEGIN CERTIFICATE-----` markers)

**`key.pem`** — The private key (secret).  It:
- Must never be committed to version control
- Must never be shared
- Is read by nginx at startup to perform the TLS handshake
- With `-nodes`, it is stored unencrypted so nginx can load it without a passphrase

---

## The TLS Handshake (simplified)

When a client (browser, curl) connects to nginx over HTTPS:

```
Client                                  nginx
  │                                       │
  │── ClientHello (supported cipher suites, TLS version) ──►│
  │                                       │
  │◄── ServerHello (chosen cipher suite) ─│
  │◄── Certificate (cert.pem)            ─│
  │                                       │
  │  [Client verifies certificate]        │
  │                                       │
  │── ClientKeyExchange (session key) ───►│
  │── ChangeCipherSpec ──────────────────►│
  │── Finished (encrypted) ─────────────►│
  │                                       │
  │◄── ChangeCipherSpec ──────────────────│
  │◄── Finished (encrypted) ──────────────│
  │                                       │
  │═══════════ Encrypted data ════════════│
```

After the handshake, all data is encrypted with symmetric keys derived from the
negotiated session.

---

## TLS Termination

**TLS termination** means decrypting HTTPS traffic at the edge (nginx) and
forwarding plain HTTP internally.  The internal Docker network is private and
trusted, so encryption inside the network is not required.

Benefits:
- Application code (Python/Flask) does not need to handle certificates.
- Certificate management is centralised at the proxy.
- You can swap or renew certificates without touching the application.

The `X-Forwarded-Proto: https` header that nginx adds tells the application
whether the original request was HTTPS, which the app can use for generating
correct redirect URLs or enforcing HTTPS-only APIs.

---

## Why Does My Browser Show a Warning?

Because the certificate is self-signed, your browser cannot verify it against
a trusted CA.  You will see a warning like:

- Chrome: "Your connection is not private" (NET::ERR_CERT_AUTHORITY_INVALID)
- Firefox: "Warning: Potential Security Risk Ahead"
- curl: `curl: (60) SSL certificate problem: self signed certificate`

To proceed in the browser, click "Advanced" → "Proceed to localhost (unsafe)".
In curl, add the `-k` / `--insecure` flag.

For a development workflow that avoids this warning, you can add the
certificate to your OS/browser's trusted store, or use a tool like
[mkcert](https://github.com/FiloSottile/mkcert) to generate a locally-trusted
certificate.

---

## Recommended nginx TLS Settings

```nginx
ssl_protocols   TLSv1.2 TLSv1.3;
ssl_ciphers     HIGH:!aNULL:!MD5;
```

- `TLSv1.2 TLSv1.3` — disables older, vulnerable protocol versions.
- `HIGH` — only strong cipher suites.
- `!aNULL` — excludes anonymous (unauthenticated) ciphers.
- `!MD5` — excludes ciphers using the broken MD5 MAC.

For a production nginx configuration, tools like
[Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
generate up-to-date, hardened settings.
