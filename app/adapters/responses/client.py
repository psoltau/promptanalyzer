import json
from typing import Any, Dict, List, Optional

import httpx

from app.application.ports import ModelGatewayError, ModelRequest, ModelResult

RESPONSES_URL = "https://api.openai.com/v1/responses"
_TIMEOUT_SECONDS = 600.0


class OpenAiResponsesGateway:
    def __init__(self, client: Optional[httpx.Client] = None) -> None:
        self._client = client or httpx.Client(timeout=_TIMEOUT_SECONDS)

    def run(self, request: ModelRequest) -> ModelResult:
        payload = _build_payload(request)
        response = self._send(payload, request.api_key)
        return _parse_response(payload, response)

    def _send(self, payload: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        try:
            http_response = self._client.post(
                RESPONSES_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
        except httpx.HTTPError as exc:
            raise ModelGatewayError(str(exc), json.dumps(payload)) from exc
        return _als_json_oder_fehler(http_response, payload)


def _als_json_oder_fehler(http_response: httpx.Response, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = http_response.json()
    if http_response.status_code >= 400:
        raise ModelGatewayError(_fehlermeldung(body), json.dumps(payload))
    if body.get("status") == "failed":
        raise ModelGatewayError(_fehlermeldung(body), json.dumps(payload))
    return body


def _fehlermeldung(body: Dict[str, Any]) -> str:
    fehler = body.get("error") or {}
    return fehler.get("message", "Unbekannter Fehler der Responses API")


def _build_payload(request: ModelRequest) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"model": request.model, "input": request.user_prompt}
    if request.system_prompt:
        payload["instructions"] = request.system_prompt
    if request.max_output_tokens is not None:
        payload["max_output_tokens"] = request.max_output_tokens
    if request.reasoning_effort:
        payload["reasoning"] = {"effort": request.reasoning_effort}
    _mit_werkzeugen(payload, request)
    return payload


def _mit_werkzeugen(payload: Dict[str, Any], request: ModelRequest) -> None:
    tools: List[Dict[str, Any]] = json.loads(request.tools_json) if request.tools_json else []
    if request.web_suche:
        web_search: Dict[str, Any] = {"type": "web_search"}
        if request.search_context_size:
            web_search["search_context_size"] = request.search_context_size
        tools.append(web_search)
    if tools:
        payload["tools"] = tools


def _parse_response(payload: Dict[str, Any], response: Dict[str, Any]) -> ModelResult:
    incomplete_grund = None
    if response.get("status") == "incomplete":
        incomplete_grund = (response.get("incomplete_details") or {}).get("reason")
    usage = response.get("usage") or {}
    return ModelResult(
        incomplete_grund=incomplete_grund,
        input_tokens=usage.get("input_tokens", 0),
        cached_input_tokens=(usage.get("input_tokens_details") or {}).get("cached_tokens", 0),
        reasoning_tokens=(usage.get("output_tokens_details") or {}).get("reasoning_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        web_search_calls=_zaehle_web_suchen(response),
        antwort_text=_antworttext(response),
        request_json=json.dumps(payload),
        response_json=json.dumps(response),
    )


def _zaehle_web_suchen(response: Dict[str, Any]) -> int:
    output = response.get("output") or []
    return sum(1 for item in output if item.get("type") == "web_search_call")


def _antworttext(response: Dict[str, Any]) -> str:
    output = response.get("output") or []
    teile = []
    for item in output:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                teile.append(content.get("text", ""))
    return "".join(teile)
