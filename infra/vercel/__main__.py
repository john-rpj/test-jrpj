"""Vercel deployment target: project, domain, env vars, and CF Access."""
import pulumi
import pulumi_cloudflare as cloudflare
import pulumiverse_vercel as vercel

from shared.config import load_richmond_config
from shared.cloudflare_access import create_cf_access

# --- Config from richmond.yaml ---
cfg = load_richmond_config()
app_slug = cfg["app"]["slug"]
app_org = cfg["app"]["org"]
app_type = cfg["app"].get("type", "nextjs")
domain = cfg["domain"]

auth = cfg.get("auth", {})
allowed_domain = auth.get("allowed_domain")
allowed_emails = auth.get("allowed_emails")

vercel_cfg = cfg.get("targets", {}).get("vercel", {})
build_command = vercel_cfg.get("build_command")
node_version = vercel_cfg.get("node_version", "20.x")
vercel_env = vercel_cfg.get("env", {})
skip_branches = vercel_cfg.get("skip_branches")

global_env = cfg.get("env", {})

# --- Secrets from Pulumi config ---
secrets = pulumi.Config()
account_id = secrets.require("accountId")
zone_id = secrets.require("zoneId")
google_idp_id = secrets.require("googleIdpId")

# --- Framework detection ---
framework_map = {"nextjs": "nextjs", "flask": None}
framework = framework_map.get(app_type)

# ── Vercel: Project ───────────────────────────────────────────────────────
vercel_project = vercel.Project(
    "vercel-project",
    name=app_slug,
    framework=framework,
    git_repository=vercel.ProjectGitRepositoryArgs(
        type="github",
        repo=f"{app_org}/{app_slug}",
        production_branch="main",
    ),
    build_command=build_command,
    node_version=node_version,
)

# ── Vercel: Custom Domain ────────────────────────────────────────────────
vercel_domain = vercel.ProjectDomain(
    "vercel-domain",
    project_id=vercel_project.id,
    domain=domain,
)

# ── Vercel: Environment Variables ─────────────────────────────────────────
all_env = {**global_env, **vercel_env}
for key, value in all_env.items():
    vercel.ProjectEnvironmentVariable(
        f"env-{key.lower().replace('_', '-')}",
        project_id=vercel_project.id,
        key=key,
        value=value,
        targets=["production", "preview", "development"],
    )

# ── Cloudflare: DNS CNAME → Vercel ───────────────────────────────────────
cloudflare.DnsRecord(
    "dns-vercel",
    zone_id=zone_id,
    name=domain,
    type="CNAME",
    content="cname.vercel-dns.com",
    proxied=True,
    ttl=1,
)

# Wildcard CNAME for branch subdomains (e.g., *.myapp.rpjlabs.com)
# domain is e.g. "myapp.rpjlabs.com"; wildcard record covers branch deploys
base_domain = domain.split(".", 1)[1] if "." in domain else domain
cloudflare.DnsRecord(
    "dns-vercel-wildcard",
    zone_id=zone_id,
    name=f"*.{app_slug}.{base_domain}",
    type="CNAME",
    content="cname.vercel-dns.com",
    proxied=True,
    ttl=1,
)

# ── Cloudflare: Access ────────────────────────────────────────────────────
access_resources = create_cf_access(
    account_id=account_id,
    app_slug=app_slug,
    app_domain=domain,
    google_idp_id=google_idp_id,
    allowed_domain=allowed_domain,
    allowed_emails=allowed_emails,
)

# ── Outputs ───────────────────────────────────────────────────────────────
pulumi.export("vercel_project_id", vercel_project.id)
pulumi.export("app_url", f"https://{domain}")
pulumi.export("access_app_aud", access_resources["access_app"].aud)
