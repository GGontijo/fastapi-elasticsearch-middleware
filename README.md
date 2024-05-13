# Elasticsearch Logger Middleware for FastAPI

Elasticsearch Logger Middleware for FastAPI is designed to facilitate detailed and efficient logging directly to Elasticsearch servers from FastAPI applications. It streamlines the logging processes by capturing detailed HTTP requests data and automates telemetry to provide insights into application performance.

### Key Features

1. **Elasticsearch Integration:** Send logs directly to an Elasticsearch server.
2. **Flexible Configuration:** Configure to suit various environment needs.
3. **Automated Detailed Data Logging:** Automatically captures headers, query parameters, and the request body.
4. **Effortless Telemetry:** Automatically generates telemetry for monitoring request times.
5. **Enhanced Data Control:** Limit payload sizes for efficient Elasticsearch indexing.

### Installation

To install this middleware, ensure you have Python installed and then run:

```bash
pip install fastapi-elasticsearch-middleware
```

### Usage

Configure the middleware by creating a `config` dictionary in your FastAPI application as follows:

```python
config = {
    'url': 'http://localhost:9200',
    'user': 'elasticsearch_user',
    'password': 'password',
    'index': 'my_app_logs',
    'environment': 'development',
    'limit': True,
    'debug': False
}
```

**The `debug` parameter prevents sending logs to Elasticsearch.**

Integrate the middleware into your FastAPI application like this:

```python
from fastapi import FastAPI
from fastapi_elasticsearch_middleware.elasticsearch_middleware import ElasticsearchLoggerMiddleware

app = FastAPI()
app.add_middleware(ElasticsearchLoggerMiddleware, config=config)
```

### How It Works

The middleware captures each HTTP request, processes it, and sends log data to your Elasticsearch server based on the configured parameters. It includes detailed logs of request headers, body data, and response metrics.


## How to Contribute

We welcome contributions from the community and are pleased to have you join us. Here are some guidelines that will help you get started.

### Prerequisites

Before contributing, please ensure you have the following:
- A basic understanding of Python and FastAPI.
- A basic understanding of Middlewares.

### Setting Up Your Development Environment

1. **Fork the Repository**: Start by forking the repository to your GitHub account.
2. **Clone the Repository**: Clone your fork to your local machine.
   ```bash
   git clone https://github.com/GGontijo/fastapi-elasticsearch-middleware
   cd repository-name
   ```
3. **Install Dependencies**: Install the required dependencies.
   ```bash
   pip install -r requirements.txt
   ```

### Making Changes

1. **Create a New Branch**: Create a new branch for your feature or bug fix.
   ```bash
   git checkout -b awesome-feature
   ```
2. **Make Your Changes**: Implement your feature or fix a bug. Be sure to adhere to the coding standards and include comments where necessary.

### Submitting a Pull Request

1. **Commit Your Changes**: Once your tests pass, commit your changes.
   ```bash
   git commit -m 'Add some feature'
   ```
2. **Push to GitHub**: Push your changes to your fork on GitHub.
   ```bash
   git push origin awesome-feature
   ```
3. **Open a Pull Request**: Go to the original repository and click the *Compare & pull request* button. Then submit your pull request with a clear title and description.

### Code Review

Once your pull request is opened, it will be reviewed by the maintainers. Some changes may be requested. Please be patient and responsive. Once the pull request has been approved, it will be merged into the master branch.

Thank you for contributing!