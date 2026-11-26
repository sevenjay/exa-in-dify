from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.exa_api import post


class ExaProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            api_key = credentials.get("exa_api_key")
            if not api_key:
                raise ValueError("Exa API key is required.")
            post(api_key, "search", {"query": "Exa", "type": "lite", "numResults": 1})
        except Exception as error:
            raise ToolProviderCredentialValidationError(str(error)) from error
