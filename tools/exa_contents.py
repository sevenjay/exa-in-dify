import json
import re
from collections.abc import Generator
from typing import Any
from urllib.parse import urlsplit

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.exa_api import max_age_hours, post


class ExaContentsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            urls = self._parse_urls(tool_parameters.get("urls"))
            payload: dict[str, Any] = {"urls": urls}
            age = max_age_hours(tool_parameters.get("max_age_hours"))
            if age is not None:
                payload["maxAgeHours"] = age

            if tool_parameters.get("include_highlights", True):
                limit = tool_parameters.get("highlights_max_characters")
                payload["highlights"] = {"maxCharacters": int(limit)} if limit is not None else True
            payload["text"] = tool_parameters.get("full_page_text", False)

            number_of_subpages = int(tool_parameters.get("number_of_subpages", 1))
            if number_of_subpages > 0:
                payload["subpages"] = number_of_subpages
            return_links = int(tool_parameters.get("return_links", 1))
            if return_links > 0:
                payload["extras"] = {"links": return_links}

            result_data = post(self.runtime.credentials["exa_api_key"], "contents", payload)
            yield self.create_json_message(result_data)
            yield self.create_text_message(self._format_results_as_markdown(result_data))
        except Exception as error:
            yield self.create_json_message({"status": "error", "error": str(error)})
            yield self.create_text_message(f"Error: {error}")

    def _parse_urls(self, value: str | list[str] | None) -> list[str]:
        if isinstance(value, str):
            value = value.strip()
            try:
                parsed = json.loads(value) if value.startswith("[") else None
            except json.JSONDecodeError:
                parsed = None
            value = parsed if isinstance(parsed, list) else re.split(r"[,，\s;]+", value.strip("[]"))
        if not isinstance(value, list):
            raise ValueError("Provide one or more URLs.")

        urls = []
        for entry in value:
            if not isinstance(entry, str):
                raise ValueError("Each URL must be a string.")
            url = entry.strip(" '\"")
            if not url:
                continue
            if "://" not in url:
                url = "https://" + url
            parsed_url = urlsplit(url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
                raise ValueError(f"Invalid HTTP or HTTPS URL: {url}")
            urls.append(url)
        if not 1 <= len(urls) <= 100:
            raise ValueError("Provide between 1 and 100 URLs.")
        return urls

    def _format_results_as_markdown(self, api_response: dict[str, Any]) -> str:
        sections = ["## Exa Content Extraction Results"]
        for result in api_response.get("results", []):
            url = result.get("url") or result.get("id", "")
            title = result.get("title") or url
            sections.append(f"### [{title}]({url})")
            if highlights := result.get("highlights"):
                sections.append("**Highlights**\n\n" + "\n".join(f"> {item}" for item in highlights))
            if page_text := result.get("text"):
                excerpt = page_text[:1000] + ("..." if len(page_text) > 1000 else "")
                sections.append(f"**Content**\n\n```\n{excerpt}\n```")
            if links := (result.get("extras") or {}).get("links"):
                sections.append("**Links**\n\n" + "\n".join(f"- [{link}]({link})" for link in links))
            if subpages := result.get("subpages"):
                sections.append("**Subpages**")
                for page in subpages:
                    page_url = page.get("url") or page.get("id", "")
                    sections.append(f"#### [{page.get('title') or page_url}]({page_url})")
                    if page_text := page.get("text"):
                        excerpt = page_text[:500] + ("..." if len(page_text) > 500 else "")
                        sections.append(f"```\n{excerpt}\n```")

        failed = []
        for status in api_response.get("statuses", []):
            if status.get("status") == "error":
                detail = status.get("error") or {}
                reason = detail.get("tag") or detail.get("httpStatusCode") or "Unknown error"
                failed.append(f"- {status.get('id', 'Unknown URL')} ({reason})")
        if failed:
            sections.append("### URLs that could not be fetched\n\n" + "\n".join(failed))
        if len(sections) == 1:
            sections.append("No content available.")
        return "\n\n".join(sections) + "\n"
