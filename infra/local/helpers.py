import re


def sanitise_branch(branch: str) -> str:
    """Sanitise a git branch name for use in Docker names and subdomains.

    Replaces any character outside [a-zA-Z0-9-] with '-', then strips
    leading and trailing hyphens.
    """
    return re.sub(r"[^a-zA-Z0-9-]", "-", branch).strip("-")


def make_branch_domain(branch: str, app_slug: str, domain: str) -> str:
    """Return the domain for a branch deployment.

    Uses flat single-level subdomains to stay within *.{domain} Universal SSL coverage.

    main            -> {app_slug}.{domain}
    feature-theme   -> {app_slug}--feature-theme.{domain}
    """
    if branch == "main":
        return f"{app_slug}.{domain}"
    return f"{app_slug}--{sanitise_branch(branch)}.{domain}"
