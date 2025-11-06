from database import read_tracker_data
import json


async def read_tracker_resource(name: str) -> str:
    """
    Read tracker data as a resource for the agent
    """
    tracker = read_tracker_data(name)
    
    if not tracker:
        return json.dumps({
            "name": name,
            "total_tracked": 0,
            "last_run": "Never",
            "status": "New tracker - no data yet"
        })
    
    return json.dumps({
        "name": name,
        "category": tracker["category"],
        "total_tracked": tracker["total_tracked"],
        "last_run": tracker["last_run"],
        "data": tracker["data"]
    }, indent=2)


async def read_category_resource(category: str) -> str:
    """
    Read category information as a resource for the agent
    """
    category_descriptions = {
        "Business Analyst": """
Business Analysts bridge the gap between business needs and technical solutions.
Key skills: Requirements gathering, data analysis, stakeholder management, SQL, Excel, Tableau.
Typical salary range: $65K - $120K
Growth: High demand across all industries, especially finance and tech.
        """,
        "Data Analyst": """
Data Analysts collect, process, and analyze data to help organizations make decisions.
Key skills: SQL, Python/R, data visualization, statistics, Excel, business intelligence tools.
Typical salary range: $55K - $110K
Growth: Rapidly growing field with increasing demand across all sectors.
        """,
        "Software Engineer": """
Software Engineers design, develop, and maintain software applications and systems.
Key skills: Programming (Python, Java, JavaScript), algorithms, system design, Git, cloud platforms.
Typical salary range: $80K - $180K+
Growth: Extremely high demand, especially for full-stack and cloud engineers.
        """,
        "Product Manager": """
Product Managers own the product vision, strategy, and roadmap for products.
Key skills: Product strategy, user research, data analysis, roadmapping, cross-functional leadership.
Typical salary range: $90K - $170K+
Growth: High demand in tech companies and digital transformation initiatives.
        """
    }
    
    description = category_descriptions.get(category, f"Information about {category} roles.")
    
    return f"""
Category: {category}
{description}
    """.strip()