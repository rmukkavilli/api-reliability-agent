import asyncio  # Runs our async tool from this regular test function.
import json  # Converts the tool arguments into a JSON string.

import httpx  # Provides the HTTP client, response, and mock transport.
from agents.tool_context import ToolContext

from app import tools  # Imports your application’s tools.py module.


# pytest supplies monkeypatch so we can temporarily replace the HTTP client.
def test_screening_invalid_json(monkeypatch):

    # This function receives the request instead of sending it to a server.
    def fake_response(request):

        # Verify that the tool performs a read-only GET request.
        assert request.method == "GET"

        # Verify that the tool requests the correct endpoint.
        assert request.url.path == "/screenings"

        # Build the simulated HTTP response.
        return httpx.Response(
            status_code=200,  # The server reports HTTP success.
            text="this is not valid JSON",  # But the body violates our contract.
        )

    # Save the real client class before replacing it.
    original_client = httpx.AsyncClient

    # Accept the same keyword arguments your tool passes, such as timeout.
    def mock_client(**kwargs):

        # Create a real HTTPX client, but replace its network transport.
        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    # Temporarily make your tool use mock_client instead of AsyncClient.
    # pytest automatically restores the original client after this test.
    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)

    # Run the async tool and store the text it returns.
    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    # Context required by the SDK's tool interface.
    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    # Execute your tool with the mocked HTTP client.
    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    

    # Verify that the report identifies the correct Screening endpoint.
    assert "Screening endpoint: https://example.test/screenings" in result

    # Verify that the report preserves the HTTP status as evidence.
    assert "HTTP status: 200" in result

    # Verify that the report explains the actual problem.
    assert "Response body is not valid JSON." in result

    # Verify that invalid JSON causes a failed check despite HTTP 200.
    assert "Check passed: False" in result

def test_screening_timeout(monkeypatch):
    # This function receives the request instead of sending it to a server.
    def fake_response(request):

        # Verify that the tool performs a read-only GET request.
        assert request.method == "GET"

        # Verify that the tool requests the correct endpoint.
        assert request.url.path == "/screenings"
        raise httpx.ReadTimeout(
            "Simulated timeout",
            request=request,
        )
        
    # Save the real client class before replacing it.
    original_client = httpx.AsyncClient

    # Accept the same keyword arguments your tool passes, such as timeout.
    def mock_client(**kwargs):

        # Create a real HTTPX client, but replace its network transport.
        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    # Temporarily make your tool use mock_client instead of AsyncClient.
    # pytest automatically restores the original client after this test.
    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)

    # Run the async tool and store the text it returns.
    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    # Context required by the SDK's tool interface.
    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    # Execute your tool with the mocked HTTP client.
    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    # Verify that the report explains the actual problem.
    assert "Error: ReadTimeout" in result

    # Verify that invalid JSON causes a failed check despite HTTP 200.
    assert "Check passed: False" in result

def test_screening_503_then_200(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25
        
    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        if call_count == 1:
            returned_responses.append(503)
            return httpx.Response(status_code=503, json=[])
        returned_responses.append(200)
        return httpx.Response(status_code=200, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 2
    assert returned_responses == [503,200]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 200" in result
    assert "Response is a list: True" in result
    assert "Check passed: True" in result
    assert list_sleep == [1.25]

def test_screening_503_then_401(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25  # Make jitter predictable.
    
    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        if call_count == 1:
            returned_responses.append(503)
            return httpx.Response(status_code=503, json=[])
        returned_responses.append(401)
        return httpx.Response(status_code=401, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 2
    assert returned_responses == [503,401]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 401" in result
    assert "Response is a list: True" in result
    assert "Check passed: False" in result
    assert list_sleep == [1.25]


def test_screening_503_then_503(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []
    
    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25  # Make jitter predictable.
    
    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        
        returned_responses.append(503)
        return httpx.Response(status_code=503, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 3
    assert returned_responses == [503,503,503]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 503" in result
    assert "Response is a list: True" in result
    assert "Check passed: False" in result
    assert list_sleep == [1.25, 2.25]


def test_screening_401_without_wait(monkeypatch):
    def fake_response(request):

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        
        return httpx.Response(status_code=401, json=[])
    
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    # Verify that the report identifies the correct Screening endpoint.
    assert "Screening endpoint: https://example.test/screenings" in result

    # Verify that the report preserves the HTTP status as evidence.
    assert "HTTP status: 401" in result

    # Verify that the response body meets the list requirement.
    assert "Response is a list: True" in result

    # Verify that HTTP 503 still makes the check fail.
    assert "Check passed: False" in result


def test_screening_404(monkeypatch):
    def fake_response(request):

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        
        return httpx.Response(status_code=404, json=[])
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    # Verify that the report identifies the correct Screening endpoint.
    assert "Screening endpoint: https://example.test/screenings" in result

    # Verify that the report preserves the HTTP status as evidence.
    assert "HTTP status: 404" in result

    # Verify that the response body meets the list requirement.
    assert "Response is a list: True" in result

    # Verify that HTTP 503 still makes the check fail.
    assert "Check passed: False" in result


def test_screening_wrong_json_type(monkeypatch):
    def fake_response(request):
        assert request.method == "GET"

        assert request.url.path == "/screenings"
        
        return httpx.Response(status_code=200, json={"message": "unexpected"})
    original_client = httpx.AsyncClient
    
    def mock_client(**kwargs):
        return original_client(
            transport=httpx.MockTransport(fake_response), 
            **kwargs,
        )
    monkeypatch.setattr(tools.httpx, "AsyncClient",mock_client)

    arguments = json.dumps({"target_url":"https://example.test"})
    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )
    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    # Verify that the report identifies the correct Screening endpoint.
    assert "Screening endpoint: https://example.test/screenings" in result

    # Verify that the report preserves the HTTP status as evidence.
    assert "HTTP status: 200" in result

    # Verify that the response body meets the list requirement.
    assert "Response is a list: False" in result

    # Verify that HTTP 503 still makes the check fail.

    assert "Check passed: False" in result


def test_screening_connect_error(monkeypatch):
    def fake_response(request):
        assert request.method == "GET"

        assert request.url.path == "/screenings"
        
        # Simulate a failure to establish the connection.
        raise httpx.ConnectError(
            "Simulated connection failure",
            request=request,
        )

    original_client = httpx.AsyncClient
    
    def mock_client(**kwargs):
        return original_client(
            transport=httpx.MockTransport(fake_response), 
            **kwargs,
        )
    monkeypatch.setattr(tools.httpx, "AsyncClient",mock_client)

    arguments = json.dumps({"target_url":"https://example.test"})
    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )
    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )

    # Verify that the failed request identifies the correct endpoint.
    assert "Screening check failed for https://example.test/screenings." in result

    # Verify that the tool reports the connection error.
    assert "Error: ConnectError" in result

    # Verify that a connection failure makes the API check fail.
    assert "Check passed: False" in result


def test_screening_new_401(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25
        
    def fake_response(request):
        nonlocal call_count
        call_count +=1
        

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        returned_responses.append(401)
        return httpx.Response(status_code=401, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 1
    assert returned_responses == [401]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 401" in result
    assert "Response is a list: True" in result
    assert "Check passed: False" in result
    assert list_sleep == []
    
def test_screening_new_200(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25
        
    def fake_response(request):
        nonlocal call_count
        call_count +=1
        

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        returned_responses.append(200)
        return httpx.Response(status_code=200, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 1
    assert returned_responses == [200]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 200" in result
    assert "Response is a list: True" in result
    assert "Check passed: True" in result
    assert list_sleep == []
    

def test_screening_429_then_200(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25  # Make jitter predictable.
    
    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        if call_count == 1:
            returned_responses.append(429)
            return httpx.Response(headers={"Retry-After": "5"}, status_code=429, json=[])
        returned_responses.append(200)
        return httpx.Response(status_code=200, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 2
    assert returned_responses == [429,200]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 200" in result
    assert "Response is a list: True" in result
    assert "Check passed: True" in result
    assert list_sleep == [5.25]



def test_screening_429_no_header_then_200(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25  # Make jitter predictable.
    
    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        if call_count == 1:
            returned_responses.append(429)
            return httpx.Response(status_code=429, json=[])
        returned_responses.append(200)
        return httpx.Response(status_code=200, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 2
    assert returned_responses == [429,200]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 200" in result
    assert "Response is a list: True" in result
    assert "Check passed: True" in result
    assert list_sleep == [1.25]



def test_screening_429_to_429_with_no_header_then_200(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25  # Make jitter predictable.
    
    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        if call_count <= 2:
            returned_responses.append(429)
            return httpx.Response(status_code=429, json=[])
        returned_responses.append(200)
        return httpx.Response(status_code=200, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 3
    assert returned_responses == [429,429,200]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 200" in result
    assert "Response is a list: True" in result
    assert "Check passed: True" in result
    assert list_sleep == [1.25,2.25]


def test_screening_429_with_non_numeric_header_then_200(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_uniform(low,high):
        return 0.25  # Make jitter predictable.
    
    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/screenings"
        if call_count == 1:
            returned_responses.append(429)
            return httpx.Response(headers={"Retry-After": "-5"}, status_code=429, json=[])
        returned_responses.append(200)
        return httpx.Response(status_code=200, json=[])
        
        
    original_client = httpx.AsyncClient

    def mock_client(**kwargs):

        return original_client(
            # Route requests to fake_response instead of the internet.
            transport=httpx.MockTransport(fake_response),
            **kwargs,  # Preserve the original settings, including timeout.
        )

    monkeypatch.setattr(tools.httpx, "AsyncClient", mock_client)
    monkeypatch.setattr(tools.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(tools.random, "uniform", fake_uniform)

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_screening_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_screening_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 2
    assert returned_responses == [429,200]
    assert "Screening endpoint: https://example.test/screenings" in result
    assert "HTTP status: 200" in result
    assert "Response is a list: True" in result
    assert "Check passed: True" in result
    assert list_sleep == [1.25]









