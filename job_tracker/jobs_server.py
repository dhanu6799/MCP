from mcp.server.fastmcp import FastMCP
from jobs_api import get_todays_jobs, get_job_stats
from typing import List, Dict

mcp = FastMCP("jobs_server")


@mcp.tool()
async def search_jobs_today(category: str) -> List[Dict]:
    """
    Search for jobs posted today in a specific category.
    
    Args:
        category: Job category (e.g., "Business Analyst", "Data Analyst", "Software Engineer")
    
    Returns:
        List of job postings from today
    """
    use_mock = True  # Set to False when you have RapidAPI key configured
    return get_todays_jobs(category, use_mock=use_mock)


@mcp.tool()
async def get_category_stats(category: str) -> Dict:
    """
    Get statistics about jobs in a category for today.
    
    Args:
        category: Job category to analyze
    
    Returns:
        Dictionary with total_jobs, avg_salary, and top locations
    """
    return get_job_stats(category)


@mcp.tool()
async def search_jobs_by_location(category: str, city: str, state: str) -> List[Dict]:
    """
    Search for jobs in a specific location.
    
    Args:
        category: Job category
        city: City name (e.g., "New York")
        state: State code (e.g., "NY")
    
    Returns:
        List of jobs in that location
    """
    all_jobs = get_todays_jobs(category, use_mock=True)
    location_search = f"{city}, {state}"
    
    filtered_jobs = [
        job for job in all_jobs 
        if location_search.lower() in job.get("location", "").lower()
    ]
    
    return filtered_jobs


@mcp.tool()
async def get_salary_range(category: str) -> Dict:
    """
    Get salary range information for a job category.
    
    Args:
        category: Job category
    
    Returns:
        Dictionary with min, max, and average salaries
    """
    stats = get_job_stats(category)
    jobs = stats.get("jobs", [])
    
    salaries = [j["salary_max"] for j in jobs if j.get("salary_max")]
    
    if not salaries:
        return {"min": 0, "max": 0, "avg": 0, "count": 0}
    
    return {
        "min": min(salaries),
        "max": max(salaries),
        "avg": sum(salaries) // len(salaries),
        "count": len(salaries)
    }


if __name__ == "__main__":
    mcp.run(transport='stdio')