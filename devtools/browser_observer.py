from dataclasses import dataclass, field
from urllib.parse import urlsplit

from playwright.sync_api import (
    BrowserContext,
    ConsoleMessage,
    Page,
    Request,
    Response,
    Route,
)

from utils.offline import is_loopback


@dataclass
class BrowserObservation:
    external_requests: list[str] = field(default_factory=list)
    asset_failures: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    response_failures: list[str] = field(default_factory=list)

    def route(self, route: Route) -> None:
        if is_loopback(urlsplit(route.request.url).hostname):
            route.continue_()
        else:
            self.external_requests.append(route.request.url)
            route.abort()

    def request_failed(self, request: Request) -> None:
        if request.resource_type in {"stylesheet", "script", "image", "font"}:
            self.asset_failures.append(request.url)

    def response_received(self, response: Response) -> None:
        if response.status >= 400:
            self.response_failures.append(f"{response.status} {response.url}")

    def console_message(self, message: ConsoleMessage) -> None:
        if message.type == "error":
            self.page_errors.append(message.text)

    def observe(self, context: BrowserContext, page: Page) -> None:
        context.route("**/*", self.route)
        page.on("requestfailed", self.request_failed)
        page.on("response", self.response_received)
        page.on("pageerror", lambda error: self.page_errors.append(str(error)))
        page.on("console", self.console_message)

    def assert_clean(self) -> None:
        failures = (
            self.external_requests
            + self.asset_failures
            + self.page_errors
            + self.response_failures
        )
        if failures:
            raise AssertionError("Browser validation failed:\n" + "\n".join(failures))
