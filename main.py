
import os
import html
import tempfile
import asyncio
import logging
import re
import markdown

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError, NetworkError, TimedOut
from telegram.request import HTTPXRequest

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from ai_explainer import explain_analysis
from visualizer import create_charts
from analyzer import analyze_csv
from pdf_report import create_pdf_report


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

active_chats = set()

MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_MESSAGE_LENGTH = 3900


# --------------------------------------------------
# MARKDOWN TO TELEGRAM HTML
# --------------------------------------------------

def markdown_to_telegram_html(text: str) -> str:
    result = markdown.markdown(
        text,
        extensions=["fenced_code", "sane_lists"],
    )

    result = re.sub(
        r"<h[1-6]>(.*?)</h[1-6]>",
        r"<b>\1</b>\n",
        result,
        flags=re.DOTALL,
    )

    result = result.replace("<strong>", "<b>")
    result = result.replace("</strong>", "</b>")
    result = result.replace("<em>", "<i>")
    result = result.replace("</em>", "</i>")

    result = result.replace("<p>", "")
    result = result.replace("</p>", "\n\n")
    result = result.replace("<ul>", "")
    result = result.replace("</ul>", "")
    result = result.replace("<ol>", "")
    result = result.replace("</ol>", "")
    result = result.replace("<li>", "• ")
    result = result.replace("</li>", "\n")

    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()


# --------------------------------------------------
# STATUS ANIMATION
# --------------------------------------------------

async def animate_status(status_message, status):
    frames = ["◐", "◓", "◑", "◒"]
    index = 0

    while True:
        frame = frames[index % len(frames)]

        text = (
            f"{frame} <b>DATA ANALYST BOT</b>\n\n"
            f"{status['stage']}"
        )

        try:
            await status_message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
            )
        except TelegramError:
            pass

        index += 1
        await asyncio.sleep(1.5)


async def stop_animation(task):
    if task is None:
        return

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass


# --------------------------------------------------
# SAFE FILE DOWNLOAD WITH RETRIES
# --------------------------------------------------

async def download_csv(document, file_path):
    attempts = 3

    for attempt in range(attempts):
        try:
            telegram_file = await document.get_file()

            await telegram_file.download_to_drive(
                custom_path=file_path
            )

            return

        except (TimedOut, NetworkError):
            if os.path.exists(file_path):
                os.remove(file_path)

            if attempt == attempts - 1:
                raise

            delay = 2 ** (attempt + 1)

            logger.warning(
                "Telegram download failed. "
                "Retrying in %s seconds. Attempt %s/%s",
                delay,
                attempt + 1,
                attempts,
            )

            await asyncio.sleep(delay)


# --------------------------------------------------
# TELEGRAM COMMANDS
# --------------------------------------------------

async def start(update, context):
    await update.message.reply_text(
        "👋 Welcome to Data Analyst Bot!\n\n"
        "Upload a CSV file and I will:\n"
        "📊 Analyze your data\n"
        "🔍 Detect unusual values\n"
        "🧮 Check calculation errors\n"
        "🤖 Generate AI insights\n"
        "📈 Create charts\n"
        "📄 Prepare a PDF report\n\n"
        "Let's explore your data!"
    )


async def help_command(update, context):
    await update.message.reply_text(
        "📌 HOW TO USE\n\n"
        "1. Upload a CSV file.\n"
        "2. Wait while your data is analyzed.\n"
        "3. Receive your report, charts and PDF.\n\n"
        "COMMANDS\n"
        "/start - Start the bot\n"
        "/help - Show instructions"
    )


# --------------------------------------------------
# ANOMALY SUMMARY
# --------------------------------------------------

def get_anomaly_summary(outliers: dict) -> tuple:
    statistical_count = 0
    business_count = 0

    for info in outliers.values():
        statistical = info.get("statistical", {})
        business = info.get("business_rules", {})

        statistical_count += statistical.get("count", 0)
        business_count += business.get("count", 0)

    return statistical_count, business_count


def build_calculation_summary(errors: dict) -> str:
    if not errors:
        return (
            "\n🧮 <b>CALCULATION VALIDATION</b>\n"
            "No calculation errors detected.\n"
        )

    total_errors = sum(
        info.get("count", 0)
        for info in errors.values()
    )

    message = (
        "\n🧮 <b>CALCULATION VALIDATION</b>\n"
        f"Total calculation errors: {total_errors}\n"
    )

    for column, info in errors.items():
        safe_column = html.escape(str(column))

        message += (
            f"\n<b>{safe_column}</b>: "
            f"{info['count']} errors\n"
        )

        for item in info.get("sample", [])[:3]:
            message += (
                f"• Row {item['row']}: "
                f"actual={item['actual']:.2f}, "
                f"expected={item['expected']:.2f}\n"
            )

    return message


# --------------------------------------------------
# CSV HANDLER
# --------------------------------------------------

async def handle_csv(update, context):
    document = update.message.document
    chat_id = update.effective_chat.id

    if (
        not document.file_name
        or not document.file_name.lower().endswith(".csv")
    ):
        await update.message.reply_text(
            "⚠️ Please upload a CSV file."
        )
        return

    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            "⚠️ File too large. Maximum size is 15 MB."
        )
        return

    if chat_id in active_chats:
        await update.message.reply_text(
            "⏳ Your previous file is still being analyzed. "
            "Please wait until it finishes."
        )
        return

    active_chats.add(chat_id)

    status_message = None
    animation_task = None

    file_path = None
    pdf_path = None
    chart_paths = []

    current_stage = "download"

    status = {
        "stage": "📥 Downloading your CSV file..."
    }

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".csv",
            delete=False,
        ) as temp_file:
            file_path = temp_file.name

        status_message = await update.message.reply_text(
            "◐ DATA ANALYST BOT\n\n"
            "📥 Preparing your file..."
        )

        animation_task = asyncio.create_task(
            animate_status(status_message, status)
        )

        # DOWNLOAD CSV

        current_stage = "download"
        status["stage"] = "📥 Downloading your CSV file..."

        await download_csv(document, file_path)

        # CSV ANALYSIS

        current_stage = "csv"
        status["stage"] = "📊 Analyzing your data..."

        report = await asyncio.to_thread(
            analyze_csv,
            file_path,
        )

        # AI ANALYSIS

        current_stage = "ai"
        status["stage"] = (
            "🤖 Generating AI insights...\n"
            "This may take a little while."
        )

        try:
            ai_explanation = await asyncio.wait_for(
                asyncio.to_thread(
                    explain_analysis,
                    report,
                ),
                timeout=90,
            )

        except asyncio.TimeoutError:
            logger.warning("AI analysis timed out.")

            ai_explanation = (
                "AI analysis took too long and was skipped. "
                "The statistical report is still available."
            )

        except Exception:
            logger.exception("AI explanation failed.")

            ai_explanation = (
                "AI analysis is temporarily unavailable. "
                "The statistical report is still available."
            )

        # CREATE CHARTS

        current_stage = "charts"
        status["stage"] = "📈 Creating data visualizations..."

        chart_paths = await asyncio.to_thread(
            create_charts,
            file_path,
            report["numeric_columns"],
        )

        chart_paths = chart_paths or []

        # CREATE PDF

        current_stage = "pdf"
        status["stage"] = "📄 Preparing your PDF report..."

        pdf_path = await asyncio.to_thread(
            create_pdf_report,
            report,
            ai_explanation,
        )

        # BUILD STATISTICAL REPORT

        current_stage = "sending_report"

        quality = report["data_quality"]

        message = (
            "📊 <b>DATA ANALYSIS REPORT</b>\n\n"
            f"📁 Rows: {report['rows']}\n"
            f"📋 Columns: {report['columns']}\n\n"
            "🔍 <b>DATA QUALITY</b>\n"
            f"Missing values: {quality['missing_values']}\n"
            f"Duplicate rows: {quality['duplicate_rows']}\n\n"
            "📈 <b>NUMERIC STATISTICS</b>\n"
        )

        for column, stats in report["statistics"].items():

            if "mean" not in stats:
                continue

            safe_column = html.escape(str(column))

            message += (
                f"\n<b>{safe_column}</b>\n"
                f"Mean: {stats['mean']:.2f} | "
                f"Median: {stats['median']:.2f}\n"
                f"Min: {stats['min']:.2f} | "
                f"Max: {stats['max']:.2f}\n"
            )

        # ANOMALY SUMMARY

        statistical_count, business_count = (
            get_anomaly_summary(report.get("outliers", {}))
        )

        message += (
            "\n⚠️ <b>ANOMALY DETECTION</b>\n"
            f"Statistical outliers: {statistical_count}\n"
            f"Business rule violations: {business_count}\n"
            f"Total flagged values: "
            f"{statistical_count + business_count}\n"
            "\nℹ️ Statistical outliers are unusual values, "
            "not necessarily errors.\n"
        )

        # CALCULATION ERRORS

        message += build_calculation_summary(
            report.get("calculation_errors", {})
        )

        # DATA INSIGHTS

        message += "\n💡 <b>DATA INSIGHTS</b>\n"

        if report["insights"]:
            for insight in report["insights"][:3]:
                message += (
                    f"• {html.escape(str(insight))}\n"
                )
        else:
            message += (
                "No time-based trends were calculated.\n"
            )

        # SEND REPORT IN SAFE-SIZED PARTS

        for start_index in range(
            0,
            len(message),
            MAX_MESSAGE_LENGTH,
        ):
            await update.message.reply_text(
                message[
                    start_index:
                    start_index + MAX_MESSAGE_LENGTH
                ],
                parse_mode=ParseMode.HTML,
            )

        # SEND AI REPORT

        current_stage = "sending_ai"

        formatted_explanation = markdown_to_telegram_html(
            ai_explanation
        )

        await update.message.reply_text(
            "🤖 <b>AI ANALYSIS</b>\n\n"
            + formatted_explanation[:MAX_MESSAGE_LENGTH],
            parse_mode=ParseMode.HTML,
        )

        # SEND CHARTS

        current_stage = "sending_charts"

        if chart_paths:
            for chart_path in chart_paths:

                if not os.path.exists(chart_path):
                    logger.warning(
                        "Chart file does not exist: %s",
                        chart_path,
                    )
                    continue

                with open(chart_path, "rb") as chart:
                    await update.message.reply_photo(
                        photo=chart,
                    )
        else:
            await update.message.reply_text(
                "ℹ️ No numeric columns available for charts."
            )

        # SEND PDF

        current_stage = "sending_pdf"

        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf:
                await update.message.reply_document(
                    document=pdf,
                    filename="analysis_report.pdf",
                    caption="📄 Your PDF report is ready!",
                )
        else:
            logger.warning("PDF file was not created.")

        # FINISH

        await stop_animation(animation_task)
        animation_task = None

        await update.message.reply_text(
            "✅ <b>ANALYSIS COMPLETE!</b>\n\n"
            "Your data has been successfully processed.\n"
            "Thank you for using Data Analyst Bot! 🚀",
            parse_mode=ParseMode.HTML,
        )

        try:
            await status_message.delete()
        except TelegramError:
            logger.warning("Could not delete status message.")

    except Exception:
        logger.exception(
            "CSV analysis failed at stage: %s",
            current_stage,
        )

        await stop_animation(animation_task)
        animation_task = None

        error_messages = {
            "download": (
                "Could not download your file. "
                "Telegram or your internet connection may be temporarily unavailable. "
                "Please try again."
            ),
            "csv": (
                "Could not read this CSV file. "
                "Check its format, encoding and contents."
            ),
            "charts": (
                "Your data was analyzed, but chart generation failed."
            ),
            "pdf": (
                "Your data was analyzed, but PDF generation failed."
            ),
            "sending_report": (
                "Telegram could not send the statistical report."
            ),
            "sending_ai": (
                "The statistical report was sent, but Telegram could not send the AI report."
            ),
            "sending_charts": (
                "The reports were created, but Telegram could not send the charts."
            ),
            "sending_pdf": (
                "The reports were created, but Telegram could not send the PDF."
            ),
        }

        error_text = error_messages.get(
            current_stage,
            "An unexpected error occurred. Please try again.",
        )

        if current_stage.startswith("sending"):
            error_text += (
                "\n\nSome results may already have been delivered."
            )

        if status_message:
            try:
                await status_message.edit_text(
                    "❌ <b>ANALYSIS FAILED</b>\n\n"
                    + error_text,
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError:
                logger.warning(
                    "Could not update the error status message."
                )
        else:
            try:
                await update.message.reply_text(error_text)
            except TelegramError:
                logger.exception(
                    "Could not send the error message."
                )

    finally:
        await stop_animation(animation_task)

        temporary_files = (
            [file_path, pdf_path] + list(chart_paths or [])
        )

        for path in temporary_files:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    logger.exception(
                        "Could not remove temporary file."
                    )

        active_chats.discard(chat_id)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is missing. Check your .env file."
        )

    request = HTTPXRequest(
        connection_pool_size=20,
        connect_timeout=30,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=30,
    )

    updates_request = HTTPXRequest(
        connection_pool_size=2,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30,
    )

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(request)
        .get_updates_request(updates_request)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            handle_csv,
        )
    )

    logger.info("Data Analyst Bot is running!")

    app.run_polling()


if __name__ == "__main__":
    main()
