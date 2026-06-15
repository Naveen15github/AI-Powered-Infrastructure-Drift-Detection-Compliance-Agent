"""Check GitHub Actions workflow runs to verify schedule is working."""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def check_workflow_runs():
    """Fetch recent workflow runs from GitHub API."""
    
    repo = "Naveen15github/terraform-agent-"
    workflow_file = "drift_detection.yml"
    
    # GitHub API endpoint
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/runs"
    
    try:
        response = requests.get(url, params={"per_page": 10})
        response.raise_for_status()
        data = response.json()
        
        print("=" * 80)
        print("GitHub Actions - Recent Workflow Runs")
        print("=" * 80)
        print(f"Repository: {repo}")
        print(f"Workflow: {workflow_file}")
        print(f"Schedule: Every 2 minutes (*/2 * * * *)")
        print("=" * 80)
        
        runs = data.get('workflow_runs', [])
        
        if not runs:
            print("\n❌ No workflow runs found yet.")
            print("   The first scheduled run may take 5-10 minutes to appear.")
            print("   Try manually triggering the workflow in the meantime.")
            return
        
        print(f"\n✅ Found {len(runs)} recent runs:\n")
        
        for i, run in enumerate(runs, 1):
            run_number = run.get('run_number')
            status = run.get('status')
            conclusion = run.get('conclusion', 'running')
            created_at = run.get('created_at', '')
            trigger = run.get('event', 'unknown')
            
            # Parse timestamp
            if created_at:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            else:
                time_str = "Unknown"
            
            # Status emoji
            if conclusion == 'success':
                emoji = "✅"
            elif conclusion == 'failure':
                emoji = "❌"
            elif status == 'in_progress':
                emoji = "⏳"
            else:
                emoji = "⚠️"
            
            print(f"{i}. Run #{run_number} {emoji}")
            print(f"   Trigger: {trigger}")
            print(f"   Status: {status} / {conclusion}")
            print(f"   Time: {time_str}")
            print()
        
        # Check if runs are scheduled
        scheduled_runs = [r for r in runs if r.get('event') == 'schedule']
        manual_runs = [r for r in runs if r.get('event') == 'workflow_dispatch']
        
        print("=" * 80)
        print(f"Scheduled runs: {len(scheduled_runs)}")
        print(f"Manual runs: {len(manual_runs)}")
        print("=" * 80)
        
        if len(scheduled_runs) == 0:
            print("\n⚠️  No scheduled runs detected yet.")
            print("   This is normal if you just pushed the change.")
            print("   Wait 2-5 minutes and run this script again.")
        elif len(scheduled_runs) >= 2:
            print("\n✅ Scheduled runs are working! You should see a new run every 2 minutes.")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching workflow runs: {e}")
        print("\nMake sure:")
        print("  1. Repository name is correct: Naveen15github/terraform-agent-")
        print("  2. Repository is public (or add a GitHub token for private repos)")

if __name__ == "__main__":
    check_workflow_runs()
