# Data Analyst Bot

**An AI-powered Telegram bot for CSV data analysis, data visualization, anomaly detection, and PDF reporting.**

Data Analyst Bot transforms raw CSV files into meaningful insights. Simply upload a dataset through Telegram and receive automated statistical analysis, data quality checks, visualizations, AI-generated explanations, and downloadable PDF reports.

---

## Features

- **CSV Data Analysis** — Automatically processes datasets and calculates descriptive statistics.
- **Data Quality Assessment** — Detects missing values and potential data quality issues.
- **Anomaly Detection** — Identifies unusual values in numerical columns.
- **Data Visualization** — Generates charts to highlight patterns and trends.
- **AI-Powered Insights** — Uses Google Gemini to explain findings and provide practical recommendations.
- **PDF Report Generation** — Creates downloadable reports containing analysis results.
- **Telegram Integration** — Provides a simple interface for uploading and analyzing CSV files.

## How It Works

1. Start a conversation with the Telegram bot.
2. Upload a CSV file.
3. The bot automatically analyzes the dataset.
4. Review statistical results, data quality findings, and visualizations.
5. Receive an AI-generated explanation of the results.
6. Download the generated PDF report.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| python-telegram-bot | Telegram Bot API integration |
| Pandas | Data processing and analysis |
| Matplotlib | Data visualization |
| Google Gemini API | AI-powered explanations |
| ReportLab | PDF report generation |
| python-dotenv | Environment variable management |

## Project Structure

```text
data-analyst-bot/
│
├── main.py              # Telegram bot entry point
├── analyzer.py          # CSV analysis and data quality checks
├── visualizer.py        # Chart generation
├── ai_explainer.py      # AI-powered analysis
├── pdf_report.py        # PDF report generation
├── config.py            # Application configuration
│
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore           # Git exclusions
└── README.md            # Project documentation
```

Generated charts, temporary data files, and PDF reports are stored in their respective directories when the application runs.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/rootHat-Admin/data-analyst-bot.git
cd data-analyst-bot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment:

**Linux / macOS**

```bash
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**

```cmd
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using `.env.example` as a template.

**Linux / macOS**

```bash
cp .env.example .env
```

**Windows**

```cmd
copy .env.example .env
```

Open `.env` and add your credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

You need:

- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/).

**Important:** Never publish your `.env` file or expose your API keys.

### 5. Run the bot

```bash
python main.py
```

The bot will start polling Telegram for incoming messages.

## Deployment

The project can be deployed to a Python hosting environment that supports long-running processes and Telegram long polling.

Deployment requirements:

- Python runtime.
- Dependencies installed from `requirements.txt`.
- Environment variables configured securely.
- Startup command: `python main.py`.

The local virtual environment (`.venv`) should not be uploaded to the hosting server.

## Security

- API credentials are loaded from environment variables.
- `.env` is excluded from Git version control.
- Virtual environments and Python cache files are excluded.
- Generated files and local datasets are excluded from the repository.

## Project Status

**Actively developed.**

New improvements and features may be added over time.

## License

No open-source license has been added to this repository. All rights are reserved by the author.

---

**Developed with Python, Telegram, and Google Gemini.**
