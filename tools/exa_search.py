from collections.abc import Generator
from datetime import date, datetime
from typing import Any
from urllib.parse import urlsplit

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.exa_api import max_age_hours, post


def _published_date(value: str) -> str:
    try:
        return f"{date.fromisoformat(value)}T00:00:00Z"
    except ValueError:
        timestamp = datetime.fromisoformat(value)
        if timestamp.tzinfo is None:
            raise ValueError("Publication dates with a time must include a time zone.")
        return timestamp.isoformat()


class ExaSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            query = (tool_parameters.get("query") or "").strip()
            if not query:
                raise ValueError("Search query is required.")

            search_type = tool_parameters.get("search_type") or "auto"
            if search_type not in {"auto", "lite", "deep-lite", "deep"}:
                raise ValueError("Search type must be Auto, Lite, Deep Lite, or Deep.")
            age = max_age_hours(tool_parameters.get("max_age_hours"))
            if search_type == "lite" and age is not None:
                raise ValueError("Use Auto, Deep Lite, or Deep to set a maximum content age.")

            category = tool_parameters.get("category")
            payload: dict[str, Any] = {
                "query": query,
                "type": search_type,
                "numResults": int(tool_parameters.get("num_results", 10)),
            }
            if category:
                payload["category"] = category
            for name, field in (("include_domains", "includeDomains"), ("exclude_domains", "excludeDomains")):
                values = (tool_parameters.get(name) or "").split(",")
                domains = [value.strip() for value in values if value.strip()]
                if domains:
                    payload[field] = domains
            for name, field in (
                ("start_published_date", "startPublishedDate"),
                ("end_published_date", "endPublishedDate"),
            ):
                value = (tool_parameters.get(name) or "").strip()
                if value:
                    if category in {"company", "people"}:
                        raise ValueError("Company and People searches do not support publication date filters.")
                    payload[field] = _published_date(value)
            if category == "people" and "excludeDomains" in payload:
                raise ValueError("People searches do not support domain exclusions.")

            contents: dict[str, Any] = {}
            if tool_parameters.get("include_highlights", True):
                limit = tool_parameters.get("highlights_max_characters")
                contents["highlights"] = {"maxCharacters": int(limit)} if limit is not None else True
            if tool_parameters.get("include_text", False):
                contents["text"] = True
            if age is not None:
                contents["maxAgeHours"] = age
            if contents:
                payload["contents"] = contents

            result_data = post(self.runtime.credentials["exa_api_key"], "search", payload)
            results = result_data.get("results", [])
            urls = [result["url"] for result in results if result.get("url")]
            images = []
            for result in results:
                image = result.get("image")
                if isinstance(image, str) and image.startswith(("http://", "https://")):
                    images.append(image)

            yield self.create_json_message(result_data)
            yield self.create_text_message(self._format_results_as_markdown(results, query))
            yield self.create_variable_message("urls", urls)
            yield self.create_variable_message("images", images)
        except Exception as error:
            yield self.create_json_message({"status": "error", "error": str(error)})
            yield self.create_text_message(f"Error: {error}")

    def _format_results_as_markdown(self, results: list[dict[str, Any]], query: str) -> str:
        markdown = f"## Exa Search Results\n\n**Query:** {query}\n\n**Total Results:** {len(results)}\n\n"
        if not results:
            return markdown + "No results found.\n"

        for i, result in enumerate(results, 1):
            title = result.get("title") or "No title"
            url = result.get("url", "")
            domain = result.get("domain") or urlsplit(url).hostname or "Unknown source"
            markdown += f"### {i}. [{title}]({url})\n\n"
            if image := result.get("image"):
                markdown += f"![Image from {domain}]({image})\n\n"
            markdown += f"**Source:** {domain}\n"
            if published_date := result.get("publishedDate"):
                markdown += f"**Published:** {published_date}\n"
            if author := result.get("author"):
                markdown += f"**Author:** {author}\n"
            markdown += "\n"

            if highlights := result.get("highlights"):
                markdown += "**Highlights:**\n\n"
                markdown += "".join(f"> {highlight}\n" for highlight in highlights) + "\n"
            if page_text := result.get("text"):
                excerpt = page_text[:500] + ("..." if len(page_text) > 500 else "")
                markdown += f"**Content Excerpt:**\n\n```\n{excerpt}\n```\n\n"
            markdown += "---\n\n"
        return markdown
