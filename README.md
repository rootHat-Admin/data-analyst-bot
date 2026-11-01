# Data Analyst Bot

**An AI-powered Telegram bot for CSV data analysis, visualization, anomaly detection, and PDF reporting.**

Data Analyst Bot helps users turn raw CSV files into useful insights. Upload a dataset to Telegram and receive automated statistical analysis, data quality checks, visualizations, AI-generated explanations, and a downloadable PDF report.

## Features

- **CSV Analysis** — Automatically reads datasets and calculates descriptive statistics.
- **Data Quality Checks** — Detects missing values and potential data quality issues.
- **Anomaly Detection** — Identifies unusual values in numerical columns.
- **Data Visualization** — Generates charts to make patterns and trends easier to understand.
- **AI-Powered Insights** — Uses Google Gemini to explain findings and provide practical recommendations.
- **PDF Reports** — Generates downloadable reports containing analysis results.
- **Telegram Integration** — Simple interface for uploading and analyzing CSV files.

## How It Works

1. Start a conversation with the Telegram bot.
2. Upload a CSV file.
3. The bot analyzes the dataset.
4. Review statistics, data quality findings, and visualizations.
5. Receive an AI-generated explanation.
6. Download the PDF report.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| python-telegram-bot | Telegram integration |
| Pandas | Data processing and analysis |
| Matplotlib | Data visualization |
| Google Gemini API | AI-powered explanations |
| ReportLab | PDF report generation |

## Project Structure

```text
data-analyst-bot/
├── main.py
├── analyzer.py
├── visualizer.py
├── ai_explainer.py
├── pdf_report.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── charts/
├── data/
└── reports/
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/data-analyst-bot.git
cd data-analyst-bot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Linux / macOS**
```bash
source .venv/bin/activate
```

**Windows**
```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

Add your own credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

Never publish your `.env` file or share your API keys.

### 5. Run the bot

```bash
python main.py
```

## Configuration

The application requires:

- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/).

## Security

- API keys are loaded from environment variables.
- `.env` is excluded from version control.
- Virtual environments and generated files are excluded from the repository.

## Project Status

Actively developed.

## License

This project is currently published without an open-source license. All rights are reserved by the author unless a license is added.

---

**Built with Python, Telegram, and Google Gemini.**
