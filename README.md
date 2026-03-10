# VLA-Eval-Monitor
A lightweight Python monitor for VLA model evaluations. Integrates Ollama for local AI summaries and pushes interactive progress cards to Feishu/Lark.轻量级 VLA 模型评测监控工具。结合 Ollama 本地大模型生成智能总结，并自动向飞书推送评测进度与数据卡片。

---

## ✨ Features

- **Real-time Monitoring**: Automatically detects changes in your evaluation directory using MD5 fingerprinting.
- **Metrics Parsing**: Deeply parses `results.json` from Libero (or similar formats) to calculate individual task success rates and overall evaluation progress.
- **AI-Powered Insights**: Integrates with local **Ollama** models (default: `qwen2.5:3b`) to auto-generate a concise, intelligent summary of your model's performance.
- **Feishu / Lark Integration**: Pushes beautiful, interactive Markdown cards directly to your team's chat group.

## 🛠️ Prerequisites

Before running the monitor, ensure you have the following ready:

### 1. Python Environment
- Python 3.8 or higher.
- The `requests` library.

### 2. Feishu / Lark Webhook
1. Open your Feishu/Lark desktop app.
2. Go to the group chat where you want to receive notifications.
3. Click `Settings` (gear icon) -> `Bots` (群机器人) -> `Add Bot` (添加机器人).
4. Choose **Custom Bot** (自定义机器人), give it a name, and copy the **Webhook URL**.

### 3. 🦙 Ollama Setup (For AI Summaries)
This monitor relies on [Ollama](https://ollama.com/) to run LLMs locally without sending sensitive evaluation data to third-party APIs.

1. **Install Ollama**: 
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`
   - Windows/macOS: Download from the [official website](https://ollama.com/download).
2. **Pull and Run the Model**:
   Open your terminal and run:
   ```bash
   ollama run qwen2.5:3b
(Wait for the download to finish. You can press Ctrl+D to exit the chat prompt, the Ollama service will keep running in the background).3. Verify API: Ensure http://localhost:11434/api/generate is accessible on your machine.📦 InstallationClone the repository and install the required dependencies:Bashgit clone [https://github.com/your-username/VLA-Eval-Monitor.git](https://github.com/your-username/VLA-Eval-Monitor.git)
cd VLA-Eval-Monitor

# Install requests library
pip install requests
(Optional) You can save requests>=2.25.0 into a requirements.txt file and run pip install -r requirements.txt.🚀 UsageYou can run the script directly from your terminal. Use command-line arguments to specify your unique paths and configurations.Basic RunIf you are using the default settings (Libero-10, 50 episodes per task, local Ollama):Bashpython vlamonitor.py \
  --dir "/path/to/your/eval_results/libero_10" \
  --webhook "[https://open.feishu.cn/open-apis/bot/v2/hook/YOUR-WEBHOOK-TOKEN](https://open.feishu.cn/open-apis/bot/v2/hook/YOUR-WEBHOOK-TOKEN)"
Advanced ConfigurationCustomize parameters for different datasets or models:Bashpython vlamonitor.py \
  --dir "/data/runs/vla0/eval_libero/libero_10" \
  --webhook "[https://open.feishu.cn/open-apis/bot/v2/hook/xxx](https://open.feishu.cn/open-apis/bot/v2/hook/xxx)" \
  --ollama_api "http://localhost:11434/api/generate" \
  --ollama_model "llama3" \
  --total_tasks 10 \
  --episodes_per_task 50 \
  --interval 300
Argument DetailsArgumentTypeDefaultDescription--dirstrRequiredPath to the directory containing your evaluation results.--webhookstrRequiredYour Feishu/Lark Custom Bot Webhook URL.--ollama_apistrhttp://localhost:11434/api/generateThe endpoint for your local Ollama instance.--ollama_modelstrqwen2.5:3bThe local model used to generate the AI summary.--total_tasksint10Total number of expected tasks (e.g., 10 for Libero-10).--episodes_per_taskint50Expected number of evaluation episodes/demos per task.--intervalint300Polling interval in seconds (default: 300s / 5 mins).🖥️ Running in the Background (For Servers)Since this is a continuous monitoring tool, you likely want it to keep running even after you disconnect from your SSH session.Using nohup:Bashnohup python vlamonitor.py --dir "/your/path" --webhook "your_webhook" > monitor.log 2>&1 &
To stop it later, find the process ID using ps aux | grep vlamonitor.py and kill it (kill -9 PID).Using tmux or screen (Recommended):Bashtmux new -s vla_monitor
python vlamonitor.py --dir "/your/path" --webhook "your_webhook"
# Press Ctrl+B, then D to detach. The monitor will keep running.
📂 Expected Directory StructureThe script is specifically optimized for parsing Libero dataset evaluation outputs. It expects your --dir to contain subfolders for each task, each containing a results.json:Plaintextlibero_10/
├── task_1_put_the_apple_in_the_bowl/
│   ├── results.json
│   └── videos/
├── task_2_.../
│   └── results.json
└── ...
🤝 License & ContributingThis project is licensed under the MIT License.Pull requests are welcome! If you want to add support for other datasets (like RLBench, RoboVerse) or other notification platforms (Slack, Discord), feel free to open an issue or submit a PR.
