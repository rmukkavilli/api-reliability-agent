import httpx
from agents import function_tool
import asyncio  # Runs our async tool from this regular test function.
import random


# Receives the target API URL.
# Adds /health.
# Sends an HTTP GET request.
# Captures the status code and response.
# Returns that evidence to the agent.
# If the request fails, returns the error type instead of crashing.

RETRYABLE_STATUS_CODES = {429, 500, 503, 502, 504}
MAX_ATTEMPTS = 3
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
            for attempt in range(MAX_ATTEMPTS):
                response = await client.get(screenings_url)
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    break
                if attempt < MAX_ATTEMPTS - 1:
                    try:
                        retry_after = response.headers.get("Retry-After")
                        # await asyncio.sleep(2** attempt)
                        retry_after = 2** attempt if retry_after is None else int(retry_after)
                        if retry_after < 0:
                            retry_after = 2 ** attempt
                        
                    except ValueError:
                        retry_after = 2** attempt
                    await asyncio.sleep(retry_after +  random.uniform(0, 0.5))
                    continue    
                        
        
            data = response.json()
            is_list = isinstance(data, list)
            record_count = len(data) if is_list else "Not applicable"
            check_passed = response.status_code == 200 and is_list

        return (
            f"Screening endpoint: {screenings_url}\n"
            f"HTTP status: {response.status_code}\n"
            f"Response is a list: {is_list}\n"
            f"Record count: {record_count}\n"
            f"Check passed: {check_passed}\n"
        )

    

    except ValueError:
        return (
            f"Screening endpoint: {screenings_url}\n"
            f"HTTP status: {response.status_code}\n"    
            "Response body is not valid JSON.\n"
            f"Check passed: False\n"
        )

    except httpx.RequestError as error:
        return (
            f"Screening check failed for {screenings_url}.\n "
            f"Error: {error.__class__.__name__}"
            f"Check passed: False\n"
        )
    
@function_tool
async def check_patient_api(target_url: str) -> str:
    """Build the URL for the read-only Patient endpoint."""

    patients_url = f"{target_url.rstrip('/')}/patients"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
             for attempt in range(MAX_ATTEMPTS):
                response = await client.get(patients_url)
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    break
                
                if attempt < MAX_ATTEMPTS - 1:
                    # await asyncio.sleep(2 ** attempt)
                    await asyncio.sleep(1 +  random.uniform(0, 0.5))
                    continue
             data = response.json()
             is_list = isinstance(data, list)
             record_count = len(data) if is_list else "Not applicable"
             check_passed = response.status_code == 200 and is_list
             print(check_passed)

        return (
            f"Patient endpoint: {patients_url}\n"
            f"HTTP status: {response.status_code}\n"
            f"Response is a list: {is_list}\n"
            f"Record count: {record_count}\n"
            f"Check passed: {check_passed}\n"
        )

    except ValueError:
        return (
            f"Patient endpoint: {patients_url}\n"
            f"HTTP status: {response.status_code}\n"    
            "Response body is not valid JSON.\n"
            f"Check passed: False\n"
        )

    except httpx.RequestError as error:
        return (
            f"Patient check failed for {patients_url}.\n "
            f"Error: {error.__class__.__name__}"
            f"Check passed: False\n"
        )
    
