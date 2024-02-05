import json
import logging
import time
from fastapi import Request
from datetime import datetime, timezone
from fastapi.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send
from elasticsearch import Elasticsearch

class LogLevelEnum:
    level_mapping = {
        2: "Info",
        3: "Warning",
        4: "Warning",
        5: "Error"
    }

class ElasticsearchLoggerMiddleware:
    def __init__(self, app: ASGIApp, config: dict) -> None:
        """
        Initializes an Elasticsearch Logger Middleware for FastAPI.

        Args:
            app (ASGIApp): The FastAPI ASGI application.
            config (dict): Configuration settings for Elasticsearch logging.
                {
                    'url': str,          # Elasticsearch server URL
                    'index': str,        # Elasticsearch index name
                    'environment': str,  # Environment identifier for logs
                    'debug': bool        # When True logs aren't sent to Elasticsearch
                }
        """
        elastic_config = config
        self.elasticsearch_client = Elasticsearch([elastic_config.get('url')])
        self.index = elastic_config.get('index')
        self.environment = elastic_config.get('environment')
        self.debug = elastic_config.get('debug')
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get('type') == 'http' and not self.debug:
            request = Request(scope)
            
            request_data_received = await receive() 
            request_received_body = json.dumps(json.loads(request_data_received.get('body')), ensure_ascii=False) if len(request_data_received.get('body')) > 0 else None
            
            start_time = time.time()
            
            log_data = {
                "@timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "environment": self.environment, 
                "method": request.method,
                "path": request.url.path,
                "request": {},
                "response": {}
            }

            log_data["request"]["body"] = request_received_body

            async def intercept_send(response):
                nonlocal log_data
                if response['type'] == 'http.response.body' and "response" not in log_data.keys(): # Streaming response, we don't want to log this
                    await send(response)
                    return 
                if response['type'] == 'http.response.body' and "response" in log_data.keys(): # Response part
                    
                    end_time = time.time()
                    elapsed_time = end_time - start_time

                    log_data["elapsed_time"] = elapsed_time

                    if log_data["response"]["headers"].get('content-type') == 'application/json':
                        log_data["response"]["body"] = json.dumps(json.loads(response.get('body')), ensure_ascii=False) if 'body' in response.keys() else None
                        
                    elif log_data["response"]["headers"].get('content-type') == 'application/octet-stream':
                        log_data["response"]["body"] = str(response.get('body')) if 'body' in response.keys() else None

                    self.log_to_elasticsearch(log_data)

                if response['type'] == 'http.response.start': # Request part
                    

                    request_headers = dict(request.headers) if 'headers' in request.keys() else None
                    request_query_parameters = dict(request.query_params) if len(request.query_params._list) > 0 else None

                    response_headers = dict(Headers(raw=response.get('headers'))) if 'headers' in response.keys() else None

                    log_data["status_code"] = response['status']
                    log_data["level"] = LogLevelEnum.level_mapping.get(int(str(response['status'])[0]))
                    log_data["request"]["headers"] = request_headers
                    log_data["request"]["query_parameters"] = request_query_parameters
                    log_data["response"]["headers"] = response_headers

                await send(response)

            await self.app(scope, receive, intercept_send)
        else:
            await self.app(scope, receive, send)

    def log_to_elasticsearch(self, log_data):
        try:
            self.elasticsearch_client.index(index=self.index, body=log_data)
            log_data.clear()
        except Exception as e:
            logging.error(f"Failed to log to Elasticsearch: {str(e)}")
