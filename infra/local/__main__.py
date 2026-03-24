# templates/infra/local/__main__.py
import pulumi
import pulumi_cloudflare as cloudflare
import pulumi_command as command
import pulumi_docker as docker

from helpers import sanitise_branch, make_branch_domain
from shared.config import load_richmond_config
from shared.cloudflare_access import create_cf_access

# --- Config from richmond.yaml ---
cfg = load_richmond_config()
app_slug = cfg["app"]["slug"]
app_org = cfg["app"]["org"]
app_port = int(cfg["app"].get("port", 3000))
domain = cfg["domain"]

auth = cfg.get("auth", {})
allowed_domain = auth.get("allowed_domain")
allowed_emails = auth.get("allowed_emails")

local_cfg = cfg.get("targets", {}).get("local", {})
branches = local_cfg.get("branches", ["main"])
global_env = cfg.get("env", {})

# --- Secrets from Pulumi config (not in richmond.yaml) ---
secrets = pulumi.Config()
account_id = secrets.require("accountId")
zone_id = secrets.require("zoneId")
cf_team_name = secrets.require("cfTeamName")
google_idp_id = secrets.require("googleIdpId")

# Branch domains
branch_domains = [make_branch_domain(b, app_slug, domain) for b in branches]
app_domain = branch_domains[0]

# ── Cloudflare: Tunnel ────────────────────────────────────────────────────
tunnel = cloudflare.ZeroTrustTunnelCloudflared(
    "tunnel",
    account_id=account_id,
    name=f"{app_slug}-tunnel",
    tunnel_secret=secrets.require_secret("tunnelSecret"),
    config_src="cloudflare",
)

tunnel_config = cloudflare.ZeroTrustTunnelCloudflaredConfig(
    "tunnel-config",
    account_id=account_id,
    tunnel_id=tunnel.id,
    config=cloudflare.ZeroTrustTunnelCloudflaredConfigConfigArgs(
        ingresses=[
            cloudflare.ZeroTrustTunnelCloudflaredConfigConfigIngressArgs(
                hostname=bd,
                service="http://traefik:80",
            )
            for bd in branch_domains
        ] + [
            cloudflare.ZeroTrustTunnelCloudflaredConfigConfigIngressArgs(
                service="http_status:404",
            ),
        ],
    ),
)

# ── Cloudflare: DNS (one record per branch) ───────────────────────────────
tunnel_cname = tunnel.id.apply(lambda id: f"{id}.cfargotunnel.com")

dns_records: dict = {}
for bd in branch_domains:
    safe_key = bd.replace(".", "-")
    dns_records[safe_key] = cloudflare.DnsRecord(
        f"dns-{safe_key}",
        zone_id=zone_id,
        name=bd,
        type="CNAME",
        content=tunnel_cname,
        proxied=True,
        ttl=1,
    )

# ── Cloudflare: Access (shared module) ────────────────────────────────────
access = create_cf_access(
    account_id=account_id,
    app_slug=app_slug,
    app_domain=app_domain,
    google_idp_id=google_idp_id,
    allowed_domain=allowed_domain,
    allowed_emails=allowed_emails,
)
access_app = access["access_app"]
access_policy = access["access_policy"]

# ── Docker: cloudflared tunnel ────────────────────────────────────────────
tunnel_token = cloudflare.get_zero_trust_tunnel_cloudflared_token_output(
    account_id=account_id,
    tunnel_id=tunnel.id,
)

cloudflared_container = docker.Container(
    "cloudflared",
    name=f"{app_slug}-cloudflared",
    image="cloudflare/cloudflared:2025.4.0",
    command=["tunnel", "run"],
    envs=[tunnel_token.token.apply(lambda t: f"TUNNEL_TOKEN={t}")],
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name="traefik-web")],
    restart="unless-stopped",
    opts=pulumi.ResourceOptions(depends_on=[tunnel_config]),
)

# ── Docker: app containers per branch ─────────────────────────────────────
app_containers: dict = {}

for branch, branch_domain in zip(branches, branch_domains):
    sanitised_branch = sanitise_branch(branch)
    safe_name = f"{app_slug}-{sanitised_branch}"
    github_url = f"https://github.com/{app_org}/{app_slug}.git#{branch}"
    image_tag = f"{safe_name}:latest"

    build_cmd = command.local.Command(
        f"{safe_name}-build",
        create=f"docker build -t {image_tag} {github_url}",
        triggers=[branch],
    )

    container = docker.Container(
        safe_name,
        name=safe_name,
        image=image_tag,
        networks_advanced=[docker.ContainerNetworksAdvancedArgs(name="traefik-web")],
        labels=[
            docker.ContainerLabelArgs(label="traefik.enable", value="true"),
            docker.ContainerLabelArgs(
                label=f"traefik.http.routers.{safe_name}.rule",
                value=f"Host(`{branch_domain}`)",
            ),
            docker.ContainerLabelArgs(
                label=f"traefik.http.services.{safe_name}.loadbalancer.server.port",
                value=str(app_port),
            ),
        ],
        envs=[
            f"APP_NAME={app_slug}",
            f"BRANCH_NAME={branch}",
            f"CF_TEAM_NAME={cf_team_name}",
            "APP_ENV=production",
        ] + [f"{k}={v}" for k, v in global_env.items()],
        restart="unless-stopped",
        opts=pulumi.ResourceOptions(depends_on=[build_cmd]),
    )
    app_containers[safe_name] = container

# ── Outputs ───────────────────────────────────────────────────────────────
pulumi.export("app_url", f"https://{app_domain}")
pulumi.export("access_app_aud", access_app.aud)
