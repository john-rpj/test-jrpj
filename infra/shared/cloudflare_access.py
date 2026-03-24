"""Shared Cloudflare Access resources used by all deployment targets."""
import pulumi
import pulumi_cloudflare as cloudflare


def create_cf_access(
    account_id: str,
    app_slug: str,
    app_domain: str,
    google_idp_id: str,
    allowed_domain: str | None = None,
    allowed_emails: list[str] | None = None,
    resource_prefix: str = "",
) -> dict:
    """Create Cloudflare Access application and policy for an app.

    Creates a wildcard Access policy covering the app domain and
    *.{app_slug-prefix} so all branch subdomains are protected.

    Args:
        account_id: Cloudflare account ID.
        app_slug: App identifier used in domain names.
        app_domain: Full app domain (e.g., my-app.rpjlabs.com).
        google_idp_id: Google IDP ID in Cloudflare Zero Trust.
        allowed_domain: Email domain to allow (e.g., example.com).
        allowed_emails: List of specific emails to allow.
        resource_prefix: Optional prefix for Pulumi resource names.

    Returns:
        Dict with 'access_app' and 'access_policy' Pulumi resources.
    """
    if not allowed_domain and not allowed_emails:
        raise ValueError(
            "At least one of allowed_domain or allowed_emails must be set."
        )

    prefix = f"{resource_prefix}-" if resource_prefix else ""
    # app_domain is the full domain (e.g., my-app.rpjlabs.com)
    # Derive the wildcard by splitting at first dot: *.my-app.rpjlabs.com
    parts = app_domain.split(".", 1)
    base_domain = parts[1] if len(parts) > 1 else app_domain
    wildcard_domain = f"*.{app_slug}.{base_domain}"

    # Build include rules
    include_rules = []
    if allowed_domain:
        include_rules.append(
            cloudflare.ZeroTrustAccessPolicyIncludeArgs(
                email_domain=cloudflare.ZeroTrustAccessPolicyIncludeEmailDomainArgs(
                    domain=allowed_domain,
                ),
            )
        )
    if allowed_emails:
        for email in allowed_emails:
            include_rules.append(
                cloudflare.ZeroTrustAccessPolicyIncludeArgs(
                    email=cloudflare.ZeroTrustAccessPolicyIncludeEmailArgs(
                        email=email,
                    ),
                )
            )

    access_policy = cloudflare.ZeroTrustAccessPolicy(
        f"{prefix}access-policy",
        account_id=account_id,
        name=f"Allow {app_slug} users",
        decision="allow",
        includes=include_rules,
    )

    access_app = cloudflare.ZeroTrustAccessApplication(
        f"{prefix}access-app",
        account_id=account_id,
        name=app_slug,
        domain=app_domain,
        self_hosted_domains=[app_domain, wildcard_domain],
        type="self_hosted",
        session_duration="24h",
        allowed_idps=[google_idp_id],
        auto_redirect_to_identity=True,
        policies=[
            cloudflare.ZeroTrustAccessApplicationPolicyArgs(
                id=access_policy.id,
                precedence=1,
            )
        ],
    )

    return {
        "access_app": access_app,
        "access_policy": access_policy,
    }
