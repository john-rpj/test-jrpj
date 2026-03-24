"""Pulumi Dynamic Provider for Railway resources via GraphQL API."""
import requests
import pulumi
from pulumi.dynamic import Resource, ResourceProvider, CreateResult, UpdateResult

RAILWAY_API = "https://backboard.railway.com/graphql/v2"


class RailwayClient:
    """Thin wrapper around Railway's GraphQL API."""

    def __init__(self, api_token: str):
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def _query(self, query: str, variables: dict | None = None) -> dict:
        resp = requests.post(
            RAILWAY_API,
            json={"query": query, "variables": variables or {}},
            headers=self.headers,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise Exception(f"Railway API error: {data['errors']}")
        return data["data"]

    def create_project(self, name: str) -> dict:
        result = self._query(
            "mutation($input: ProjectCreateInput!) { projectCreate(input: $input) { id name } }",
            {"input": {"name": name}},
        )
        return result["projectCreate"]

    def delete_project(self, project_id: str) -> None:
        self._query(
            "mutation($id: String!) { projectDelete(id: $id) }",
            {"id": project_id},
        )

    def create_service(self, project_id: str, name: str, repo: str, branch: str = "main") -> dict:
        result = self._query(
            """mutation($input: ServiceCreateInput!) {
                serviceCreate(input: $input) { id name }
            }""",
            {"input": {"projectId": project_id, "name": name, "source": {"repo": repo}, "branch": branch}},
        )
        return result["serviceCreate"]

    def delete_service(self, service_id: str) -> None:
        self._query(
            "mutation($id: String!) { serviceDelete(id: $id) }",
            {"id": service_id},
        )

    def create_custom_domain(self, service_id: str, environment_id: str, domain: str) -> dict:
        result = self._query(
            """mutation($input: CustomDomainCreateInput!) {
                customDomainCreate(input: $input) { id }
            }""",
            {"input": {"serviceId": service_id, "environmentId": environment_id, "domain": domain}},
        )
        return result["customDomainCreate"]

    def set_variable(self, project_id: str, environment_id: str, service_id: str, name: str, value: str) -> None:
        self._query(
            """mutation($input: VariableUpsertInput!) {
                variableUpsert(input: $input)
            }""",
            {"input": {"projectId": project_id, "environmentId": environment_id, "serviceId": service_id, "name": name, "value": value}},
        )

    def get_environments(self, project_id: str) -> list[dict]:
        result = self._query(
            """query($projectId: String!) {
                environments(projectId: $projectId) { edges { node { id name } } }
            }""",
            {"projectId": project_id},
        )
        return [edge["node"] for edge in result["environments"]["edges"]]


class RailwayProjectProvider(ResourceProvider):
    def create(self, inputs: dict) -> CreateResult:
        client = RailwayClient(inputs["api_token"])
        project = client.create_project(inputs["name"])
        return CreateResult(id_=project["id"], outs={**inputs, "project_id": project["id"]})

    def delete(self, id_: str, props: dict) -> None:
        client = RailwayClient(props["api_token"])
        client.delete_project(id_)


class RailwayProject(Resource):
    project_id: pulumi.Output[str]

    def __init__(self, name: str, api_token: pulumi.Input[str], project_name: pulumi.Input[str], opts=None):
        super().__init__(
            RailwayProjectProvider(),
            name,
            {"api_token": api_token, "name": project_name, "project_id": ""},
            opts,
        )


class RailwayServiceProvider(ResourceProvider):
    def create(self, inputs: dict) -> CreateResult:
        client = RailwayClient(inputs["api_token"])
        service = client.create_service(
            inputs["project_id"], inputs["name"], inputs["repo"], inputs.get("branch", "main")
        )
        return CreateResult(id_=service["id"], outs={**inputs, "service_id": service["id"]})

    def delete(self, id_: str, props: dict) -> None:
        client = RailwayClient(props["api_token"])
        client.delete_service(id_)


class RailwayService(Resource):
    service_id: pulumi.Output[str]

    def __init__(self, name: str, api_token: pulumi.Input[str], project_id: pulumi.Input[str],
                 service_name: pulumi.Input[str], repo: pulumi.Input[str], branch: pulumi.Input[str] = "main", opts=None):
        super().__init__(
            RailwayServiceProvider(),
            name,
            {"api_token": api_token, "project_id": project_id, "name": service_name,
             "repo": repo, "branch": branch, "service_id": ""},
            opts,
        )
