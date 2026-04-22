"""Browser-level smoke test for local test auth in the NETA demo."""

import importlib.util
import importlib
import os
import re
import socket
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

_HAS_PLAYWRIGHT = importlib.util.find_spec("playwright.sync_api") is not None

try:
    import uvicorn as _uvicorn_check  # noqa: F401
    _HAS_UVICORN = True
except ImportError:
    _HAS_UVICORN = False

_HAS_BROWSER = False
if _HAS_PLAYWRIGHT:
    try:
        sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright
        _pw = sync_playwright().start()
        _br = _pw.chromium.launch(headless=True)
        _br.close()
        _pw.stop()
        _HAS_BROWSER = True
    except Exception:
        pass

pytestmark = pytest.mark.skipif(
    not (_HAS_PLAYWRIGHT and _HAS_UVICORN and _HAS_BROWSER),
    reason="Playwright or browser binaries not installed",
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    import uvicorn
    from main import app

    original_enable = os.environ.get("ENABLE_LOCAL_TEST_AUTH")
    original_env = os.environ.get("APP_ENV")
    os.environ["ENABLE_LOCAL_TEST_AUTH"] = "true"
    os.environ["APP_ENV"] = os.environ.get("APP_ENV", "development") or "development"

    port = _free_port()
    startup_error = []
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    srv = uvicorn.Server(config)

    def _run():
        try:
            srv.run()
        except Exception as exc:
            startup_error.append(exc)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    import httpx
    for _ in range(30):
        if startup_error:
            raise startup_error[0]
        try:
            response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1.0)
            if response.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.2)
    else:
        pytest.fail("Local auth browser test server did not start in time")

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        srv.should_exit = True
        if original_enable is None:
            os.environ.pop("ENABLE_LOCAL_TEST_AUTH", None)
        else:
            os.environ["ENABLE_LOCAL_TEST_AUTH"] = original_enable
        if original_env is None:
            os.environ.pop("APP_ENV", None)
        else:
            os.environ["APP_ENV"] = original_env


@pytest.fixture(scope="module")
def browser():
    sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    try:
        yield browser
    finally:
        browser.close()
        pw.stop()


@pytest.fixture
def browser_context(browser):
    context = browser.new_context()
    try:
        yield context
    finally:
        context.close()


@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    try:
        yield page
    finally:
        page.close()


def _reset_test_user(server: str, email: str) -> None:
    import httpx

    response = httpx.post(
        f"{server}/api/v1/auth/test-reset",
        json={"email": email},
        timeout=10.0,
    )
    assert response.status_code == 200, response.text


def _sign_in_local_test_user(page, server: str, email: str) -> None:
    page.goto(f"{server}/demo/neta-tcc")
    page.wait_for_load_state("networkidle")
    page.locator("#auth-test-user").select_option(email)
    page.locator("#btn-test-sign-in").click()
    page.locator("#auth-status-banner").wait_for(timeout=10000)
    banner_text = page.locator("#auth-status-banner").inner_text().lower()
    assert email in banner_text
    assert "local test auth" in banner_text
    page.wait_for_function(
        "() => document.querySelector('#data-mode-label')?.textContent?.includes('LIVE')",
        timeout=10000,
    )
    page.locator("#btn-refresh-plans").click()
    page.wait_for_function(
        "() => !document.querySelector('#saved-plans-panel')?.classList.contains('hidden')",
        timeout=10000,
    )


def _load_default_preset(page) -> None:
    page.locator("#preset-select").select_option(index=1)
    page.locator("#btn-load-preset").click()
    page.locator("#settings-section").wait_for(state="visible", timeout=10000)


def _save_plan(page, plan_name: str) -> str:
    page.locator("#save-plan-name").fill(plan_name)
    page.locator("#btn-save-plan").click()
    page.wait_for_function(
        "() => document.querySelector('#save-plan-status')?.innerText?.includes('Saved as plan #')",
        timeout=10000,
    )
    status_text = page.locator("#save-plan-status").inner_text()
    match = re.search(r"Saved as plan #(.*)", status_text)
    assert match, status_text
    return match.group(1).strip()


def _authed_fetch(page, server: str, path: str, method: str = "GET", body=None):
    return page.evaluate(
        """async ({ server, path, method, body }) => {
            const headers = { 'Content-Type': 'application/json' };
            if (currentSession?.access_token) {
              headers.Authorization = `Bearer ${currentSession.access_token}`;
            }
            const response = await fetch(`${server}${path}`, {
              method,
              headers,
              body: body ? JSON.stringify(body) : undefined,
            });
            return {
              status: response.status,
              text: await response.text(),
            };
        }""",
        {"server": server, "path": path, "method": method, "body": body},
    )


def test_local_test_auth_sign_in(server, page):
    _sign_in_local_test_user(page, server, "neta-test-a@example.com")

    expect_text = page.locator("#auth-status-banner")
    assert "local test auth" in expect_text.inner_text().lower()
    assert "neta-test-a@example.com" in expect_text.inner_text().lower()
    assert not page.locator("#saved-plans-panel").evaluate("el => el.classList.contains('hidden')")


def test_local_test_auth_two_user_plan_isolation(server, browser):
    _reset_test_user(server, "neta-test-a@example.com")
    _reset_test_user(server, "neta-test-b@example.com")

    context_a = browser.new_context()
    context_b = browser.new_context()
    page_a = context_a.new_page()
    page_b = context_b.new_page()

    plan_a_name = f"AI isolation A {int(time.time())}"
    plan_b_name = f"AI isolation B {int(time.time())}"

    try:
        _sign_in_local_test_user(page_a, server, "neta-test-a@example.com")
        _load_default_preset(page_a)
        plan_a_id = _save_plan(page_a, plan_a_name)
        page_a.locator("#btn-refresh-plans").click()
        page_a.wait_for_timeout(500)
        assert plan_a_name in page_a.locator("#saved-plans-list").inner_text()

        _sign_in_local_test_user(page_b, server, "neta-test-b@example.com")
        page_b.locator("#btn-refresh-plans").click()
        page_b.wait_for_timeout(500)
        saved_plans_b = page_b.locator("#saved-plans-list").inner_text()
        assert plan_a_name not in saved_plans_b

        cross_load_b = _authed_fetch(page_b, server, f"/api/v1/neta/plans/{plan_a_id}")
        assert cross_load_b["status"] == 404, cross_load_b["text"]

        cross_result_b = _authed_fetch(
            page_b,
            server,
            f"/api/v1/neta/plans/{plan_a_id}/results",
            method="POST",
            body={
                "overall_pass": True,
                "tested_count": 1,
                "passed_count": 1,
                "failed_count": 0,
                "maint_mode": False,
                "elements": [
                    {
                        "element": "LTPU",
                        "test_current": 640.0,
                        "measured_current": 640.0,
                        "limit_low": 576.0,
                        "limit_high": 768.0,
                        "passed": True,
                        "deviation_pct": 0.0,
                    }
                ],
                "warnings": [],
            },
        )
        assert cross_result_b["status"] == 404, cross_result_b["text"]

        _load_default_preset(page_b)
        plan_b_id = _save_plan(page_b, plan_b_name)
        page_b.locator("#btn-refresh-plans").click()
        page_b.wait_for_timeout(500)
        assert plan_b_name in page_b.locator("#saved-plans-list").inner_text()

        page_a.locator("#btn-refresh-plans").click()
        page_a.wait_for_timeout(500)
        saved_plans_a = page_a.locator("#saved-plans-list").inner_text()
        assert plan_b_name not in saved_plans_a

        cross_load_a = _authed_fetch(page_a, server, f"/api/v1/neta/plans/{plan_b_id}")
        assert cross_load_a["status"] == 404, cross_load_a["text"]
    finally:
        page_a.close()
        page_b.close()
        context_a.close()
        context_b.close()
        _reset_test_user(server, "neta-test-a@example.com")
        _reset_test_user(server, "neta-test-b@example.com")
