import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from database import write_jobs, read_jobs
from typing import List, Dict
import time

load_dotenv(override=True)

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"


def get_jobs_from_rapidapi(query: str, location: str = "United States", date_posted: str = "today") -> List[Dict]:
    """
    Fetch jobs from JSearch API on RapidAPI
    
    Args:
        query: Job title/category (e.g., "Business Analyst", "Data Analyst")
        location: Location to search (default: "United States")
        date_posted: Options: "all", "today", "3days", "week", "month"
    
    Returns:
        List of job dictionaries
    """
    url = "https://jsearch.p.rapidapi.com/search"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    querystring = {
        "query": f"{query} in {location}",
        "page": "1",
        "num_pages": "1",
        "date_posted": date_posted
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for job in data.get("data", []):
            jobs.append({
                "job_id": job.get("job_id"),
                "title": job.get("job_title"),
                "company": job.get("employer_name"),
                "location": job.get("job_city", "") + ", " + job.get("job_state", ""),
                "description": job.get("job_description", "")[:500],  # Truncate
                "posted_date": job.get("job_posted_at_datetime_utc"),
                "salary_min": job.get("job_min_salary"),
                "salary_max": job.get("job_max_salary"),
                "employment_type": job.get("job_employment_type"),
                "apply_link": job.get("job_apply_link"),
                "latitude": job.get("job_latitude"),
                "longitude": job.get("job_longitude"),
            })
        
        return jobs
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching jobs from RapidAPI: {e}")
        return []


def get_jobs_mock(query: str, location: str = "United States") -> List[Dict]:
    """
    Mock job data for testing without API calls
    """
    import random
    
    cities = [
        {"name": "New York, NY", "lat": 40.7128, "lon": -74.0060},
        {"name": "San Francisco, CA", "lat": 37.7749, "lon": -122.4194},
        {"name": "Chicago, IL", "lat": 41.8781, "lon": -87.6298},
        {"name": "Austin, TX", "lat": 30.2672, "lon": -97.7431},
        {"name": "Seattle, WA", "lat": 47.6062, "lon": -122.3321},
        {"name": "Boston, MA", "lat": 42.3601, "lon": -71.0589},
        {"name": "Denver, CO", "lat": 39.7392, "lon": -104.9903},
        {"name": "Atlanta, GA", "lat": 33.7490, "lon": -84.3880},
    ]
    
    companies = ["Google", "Amazon", "Microsoft", "Meta", "Apple", "Netflix", "Tesla", 
                 "Salesforce", "Adobe", "IBM", "Oracle", "Intel", "Cisco"]
    
    jobs = []
    num_jobs = random.randint(5, 15)
    
    for i in range(num_jobs):
        city = random.choice(cities)
        jobs.append({
            "job_id": f"mock_{query}_{i}_{int(time.time())}",
            "title": f"{query}",
            "company": random.choice(companies),
            "location": city["name"],
            "description": f"We are seeking a talented {query} to join our team...",
            "posted_date": datetime.now().isoformat(),
            "salary_min": random.randint(60000, 100000),
            "salary_max": random.randint(100000, 180000),
            "employment_type": random.choice(["FULLTIME", "CONTRACTOR", "PARTTIME"]),
            "apply_link": f"https://example.com/apply/{i}",
            "latitude": city["lat"],
            "longitude": city["lon"],
        })
    
    return jobs


def get_todays_jobs(category: str, use_mock: bool = False) -> List[Dict]:
    """
    Get today's jobs for a specific category
    """
    today = datetime.now().date().strftime("%Y-%m-%d")
    
    # Try to read from cache first
    cached_jobs = read_jobs(category, today)
    if cached_jobs:
        print(f"✓ Using cached jobs for {category} from {today}")
        # Still write stats even for cached data
        stats = get_job_stats(category)
        from database import write_job_stats
        write_job_stats(category, today, stats['total_jobs'], stats['avg_salary'], stats['locations'])
        return cached_jobs
    
    # Fetch new jobs
    print(f"→ Fetching new jobs for {category}...")
    
    if use_mock or not RAPIDAPI_KEY:
        jobs = get_jobs_mock(category)
        print(f"  Using MOCK data: {len(jobs)} jobs")
    else:
        jobs = get_jobs_from_rapidapi(category, date_posted="today")
        print(f"  From RapidAPI: {len(jobs)} jobs")
    
    # Cache the results
    if jobs:
        write_jobs(category, today, jobs)
        
        # IMPORTANT: Write stats to database for dashboard
        stats = get_job_stats(category)
        from database import write_job_stats
        write_job_stats(category, today, stats['total_jobs'], stats['avg_salary'], stats['locations'])
        print(f"  ✅ Saved stats: {stats['total_jobs']} jobs, avg ${stats['avg_salary']:,}")
    
    return jobs


def get_job_stats(category: str) -> Dict:
    """
    Get statistics for a job category
    """
    jobs = get_todays_jobs(category)
    
    if not jobs:
        return {
            "category": category,
            "total_jobs": 0,
            "avg_salary": 0,
            "locations": []
        }
    
    salaries = [j["salary_max"] for j in jobs if j.get("salary_max")]
    locations = {}
    
    for job in jobs:
        loc = job.get("location", "Unknown")
        locations[loc] = locations.get(loc, 0) + 1
    
    return {
        "category": category,
        "total_jobs": len(jobs),
        "avg_salary": sum(salaries) // len(salaries) if salaries else 0,
        "locations": [{"name": k, "count": v} for k, v in sorted(locations.items(), key=lambda x: x[1], reverse=True)][:10],
        "jobs": jobs
    }