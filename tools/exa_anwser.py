from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.exa_api import post


class ExaAnswerTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            query = (tool_parameters.get("query") or "").strip()
            if not query:
                raise ValueError("Query is required.")

            payload = {"query": query, "text": tool_parameters.get("text", False)}
            if model := tool_parameters.get("model"):
                payload["model"] = model

            result_data = post(self.runtime.credentials["exa_api_key"], "answer", payload)
            yield self.create_json_message(result_data)
            yield self.create_text_message(self._format_results_as_markdown(result_data, query))
        except Exception as error:
            yield self.create_json_message({"status": "error", "error": str(error)})
            yield self.create_text_message(f"Error: {error}")

    def _format_results_as_markdown(self, api_response: dict[str, Any], query: str) -> str:
        answer = api_response.get("answer", "No answer provided.")
        citations = api_response.get("citations", [])
        sections = ["## Exa Answer Results", f"**Query:** {query}", f"### Answer\n\n{answer}"]

        if citations:
            sections.append(f"### Sources ({len(citations)})")
            for i, citation in enumerate(citations, 1):
                url = citation.get("url", "")
                title = citation.get("title") or url
                lines = [f"**{i}. [{title}]({url})**"]
                if author := citation.get("author"):
                    lines.append(f"Author: {author}")
                if published_date := citation.get("publishedDate"):
                    lines.append(f"Published: {published_date}")
                if page_text := citation.get("text"):
                    excerpt = page_text[:300] + ("..." if len(page_text) > 300 else "")
                    lines.append(f"```\n{excerpt}\n```")
                sections.append("\n\n".join(lines))
        else:
            sections.append("No sources provided.")
        return "\n\n".join(sections) + "\n"
