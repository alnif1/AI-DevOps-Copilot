
import re

from app.schemas import IncidentReport


RULES = [
    {
        "name": "database_connection",
        "pattern": r"connection refused|connection timeout|database connection failed",
        "severity": "high",
        "summary": "Possible database connectivity failure.",
        "causes": [
            "The database may be unavailable.",
            "Network configuration or connection limits may be responsible.",
        ],
        "recommendations": [
            "Check database health and availability.",
            "Verify hostname, port, DNS, and network rules.",
            "Inspect database connection pool usage.",
        ],
    },
    {
        "name": "out_of_memory",
        "pattern": r"out of memory|oomkilled|oom killer",
        "severity": "critical",
        "summary": "Possible memory exhaustion detected.",
        "causes": [
            "The application may be consuming excessive memory.",
        ],
        "recommendations": [
            "Inspect memory usage and container memory limits.",
            "Check application logs and container restart events.",
        ],
    },
    {
        "name": "http_server_error",
        "pattern": r"\b5\d\d\b|internal server error",
        "severity": "medium",
        "summary": "An HTTP server-side error was detected.",
        "causes": [
            "The application or an upstream dependency may be failing.",
        ],
        "recommendations": [
            "Inspect application exceptions and upstream health.",
            "Check recent deployments and error-rate metrics.",
        ],
    },
]


def analyze_logs(
    log_text: str,
    service_name: str = "unknown-service",
    environment: str = "local",
) -> IncidentReport:
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    matches = []

    for rule in RULES:
        matching_lines = [
            line for line in lines
            if re.search(rule["pattern"], line, re.IGNORECASE)
        ]
        if matching_lines:
            matches.append((rule, matching_lines))

    if not matches:
        return IncidentReport(
            service_name=service_name,
            environment=environment,
            severity="low",
            summary="No recognized error pattern was detected.",
            likely_causes=["The logs may contain an unfamiliar issue."],
            recommendations=[
                "Inspect logs around the incident timestamp.",
                "Check application health and monitoring metrics.",
            ],
            evidence=[],
            matched_patterns=[],
        )

    rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    primary_rule = max(
        matches,
        key=lambda item: rank[item[0]["severity"]],
    )[0]

    evidence = list(dict.fromkeys(
        line for _, found_lines in matches for line in found_lines
    ))

    return IncidentReport(
        service_name=service_name,
        environment=environment,
        severity=max(
            (rule["severity"] for rule, _ in matches),
            key=lambda value: rank[value],
        ),
        summary=primary_rule["summary"],
        likely_causes=list(dict.fromkeys(
            cause for rule, _ in matches for cause in rule["causes"]
        )),
        recommendations=list(dict.fromkeys(
            step for rule, _ in matches for step in rule["recommendations"]
        )),
        evidence=evidence[:20],
        matched_patterns=[rule["name"] for rule, _ in matches],
    )
