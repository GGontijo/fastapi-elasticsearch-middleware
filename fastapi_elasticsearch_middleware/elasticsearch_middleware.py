import json
import logging
import time
import traceback
import uuid
from datetime import datetime, timezone

from elasticsearch import Elasticsearch
from fastapi import Request
from fastapi.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send


class LogLevelEnum:
    level_mapping = {2: "Info", 3: "Warning", 4: "Warning", 5: "Error"}


class ElasticsearchLoggerMiddleware:
    def __init__(self, app: ASGIApp, config: dict) -> None:
        """
        Initializes an Elasticsearch Logger Middleware for FastAPI.

        Args:
            app (ASGIApp): The FastAPI ASGI application.
            config (dict): Configuration settings for Elasticsearch logging.
                {
                    'url': str,          # Elasticsearch server URL
                    'user': str,         # Elasticsearch API user
                    'password': str      # Elasticsearch API password
                    'index': str,        # Elasticsearch index name
                    'environment': str,  # Environment identifier for logs
                    'limit': bool,       # Limit Elasticsearch payload array and string lenght
                    'debug': bool        # When True logs aren't sent to Elasticsearch
                }
        """
        elastic_config = config
        elastic_user = config.get("user")
        elastic_password = config.get("password")
        basic_auth = (
            (elastic_user, elastic_password)
            if elastic_user and elastic_password
            else None
        )
        self.elasticsearch_client = Elasticsearch(
            [elastic_config.get("url")], basic_auth=basic_auth
        )
        self.index = elastic_config.get("index")
        self.limit = elastic_config.get("limit", False)
        self.environment = elastic_config.get("environment", "Development")
        self.debug = elastic_config.get("debug", False)
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http" or self.debug:
            await self.app(scope, receive, send)
            return

        app_called = False

        try:
            request = Request(scope)

            async def intercept_send(response):
                nonlocal log_data
                try:
                    if response["type"] == "http.response.body" and not log_data.get(
                        "response"
                    ):  # Streaming response, we don't want to log this
                        return
                    if response["type"] == "http.response.body" and log_data.get(
                        "response"
                    ):  # Response part
                        # Finishes telemetry
                        end_time = time.time()
                        elapsed_time = end_time - start_time

                        log_data["elapsed_time"] = elapsed_time

                        if (
                            log_data["response"]["headers"].get("content-type")
                            == "application/json"
                        ):
                            response_body = json.loads(response.get("body"))
                            response_body = self.limit_array_length(response_body)

                            response_body = (
                                json.dumps(response_body, ensure_ascii=False)
                                if "body" in response.keys()
                                else None
                            )
                            log_data["response"]["body"] = response_body

                        elif (
                            log_data["response"]["headers"].get("content-type")
                            == "application/octet-stream"
                        ):
                            log_data["response"]["body"] = (
                                str(response.get("body"))
                                if "body" in response.keys()
                                else None
                            )

                        self.log_to_elasticsearch(log_data)
                        log_data["response"] = {}

                    if response["type"] == "http.response.start":  # Request part
                        response_headers_list = list(response.get("headers", []))
                        response_headers_list.append(
                            (b"request-id", log_data["request_id"].encode())
                        )
                        response["headers"] = response_headers_list

                        request_headers = (
                            dict(request.headers)
                            if "headers" in request.keys()
                            else None
                        )
                        request_query_parameters = (
                            dict(request.query_params)
                            if len(request.query_params._list) > 0
                            else None
                        )

                        response_headers = (
                            dict(Headers(raw=response.get("headers")))
                            if "headers" in response.keys()
                            else None
                        )

                        log_data["status_code"] = response["status"]
                        log_data["level"] = LogLevelEnum.level_mapping.get(
                            int(str(response["status"])[0])
                        )
                        log_data["request"]["headers"] = request_headers
                        log_data["request"]["query_parameters"] = (
                            request_query_parameters
                        )
                        log_data["response"]["headers"] = response_headers

                        _route = scope.get("route")
                        if _route is not None:
                            log_data["operation_id"] = _route.operation_id
                except Exception as exc:
                    logging.error(
                        "Failed to intercept response: %s", exc, exc_info=True
                    )
                finally:
                    await send(response)

            start_time = time.time()

            log_data = {
                "@timestamp": datetime.now(tz=timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),
                "environment": self.environment,
                "method": request.method,
                "path": request.url.path,
                "request_id": str(uuid.uuid4()),
                "request": {},
                "response": {},
            }

            # Starts telemetry
            start_time = time.time()

            async def intercept_receive():
                message = await receive()
                body = message.get("body", b"")

                try:
                    more_body = message.get("more_body", False)
                    while more_body:
                        message = await receive()
                        body += message.get("body", b"")
                        more_body = message.get("more_body", False)

                    message["body"] = body
                    request_body = ""
                    content_type = (
                        request.headers.get("content-type", "")
                        .partition(";")[0]
                        .strip()
                        .lower()
                    )

                    if len(body) > 0:
                        if content_type == "application/json":
                            request_body = json.loads(body.decode("utf-8"))
                            request_body = self.limit_string_length(request_body)
                            request_body = json.dumps(request_body, ensure_ascii=False)

                        elif content_type == "application/x-www-form-urlencoded":
                            request_body = body.decode("utf-8")
                            request_body = self.limit_string_length(request_body)

                    log_data["request"]["body"] = request_body
                except Exception as exc:
                    logging.error("Failed to intercept request: %s", exc, exc_info=True)
                    message["body"] = body

                return message

            app_called = True
            try:
                await self.app(scope, intercept_receive, intercept_send)
            except Exception as exc:
                try:
                    end_time = time.time()
                    log_data["elapsed_time"] = end_time - start_time

                    log_data["status_code"] = 500
                    log_data["level"] = "Error"
                    log_data["error"] = {
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    }

                    # Ensure request headers and query parameters are collected even if the request fails before the intercept_send
                    if "headers" not in log_data["request"]:
                        log_data["request"]["headers"] = dict(request.headers)
                        log_data["request"]["query_parameters"] = (
                            dict(request.query_params)
                            if len(request.query_params._list) > 0
                            else None
                        )

                    _route = scope.get("route")
                    if _route is not None:
                        log_data["operation_id"] = _route.operation_id

                    # Send the error log to Elasticsearch
                    self.log_to_elasticsearch(log_data)
                except Exception as logging_exc:
                    logging.error(
                        "Failed to log application exception: %s",
                        logging_exc,
                        exc_info=True,
                    )

                # Reraise the exception to be handled by the FastAPI application
                raise
        except Exception as exc:
            if app_called:
                raise

            logging.error("Elasticsearch middleware failed: %s", exc, exc_info=True)
            await self.app(scope, receive, send)

    def log_to_elasticsearch(self, log_data) -> None:
        try:
            self.elasticsearch_client.index(index=self.index, body=log_data)
        except Exception as e:
            logging.error("Failed to log to Elasticsearch: {str(e)}")

    def limit_string_length(self, data, max_lines=50):
        if not self.limit:
            return data
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.limit_string_length(value, max_lines)
        elif isinstance(data, list):
            for i in range(len(data)):
                data[i] = self.limit_string_length(data[i], max_lines)
        elif isinstance(data, str) and len(data.split("\n")) > max_lines:
            data_splitted = data.split("\n")[:max_lines]
            data_splitted.append(f" [...] value limited in {max_lines} lines")
            data = "\n".join(data_splitted)
        elif isinstance(data, str) and len(data.split("/")) > max_lines:  # Base64 files
            data_splitted = data.split("/")[:max_lines]
            data_splitted.append(f" [...] value limited in {max_lines} lines")
            data = "/".join(data_splitted)
        return data

    def limit_array_length(self, data, max_length=3):
        if not self.limit:
            return data
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.limit_array_length(value, max_length)
        elif isinstance(data, list) and len(data) > max_length:
            data = data[:max_length]
            data.append(f"[...] array limited in {max_length} objects")
        return data
