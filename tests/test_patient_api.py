import asyncio  # Runs our async tool from this regular test function.
import json  # Converts the tool arguments into a JSON string.

import httpx  # Provides the HTTP client, response, and mock transport.
from agents.tool_context import ToolContext

from app import tools  # Imports your application’s tools.py module.


# pytest supplies monkeypatch so we can temporarily replace the HTTP client.
def test_patient_invalid_json(monkeypatch):

    # This function receives the request instead of sending it to a server.
    def fake_response(request):

        # Verify that the tool performs a read-only GET request.
        assert request.method == "GET"

        # Verify that the tool requests the correct endpoint.
        assert request.url.path == "/patients"

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
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    # Execute your tool with the mocked HTTP client.
    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )
    

    # Verify that the report identifies the correct patient endpoint.
    assert "Patient endpoint: https://example.test/patients" in result

    # Verify that the report preserves the HTTP status as evidence.
    assert "HTTP status: 200" in result

    # Verify that the report explains the actual problem.
    assert "Response body is not valid JSON." in result

    # Verify that invalid JSON causes a failed check despite HTTP 200.
    assert "Check passed: False" in result

def test_patient_timeout(monkeypatch):
    # This function receives the request instead of sending it to a server.
    def fake_response(request):

        # Verify that the tool performs a read-only GET request.
        assert request.method == "GET"

        # Verify that the tool requests the correct endpoint.
        assert request.url.path == "/patients"
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
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    # Execute your tool with the mocked HTTP client.
    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )
    
    # Verify that the report explains the actual problem.
    assert "Error: ReadTimeout" in result

    # Verify that invalid JSON causes a failed check despite HTTP 200.
    assert "Check passed: False" in result

def test_patient_503_then_200(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)

    def fake_response(request):
        nonlocal call_count
        call_count +=1
        assert request.method == "GET"

        assert request.url.path == "/patients"
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

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 2
    assert returned_responses == [503,200]
    assert "Patient endpoint: https://example.test/patients" in result
    assert "HTTP status: 200" in result
    assert "Response is a list: True" in result
    assert "Check passed: True" in result
    assert list_sleep == [1]

def test_patient_503_then_401(monkeypatch):
    call_count = 0
    returned_responses = []
    list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)
    
    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/patients"
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
    

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 2
    assert returned_responses == [503,401]
    assert "Patient endpoint: https://example.test/patients" in result
    assert "HTTP status: 401" in result
    assert "Response is a list: True" in result
    assert "Check passed: False" in result
    assert list_sleep == [1]


def test_patient_503_then_503(monkeypatch):
    call_count = 0
    returned_responses = []
     list_sleep = []

    async def fake_sleep(seconds):
        list_sleep.append(seconds)

    def fake_response(request):
        nonlocal call_count
        call_count +=1

        assert request.method == "GET"

        assert request.url.path == "/patients"
        
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

    arguments = json.dumps({
    "target_url": "https://example.test"
    })

    context = ToolContext(
        context=None,
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )
    
    assert call_count == 3
    assert returned_responses == [503,503,503]
    assert "Patient endpoint: https://example.test/patients" in result
    assert "HTTP status: 503" in result
    assert "Response is a list: True" in result
    assert "Check passed: False" in result
    assert list_sleep == [1,2]

def test_patient_401(monkeypatch):
    def fake_response(request):

        assert request.method == "GET"

        assert request.url.path == "/patients"
        
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
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )
    
    # Verify that the report identifies the correct patient endpoint.
    assert "Patient endpoint: https://example.test/patients" in result

    # Verify that the report preserves the HTTP status as evidence.
    assert "HTTP status: 401" in result

    # Verify that the response body meets the list requirement.
    assert "Response is a list: True" in result

    # Verify that HTTP 503 still makes the check fail.
    assert "Check passed: False" in result


def test_patient_404(monkeypatch):
    def fake_response(request):

        assert request.method == "GET"

        assert request.url.path == "/patients"
        
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
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )

    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )
    
    # Verify that the report identifies the correct patient endpoint.
    assert "Patient endpoint: https://example.test/patients" in result

    # Verify that the report preserves the HTTP status as evidence.
    assert "HTTP status: 404" in result

    # Verify that the response body meets the list requirement.
    assert "Response is a list: True" in result

    # Verify that HTTP 503 still makes the check fail.
    assert "Check passed: False" in result


def test_patient_wrong_json_type(monkeypatch):
    def fake_response(request):
        assert request.method == "GET"

        assert request.url.path == "/patients"
        
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
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )
    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )
    
    # Verify that the report identifies the correct patient endpoint.
    assert "Patient endpoint: https://example.test/patients" in result

    # Verify that the report preserves the HTTP status as evidence.
    assert "HTTP status: 200" in result

    # Verify that the response body meets the list requirement.
    assert "Response is a list: False" in result

    # Verify that HTTP 503 still makes the check fail.

    assert "Check passed: False" in result


def test_patient_connect_error(monkeypatch):
    def fake_response(request):
        assert request.method == "GET"

        assert request.url.path == "/patients"
        
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
        tool_name="check_patient_api",
        tool_call_id="test-call-1",
        tool_arguments=arguments,
    )
    result = asyncio.run(
        tools.check_patient_api.on_invoke_tool(context, arguments)
    )

    # Verify that the failed request identifies the correct endpoint.
    assert "Patient check failed for https://example.test/patients." in result

    # Verify that the tool reports the connection error.
    assert "Error: ConnectError" in result

    # Verify that a connection failure makes the API check fail.
    assert "Check passed: False" in result

    






