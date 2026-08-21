import httpx
from agents import function_tool

# Receives the target API URL.
# Adds /health.
# Sends an HTTP GET request.
# Captures the status code and response.
# Returns that evidence to the agent.
# If the request fails, returns the error type instead of crashing.


@function_tool
async def check_api_health(target_url: str) -> str:
    """Check the /health endpoint of a target API and return the evidence."""

    health_url = f"{target_url.rstrip('/')}/health"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(health_url)

        return (
            f"Health endpoint: {health_url}\n"
            f"HTTP status: {response.status_code}\n"
            f"Response body: {response.text[:500]}"
        )

    except httpx.RequestError as error:
        return (
            f"Health check failed for {health_url}. "
            f"Error: {error.__class__.__name__}"
        )


@function_tool
async def check_screening_api(target_url: str) -> str:
    """Build the URL for the read-only Screening endpoint."""

    screenings_url = f"{target_url.rstrip('/')}/screenings"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(screenings_url)
            data = response.json()
            is_list = isinstance(data, list)
            record_count = len(data) if is_list else "Not applicable"
            check_passed = response.status_code == 200 and is_list

        return (
            f"Screening endpoint: {screenings_url}\n"
            f"HTTP status: {response.status_code}\n"
            f"Response is a list: {is_list}\n"
            f"Record count: {record_count}"

        )
    

    except ValueError:
        return (
            f"Screening endpoint: {screenings_url}\n"
            f"HTTP status: {response.status_code}\n"
            "Response body is not valid JSON.\n"
            "Check passed: False"
        )

    except httpx.RequestError as error:
        return (
            f"Screening check failed for {screenings_url}.\n "
            f"Error: {error.__class__.__name__}"
        )
    
@function_tool
async def check_patient_api(target_url: str) -> str:
    """Build the URL for the read-only Patient endpoint."""

    patients_url = f"{target_url.rstrip('/')}/patients"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(patients_url)
            data = response.json()
            is_list = isinstance(data, list)
            record_count = len(data) if is_list else "Not applicable"
            check_passed = response.status_code == 200 and is_list

        return (
            f"Patient endpoint: {patients_url}\n"
            f"HTTP status: {response.status_code}"
        )

    except ValueError:
        return (
            f"Patient endpoint: {screenings_url}\n"
            f"HTTP status: {response.status_code}\n"
            "Response body is not valid JSON.\n"
            "Check passed: False"
        )

    except httpx.RequestError as error:
        return (
            f"Patient check failed for {screenings_url}.\n "
            f"Error: {error.__class__.__name__}"
        )