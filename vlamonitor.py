import os
import json
import requests
import time
import hashlib
import argparse

def get_args():
    parser = argparse.ArgumentParser(description="VLA Evaluation Monitor & Feishu Notifier")
    parser.add_argument("--dir", type=str, required=True, help="Path to the Libero evaluation results directory")
    parser.add_argument("--webhook", type=str, required=True, help="Feishu/Lark Webhook URL")
    parser.add_argument("--ollama_api", type=str, default="http://localhost:11434/api/generate", help="Local Ollama API endpoint")
    parser.add_argument("--ollama_model", type=str, default="qwen2.5:3b", help="Ollama model name for summary")
    parser.add_argument("--total_tasks", type=int, default=10, help="Total expected tasks (e.g., 10 for Libero-10)")
    parser.add_argument("--episodes_per_task", type=int, default=50, help="Number of episodes/demos per task")
    parser.add_argument("--interval", type=int, default=300, help="Monitoring interval in seconds")
    return parser.parse_args()

def get_dir_fingerprint(root_path):
    """Calculate an MD5 fingerprint based on directory contents and modify times."""
    if not os.path.exists(root_path): 
        return ""
    fingerprint_str = ""
    try:
        folders = sorted([d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))])
        for folder in folders:
            json_path = os.path.join(root_path, folder, "results.json")
            if os.path.exists(json_path):
                fingerprint_str += f"{folder}_{os.path.getmtime(json_path)}"
    except Exception as e:
        print(f"Fingerprint calculation error: {e}")
    return hashlib.md5(fingerprint_str.encode()).hexdigest()

def shorten_task_name(name):
    """Shorten task name for better display on Feishu cards."""
    useless_words = {'put', 'the', 'in', 'on', 'of', 'and', 'both', 'it', 'to', 'left', 'right'}
    parts = [p for p in name.split('_') if p and p not in useless_words]
    short_name = "_".join(parts[-3:])
    if len(short_name) > 20:
        return short_name[-20:]
    return short_name

def parse_libero_results(root_path, expected_per_task, total_expected_tasks):
    """Parse results.json from all task folders."""
    all_tasks = []
    if not os.path.exists(root_path): return None

    folders = sorted([d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))])
    for folder in folders:
        json_path = os.path.join(root_path, folder, "results.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    s = data.get("success", 0)
                    f_count = data.get("failure", 0)
                    current_total = s + f_count
                    
                    rate_val = (s / current_total * 100) if current_total > 0 else 0
                    progress = (current_total / expected_per_task * 100)
                    
                    display_name = folder
                    l10_content = data.get("libero_10", {})
                    for key in l10_content.keys():
                        if key not in ["success", "failure"]:
                            display_name = key
                            break
                    
                    all_tasks.append({
                        "name": shorten_task_name(display_name), 
                        "s": s, 
                        "f": f_count, 
                        "rate": rate_val,
                        "progress": progress
                    })
            except Exception as e: 
                print(f"Error parsing {json_path}: {e}")
                continue

    if not all_tasks: return None
    
    total_s = sum(t['s'] for t in all_tasks)
    total_f = sum(t['f'] for t in all_tasks)
    total_tested = total_s + total_f
    
    overall_rate = (total_s / total_tested * 100) if total_tested > 0 else 0
    total_expected_episodes = total_expected_tasks * expected_per_task
    demo_completion = (total_tested / total_expected_episodes * 100) if total_expected_episodes > 0 else 0

    return {
        "total_s": total_s, 
        "total_f": total_f, 
        "total_tested": total_tested,
        "overall_rate": f"{overall_rate:.2f}%", 
        "demo_completion": f"{demo_completion:.1f}%",
        "total_expected": total_expected_episodes,
        "tasks": all_tasks
    }

def get_ai_report(stats, api_url, model_name):
    """Generate markdown report and get AI summary from Ollama."""
    def make_bar(rate):
        filled = int(rate / 10)
        return "█" * filled + "░" * (10 - filled)
        
    def get_status_dot(rate):
        if rate == 100: return "🟢"
        if rate >= 70: return "🟡"
        return "🔴"

    list_rows = []
    for t in stats['tasks']:
        dot = get_status_dot(t['rate'])
        bar = make_bar(t['progress']) 
        row = f"{dot} **{t['rate']:.0f}%** `{bar}` ({t['s']}/{t['s']+t['f']}) ➔ `{t['name']}`"
        list_rows.append(row)
        
    formatted_list = "\n".join(list_rows)
    
    md_content = (
        f"**🏆 Overall Accuracy: {stats['overall_rate']}** (Success {stats['total_s']} / Tested {stats['total_tested']})\n"
        f"**⏳ Overall Progress: {stats['demo_completion']}** ({stats['total_tested']} / {stats['total_expected']} Episodes)\n"
        f"---\n"
        f"{formatted_list}"
    )
    
    prompt = f"""
    Data: Overall Accuracy {stats['overall_rate']}.
    Task Details:
    {formatted_list}
    
    Please output exactly 2 sentences in Chinese:
    1. Identify which task performed the best and which performed the worst.
    2. Briefly evaluate the overall batch processing speed.
    """
    
    try:
        res = requests.post(api_url, json={
            "model": model_name, 
            "prompt": prompt, 
            "stream": False
        }, timeout=60)
        ai_summary = res.json().get("response", "").strip()
    except Exception as e:
        ai_summary = f"AI Analysis currently unavailable. Please check if Ollama is running. ({e})"

    return f"{md_content}\n\n**💡 AI 极简结论:**\n{ai_summary}"

def send_to_feishu(content, webhook_url):
    """Send the interactive card to Feishu/Lark."""
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🚀 VLA Evaluation Report"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Failed to send to Feishu: {response.text}")
    except Exception as e:
        print(f"Feishu webhook error: {e}")

def run_monitor(args):
    print(f"[{time.strftime('%H:%M:%S')}] 🚀 VLA Evaluation Monitor Started")
    print(f"Monitoring Directory: {args.dir}")
    print(f"Expected Tasks: {args.total_tasks} | Episodes/Task: {args.episodes_per_task}")
    
    last_fingerprint = ""
    while True:
        try:
            current_fingerprint = get_dir_fingerprint(args.dir)
            if current_fingerprint and current_fingerprint != last_fingerprint:
                print(f"[{time.strftime('%H:%M:%S')}] 📝 Data changed, generating report...")
                stats = parse_libero_results(args.dir, args.episodes_per_task, args.total_tasks)
                if stats:
                    report = get_ai_report(stats, args.ollama_api, args.ollama_model)
                    send_to_feishu(report, args.webhook)
                    last_fingerprint = current_fingerprint
            
            print(f"[{time.strftime('%H:%M:%S')}] 🔍 Listening... (Interval: {args.interval}s)", end="\r")
        except KeyboardInterrupt: 
            print("\n⏹️ Monitor stopped by user.")
            break
        except Exception as e: 
            print(f"\n❌ Error: {e}")
        
        time.sleep(args.interval)

if __name__ == "__main__":
    args = get_args()
    run_monitor(args)
