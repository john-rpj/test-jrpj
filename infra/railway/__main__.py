"""Railway deployment target: project, service, domain, and CF Access."""
import pulumi
import pulumi_cloudflare as cloudflare

from shared.config import load_richmond_config
from shared.cloudflare_access import create_cf_access
from railway_provider import RailwayProject, RailwayService

# --- Config from richmond.yaml ---
cfg = load_richmond_config()
app_slug = cfg["app"]["slug"]
app_org = cfg["app"]["org"]
domain = cfg["domain"]

auth = cfg.get("auth", {})
allowed_domain = auth.get("allowed_domain")
allowed_emails = auth.get("allowed_emails")

railway_cfg = cfg.get("targets", {}).get("railway", {})
region = railway_cfg.get("region", "us-west1")
railway_env = railway_cfg.get("env", {})
global_env = cfg.get("env", {})

# --- Secrets from Pulumi config ---
secrets = pulumi.Config()
account_id = secrets.require("accountId")
zone_id = secrets.require("zoneId")
google_idp_id = secrets.require("googleIdpId")
railway_api_token = secrets.require_secret("railwayApiToken")

# ── Railway: Project ──────────────────────────────────────────────────────
railway_project = RailwayProject(
    "railway-project",
    api_token=railway_api_token,
    project_name=app_slug,
)

# ── Railway: Service ──────────────────────────────────────────────────────
railway_service = RailwayService(
    "railway-service",
    api_token=railway_api_token,
    project_id=railway_project.project_id,
    service_name=app_slug,
    repo=f"{app_org}/{app_slug}",
    branch="main",
)

# ── Cloudflare: DNS CNAME → Railway ──────────────────────────────────────
cloudflare.DnsRecord(
    "dns-railway",
    zone_id=zone_id,
    name=domain,
    type="CNAME",
    content=railway_service.service_id.apply(lambda _: f"{app_slug}.up.railway.app"),
    proxied=True,
    ttl=1,
)

# Wildcard CNAME for branch subdomains
base_domain = domain.split(".", 1)[1] if "." in domain else domain
cloudflare.DnsRecord(
    "dns-railway-wildcard",
    zone_id=zone_id,
    name=f"*.{app_slug}.{base_domain}",
    type="CNAME",
    content=railway_service.service_id.apply(lambda _: f"{app_slug}.up.railway.app"),
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
pulumi.export("railway_project_id", railway_project.project_id)
pulumi.export("railway_service_id", railway_service.service_id)
pulumi.export("app_url", f"https://{domain}")
pulumi.export("access_app_aud", access_resources["access_app"].aud)
