export const DEPLOY_PROBE_URL = "https://kickstart-site.polarcoordinates.workers.dev/healthz";

interface ProbeOptions {
  token: string;
  version: string;
  fetcher?: typeof fetch;
  sleep?: (milliseconds: number) => Promise<void>;
  log?: (message: string) => void;
}

export async function verifyDeployment({ token, version, fetcher = fetch,
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)), log = console.log,
}: ProbeOptions): Promise<void> {
  if (!/^[a-f0-9]{64}$/.test(token) || !/^\d+\.\d+\.\d+$/.test(version)) {
    throw new Error("A deployment token and stable release version are required");
  }
  for (let attempt = 1; attempt <= 5; attempt++) {
    let failure = "request failed or health response was not JSON";
    try {
      const response = await fetcher(DEPLOY_PROBE_URL, {
        headers: { authorization: `Bearer ${token}` },
        redirect: "error",
        signal: AbortSignal.timeout(10_000),
      });
      failure = `HTTP ${response.status}`;
      if (response.ok) {
        const body: unknown = await response.json();
        if (body !== null && typeof body === "object" &&
            "status" in body && body.status === "ok" &&
            "service" in body && body.service === "kickstart-site" &&
            "version" in body && body.version === version) {
          log(`Deployed Worker serves v${version}. Custom-domain verification remains manual.`);
          return;
        }
        failure = "health metadata does not match this release";
      }
    } catch {
      // Never log response bodies or exceptions that could contain the bearer token.
    }
    log(`Deployment probe ${attempt}/5: ${failure}`);
    if (attempt < 5) await sleep(15_000);
  }
  throw new Error("Deployed Worker verification failed after five attempts");
}

if (import.meta.main) {
  await verifyDeployment({
    token: process.env.DEPLOY_PROBE_TOKEN ?? "",
    version: (process.env.GITHUB_REF_NAME ?? "").replace(/^v/, ""),
  });
}
