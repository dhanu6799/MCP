import gradio as gr
import pandas as pd
from database import get_all_stats_today, read_logs, read_jobs, read_job_stats
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# Custom CSS
css = """
.positive-stat {
    color: #00dd00 !important;
    font-weight: bold;
}
.negative-stat {
    color: #dd0000 !important;
    font-weight: bold;
}
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 10px;
    color: white;
}
footer{display:none !important}
"""


def get_overview_stats():
    """Get overall statistics for the dashboard"""
    stats = get_all_stats_today()
    
    if not stats:
        return {
            "total_jobs": 0,
            "total_categories": 0,
            "avg_salary": 0,
            "top_location": "N/A"
        }
    
    total_jobs = sum(s["total_jobs"] for s in stats)
    avg_salary = sum(s["avg_salary"] for s in stats if s["avg_salary"] > 0) // len(stats) if stats else 0
    
    # Find most common location
    all_locations = {}
    for stat in stats:
        for loc in stat.get("locations", []):
            name = loc.get("name", "Unknown")
            all_locations[name] = all_locations.get(name, 0) + loc.get("count", 0)
    
    top_location = max(all_locations.items(), key=lambda x: x[1])[0] if all_locations else "N/A"
    
    return {
        "total_jobs": total_jobs,
        "total_categories": len(stats),
        "avg_salary": avg_salary,
        "top_location": top_location
    }


def create_jobs_chart():
    """Create bar chart of jobs by category"""
    stats = get_all_stats_today()
    
    if not stats:
        fig = go.Figure()
        fig.add_annotation(text="No data available yet", showarrow=False, font=dict(size=20))
        return fig
    
    categories = [s["category"] for s in stats]
    job_counts = [s["total_jobs"] for s in stats]
    
    fig = go.Figure(data=[
        go.Bar(x=categories, y=job_counts, marker_color='#667eea')
    ])
    
    fig.update_layout(
        title="Jobs Posted Today by Category",
        xaxis_title="Category",
        yaxis_title="Number of Jobs",
        template="plotly_dark"
    )
    
    return fig


def create_salary_chart():
    """Create bar chart of average salaries"""
    stats = get_all_stats_today()
    
    if not stats:
        fig = go.Figure()
        fig.add_annotation(text="No salary data available", showarrow=False, font=dict(size=20))
        return fig
    
    categories = [s["category"] for s in stats]
    salaries = [s["avg_salary"] for s in stats]
    
    fig = go.Figure(data=[
        go.Bar(x=categories, y=salaries, marker_color='#764ba2')
    ])
    
    fig.update_layout(
        title="Average Salary by Category",
        xaxis_title="Category",
        yaxis_title="Average Salary ($)",
        template="plotly_dark"
    )
    
    return fig


def create_location_map():
    """Create map of job locations"""
    today = datetime.now().date().strftime("%Y-%m-%d")
    
    # Aggregate all jobs from all categories
    all_jobs = []
    for category in ["Business Analyst", "Data Analyst", "Software Engineer", "Product Manager"]:
        jobs = read_jobs(category, today)
        if jobs:
            all_jobs.extend(jobs)
    
    if not all_jobs:
        fig = go.Figure()
        fig.add_annotation(text="No location data available", showarrow=False, font=dict(size=20))
        return fig
    
    # Count jobs by location
    location_data = {}
    for job in all_jobs:
        lat = job.get("latitude")
        lon = job.get("longitude")
        loc_name = job.get("location", "Unknown")
        
        if lat and lon:
            key = (lat, lon, loc_name)
            if key not in location_data:
                location_data[key] = {"lat": lat, "lon": lon, "location": loc_name, "count": 0}
            location_data[key]["count"] += 1
    
    if not location_data:
        fig = go.Figure()
        fig.add_annotation(text="No geographic data available", showarrow=False, font=dict(size=20))
        return fig
    
    df = pd.DataFrame(location_data.values())
    
    fig = px.scatter_geo(df,
                          lat='lat',
                          lon='lon',
                          size='count',
                          hover_name='location',
                          hover_data={'count': True, 'lat': False, 'lon': False},
                          scope='usa',
                          title='Job Openings Across USA')
    
    fig.update_layout(
        template="plotly_dark",
        geo=dict(bgcolor='rgba(0,0,0,0)')
    )
    
    return fig


def create_trend_chart(category):
    """Create trend chart for a category over past 7 days"""
    stats = read_job_stats(category, days=7)
    
    if not stats:
        fig = go.Figure()
        fig.add_annotation(text=f"No trend data for {category}", showarrow=False, font=dict(size=20))
        return fig
    
    dates = [s["date"] for s in reversed(stats)]
    job_counts = [s["total_jobs"] for s in reversed(stats)]
    
    fig = go.Figure(data=[
        go.Scatter(x=dates, y=job_counts, mode='lines+markers', line=dict(color='#667eea', width=3))
    ])
    
    fig.update_layout(
        title=f"{category} - 7 Day Trend",
        xaxis_title="Date",
        yaxis_title="Number of Jobs",
        template="plotly_dark"
    )
    
    return fig


def get_activity_logs(limit=50):
    """Get recent activity logs"""
    logs = read_logs(limit=limit)
    
    if not logs:
        return pd.DataFrame({"Message": ["No activity yet"]})
    
    df = pd.DataFrame(logs)
    df = df[['timestamp', 'tracker_name', 'log_type', 'message']]
    df.columns = ['Time', 'Tracker', 'Type', 'Message']
    
    return df


def refresh_dashboard():
    """Refresh all dashboard components"""
    stats = get_overview_stats()
    
    return (
        f"# 📊 {stats['total_jobs']:,}",
        f"# 💼 {stats['total_categories']}",
        f"# 💰 ${stats['avg_salary']:,}",
        f"# 📍 {stats['top_location']}",
        create_jobs_chart(),
        create_salary_chart(),
        create_location_map(),
        get_activity_logs()
    )


# Build Gradio Interface
with gr.Blocks(css=css, theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 🎯 USA Job Market Tracker - Real-Time MCP Dashboard
    ### Powered by Model Context Protocol (MCP) Agents
    """)
    
    with gr.Row():
        with gr.Column():
            total_jobs = gr.Markdown("# 📊 0")
            gr.Markdown("**Total Jobs Today**")
        with gr.Column():
            categories = gr.Markdown("# 💼 0")
            gr.Markdown("**Active Categories**")
        with gr.Column():
            avg_salary = gr.Markdown("# 💰 $0")
            gr.Markdown("**Avg Salary**")
        with gr.Column():
            top_location = gr.Markdown("# 📍 N/A")
            gr.Markdown("**Top Location**")
    
    with gr.Row():
        refresh_btn = gr.Button("🔄 Refresh Dashboard", variant="primary", scale=1)
    
    with gr.Tabs():
        with gr.Tab("📈 Overview"):
            with gr.Row():
                jobs_chart = gr.Plot(label="Jobs by Category")
                salary_chart = gr.Plot(label="Salaries by Category")
            
            location_map = gr.Plot(label="Job Locations Map")
        
        with gr.Tab("📋 Activity Log"):
            activity_log = gr.Dataframe(
                headers=["Time", "Tracker", "Type", "Message"],
                label="Recent Activity",
                interactive=False
            )
        
        with gr.Tab("📊 Trends"):
            category_select = gr.Dropdown(
                choices=["Business Analyst", "Data Analyst", "Software Engineer", "Product Manager"],
                value="Business Analyst",
                label="Select Category"
            )
            trend_chart = gr.Plot(label="7-Day Trend")
            
            category_select.change(
                fn=create_trend_chart,
                inputs=[category_select],
                outputs=[trend_chart]
            )
    
    # Refresh button handler
    refresh_btn.click(
        fn=refresh_dashboard,
        outputs=[total_jobs, categories, avg_salary, top_location, 
                jobs_chart, salary_chart, location_map, activity_log]
    )
    
    # Auto-refresh on load
    app.load(
        fn=refresh_dashboard,
        outputs=[total_jobs, categories, avg_salary, top_location, 
                jobs_chart, salary_chart, location_map, activity_log]
    )


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)