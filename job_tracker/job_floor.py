from job_tracker import JobTracker
from typing import List
import asyncio
from tracers import LogTracer
from agents import add_trace_processor
from dotenv import load_dotenv
import os

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))

# Job categories and their tracker names
categories = {
    "Business Analyst": "BA_Tracker",
    "Data Analyst": "DA_Tracker",
    "Software Engineer": "SE_Tracker",
    "Product Manager": "PM_Tracker",
}


def create_trackers() -> List[JobTracker]:
    trackers = []
    for category, name in categories.items():
        trackers.append(JobTracker(name, category))
    return trackers


async def run_every_n_minutes():
    add_trace_processor(LogTracer())
    trackers = create_trackers()
    
    print(f"🚀 Starting Job Tracking Floor with {len(trackers)} trackers")
    print(f"📊 Tracking categories: {list(categories.keys())}")
    print(f"⏰ Running every {RUN_EVERY_N_MINUTES} minutes\n")
    
    while True:
        print(f"🔄 Starting new tracking cycle...")
        await asyncio.gather(*[tracker.run() for tracker in trackers])
        print(f"✅ Tracking cycle completed. Sleeping for {RUN_EVERY_N_MINUTES} minutes...\n")
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 JOB TRACKING FLOOR - Real-time USA Job Market Tracker")
    print("=" * 60)
    asyncio.run(run_every_n_minutes())