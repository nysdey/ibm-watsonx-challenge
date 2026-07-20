"""Explicit application dependency container."""

from dataclasses import dataclass

from bobbee.infrastructure.repository import JsonRepository
from bobbee.services.accounts import AccountService
from bobbee.services.jobs import JobManager
from bobbee.services.queries import AccountQueries, DashboardQueries


@dataclass(frozen=True)
class Services:
    repository: JsonRepository
    jobs: JobManager
    accounts: AccountService
    account_queries: AccountQueries
    dashboard_queries: DashboardQueries


def build_services(repository: JsonRepository, target_accounts: int) -> Services:
    return Services(
        repository=repository,
        jobs=JobManager(),
        accounts=AccountService(repository, target_accounts),
        account_queries=AccountQueries(repository),
        dashboard_queries=DashboardQueries(repository),
    )

