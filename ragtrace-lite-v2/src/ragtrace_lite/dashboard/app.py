"""
RAGTrace Dashboard - Interactive Web Interface
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from pathlib import Path
import logging

from ragtrace_lite.config.config_loader import get_config
from ragtrace_lite.config.logging_setup import setup_logging
from .services import DashboardService

# Setup centralized logging
setup_logging(debug=False)
logger = logging.getLogger(__name__)

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Basic CORS support
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# --- Error Handling ---
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions with JSON response."""
    return jsonify({
        "error": e.name,
        "message": e.description
    }), e.code

@app.errorhandler(Exception)
def handle_exception(e):
    """Return JSON instead of HTML for API errors."""
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    response = {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }
    return jsonify(response), 500


# --- Configuration and Service Initialization ---

# Use ConfigLoader for all configurations
config = get_config()
RESULTS_PATH = Path(config.get("reports.output_dir", "results")).resolve()
RESULTS_PATH.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

logger.info(f"Dashboard initialized. Results path: {RESULTS_PATH}")

# Initialize the single service layer
dashboard_service = DashboardService()


# --- API Routes ---

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard_v2.html')


@app.route('/api/reports')
def get_reports():
    """API endpoint for fetching all reports"""
    reports = dashboard_service.get_all_reports()
    return jsonify(reports)


@app.route('/api/report/<run_id>')
def get_report(run_id):
    """API endpoint for fetching a single report's details"""
    report = dashboard_service.get_report_details(run_id)
    if report:
        return jsonify(report)
    return jsonify({'error': 'Report not found'}), 404


@app.route('/api/compare', methods=['POST'])
def compare_reports():
    """API endpoint for comparing two or more reports"""
    data = request.get_json()
    run_ids = data.get('run_ids', [])

    if not run_ids or len(run_ids) < 2:
        return jsonify({'error': 'At least two run_ids are required for comparison'}), 400

    # The service layer handles the A/B test logic
    # For simplicity, we compare the first two IDs provided
    results = dashboard_service.perform_ab_test([run_ids[0]], run_ids[1:])
    return jsonify(results)


@app.route('/api/trend/<int:days>')
def get_trend(days):
    """API endpoint for trend data over a specified number of days"""
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    trend_data = dashboard_service.get_time_series_stats(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    return jsonify(trend_data)


@app.route('/api/questions/<run_id>')
def get_questions(run_id):
    """API endpoint for fetching question details for a specific run"""
    questions = dashboard_service.get_question_details(run_id)
    return jsonify(questions)


@app.route('/api/ab-test', methods=['POST'])
def ab_test():
    """API endpoint for A/B testing between two evaluations"""
    data = request.get_json()
    run_id_a = data.get('run_id_a')
    run_id_b = data.get('run_id_b')

    if not run_id_a or not run_id_b:
        return jsonify({'error': 'Both run_id_a and run_id_b are required'}), 400

    results = dashboard_service.perform_ab_test([run_id_a], [run_id_b])
    return jsonify(results)


@app.route('/api/time-series', methods=['POST'])
def time_series():
    """API endpoint for getting time series statistics for a date range"""
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date are required'}), 400

    result = dashboard_service.get_time_series_stats(start_date, end_date)
    return jsonify(result)


@app.route('/api/export/<run_id>')
def export_report(run_id):
    """Export report as HTML"""
    # Check if an HTML report file already exists
    html_files = list(RESULTS_PATH.glob(f"*{run_id}*.html"))
    if html_files:
        logger.info(f"Found existing HTML report for {run_id}, serving file.")
        return send_from_directory(RESULTS_PATH, html_files[0].name)

    # If not, return an error because on-the-fly generation is not supported here
    # The report should be generated by the CLI tool.
    logger.warning(f"HTML report for {run_id} not found in {RESULTS_PATH}.")
    return jsonify({
        'error': 'Report file not found.',
        'message': 'Please generate the report first using the CLI.'
    }), 404


def run_dashboard(host='127.0.0.1', port=8080, debug=True):
    """Run the dashboard server"""
    logger.info(f"Starting RAGTrace Dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_dashboard()
