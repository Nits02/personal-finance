# Personal Finance Statement Analyzer - Enhanced Version

## Overview

This enhanced personal finance statement analyzer now includes a comprehensive Streamlit web interface and a detailed roadmap for AI-powered enhancements. The system can parse bank and credit card statements from multiple financial institutions, standardize transaction data, perform financial analysis, and provide insights through an intuitive web interface.

## New Features

### Streamlit Web Interface
- **Interactive UI**: User-friendly web interface for uploading and processing financial statements
- **Multi-file Support**: Upload multiple PDF, TXT, or CSV files simultaneously
- **Real-time Processing**: Live processing status and results display
- **Analysis Options**: Configurable analysis and combination features
- **Export Formats**: Support for both CSV and Parquet output formats
- **Downloadable Reports**: Generated analysis reports, charts, and data files

### Enhanced Code Structure
- **Fixed Import Issues**: Resolved module import problems across all parsers
- **Standardized Interface**: Consistent metadata handling across all parsers
- **Improved Error Handling**: Better error reporting and logging throughout the system
- **Updated Dependencies**: Added Streamlit and other required packages

## Quick Start

### Prerequisites
```bash
pip install pandas numpy matplotlib pdfplumber jupyter pytest streamlit
```

### Running the Streamlit Application
```bash
# Set the Python path to include the src directory
PYTHONPATH=/path/to/project/src streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### Using the Web Interface
1. Open your browser to the Streamlit URL (typically http://localhost:8501)
2. Configure options in the sidebar:
   - Enable/disable analysis
   - Enable/disable statement combination
   - Choose output format (CSV or Parquet)
3. Upload your financial statements (PDF, TXT, or CSV files)
4. View processing results and download generated reports

## Supported Financial Institutions

- **ICICI Bank**: Savings account statements and credit card statements
- **Axis Bank**: Bank account statements
- **American Express**: Credit card statements
- **Generic CSV**: Basic CSV transaction files

## Project Structure

```
├── src/
│   ├── ui/
│   │   └── streamlit_app.py          # Streamlit web interface
│   ├── parsers/
│   │   ├── base_parser.py            # Base parser class
│   │   ├── icici_savings_bank_statement_parser.py
│   │   ├── icici_credit_card_parser.py
│   │   ├── axis_bank_statement_parser.py
│   │   └── amex_credit_card_parser.py
│   ├── parser.py                     # Main parser orchestrator
│   ├── standardizer.py               # Transaction standardization
│   ├── analyzer.py                   # Financial analysis engine
│   ├── io_utils.py                   # File I/O utilities
│   ├── logger.py                     # Logging configuration
│   └── config_loader.py              # Configuration management
├── data/
│   ├── raw/                          # Raw statement files
│   ├── processed/                    # Processed transaction data
│   └── temp_raw/                     # Temporary upload storage
├── tests/                            # Unit tests
├── config.yaml                       # Configuration file
├── requirements.txt                  # Python dependencies
└── AI_Enhancement_Roadmap.md         # Detailed AI enhancement plan
```

## Configuration

The system uses `config.yaml` for configuration:

```yaml
data:
  raw_dir: data/raw
  processed_dir: data/processed
logging:
  level: INFO
parsers:
  icici_credit_card: icici_credit_card_parser.ICICICreditCardParser
  icici_savings: icici_savings_bank_statement_parser.ICICISavingsBankStatementParser
  axis_bank: axis_bank_statement_parser.AxisBankStatementParser
  amex_credit_card: amex_credit_card_parser.AmexCreditCardParser
```

## Command Line Usage

You can still use the command line interface:

```bash
# Parse a single statement
python src/parser.py "path/to/statement.pdf"

# Parse and analyze with the run_parser script
python src/run_parser.py "path/to/statement.pdf" --analyze

# Process multiple files in a directory
python src/run_parser.py "path/to/directory/" --analyze --combined --fmt parquet
```

## AI Enhancement Roadmap

This project includes a comprehensive 5-phase roadmap for AI enhancement:

1. **RAG Architecture Implementation**: Retrieval-Augmented Generation for intelligent financial insights
2. **Advanced Language Model Integration**: Local and cloud-based LLM deployment
3. **Agentic AI Foundations**: Autonomous financial planning agents
4. **Monitoring and Optimization**: Production-ready observability
5. **Evaluation and Validation**: Comprehensive testing and quality assurance

See `AI_Enhancement_Roadmap.md` for detailed implementation plans.

## Testing

Run the test suite:
```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is open source. Please ensure compliance with financial data privacy regulations when using with real financial data.

## Security Considerations

- Never commit real financial data to version control
- Use environment variables for sensitive configuration
- Ensure proper data encryption for production deployments
- Follow financial industry security best practices

## Future Enhancements

The AI Enhancement Roadmap outlines plans for:
- Natural language query interface
- Automated financial planning
- Investment analysis and recommendations
- Predictive financial modeling
- Integration with external financial services

For detailed implementation plans, see the AI Enhancement Roadmap document.

