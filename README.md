# Finnish Government Budget Explorer

A natural language interface for exploring Finnish government financial data, using the Tutkihallintoa API, BigQuery, Vertex AI, and Streamlit.

## Overview

This application allows users to query Finnish government financial data using natural language. The system:

1. Translates natural language questions into SQL queries
2. Retrieves data from BigQuery
3. Presents results with appropriate visualizations
4. Provides natural language explanations of the findings

## Features

- **Natural Language Interface**: Ask questions in plain language about government finances
- **Dynamic SQL Generation**: Automatically generates optimized SQL queries
- **Intelligent Visualizations**: Selects appropriate chart types based on data and query
- **Insightful Analysis**: Provides explanations and insights about the query results
- **Interactive Filtering**: Apply filters by time period, ministry, and more

## Architecture

The application consists of several components:

### Data Layer
- **Tutkihallintoa API Client** (`utils/api_client.py`): Fetches data from the Finnish government finances API
- **BigQuery Loader** (`utils/bigquery_loader.py`): Loads and transforms data into BigQuery
- **SQL Executor** (`utils/sql_executor.py`): Executes SQL queries against BigQuery

### Query Processing Layer
- **NL to SQL Converter** (`utils/nl_to_sql.py`): Converts natural language to SQL
- **LLM Interface** (`models/llm_interface.py`): Interfaces with Vertex AI models
- **SQL Templates** (`sql/query_templates.py`): Reusable SQL patterns

### Visualization Layer
- **Financial Data Visualizer** (`utils/visualization.py`): Creates appropriate visualizations

### UI Layer
- **Query Input** (`components/query_input.py`): Handles user input
- **Visualization Display** (`components/visualization_display.py`): Displays results
- **Sidebar** (`components/sidebar.py`): Provides filtering and settings

## Data Schema

The financial data schema includes:

- **Time fields**: `Vuosi` (Year), `Kk` (Month)
- **Administrative structure**: `Ha_Tunnus` (Admin branch code), `Hallinnonala` (Admin branch name)
- **Budget structure**: `PaaluokkaOsasto_TunnusP`, `Luku_TunnusP`, `Momentti_TunnusP` (hierarchy)
- **Financial values**: `Alkuperäinen_talousarvio` (Original budget), `Voimassaoleva_talousarvio` (Current budget), `Nettokertymä` (Net accumulation)

## Setup and Installation

### Prerequisites

- Python 3.8+
- Google Cloud Platform account with:
  - BigQuery enabled
  - Vertex AI enabled
  - Service account with appropriate permissions

### Environment Variables

Set the following environment variables:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/finnish-budget-explorer.git
cd finnish-budget-explorer
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Initial Data Load

To load initial data into BigQuery:

```bash
python scripts/load_data.py --years=2020,2021,2022,2023,2024
```

### Running the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

## Example Queries

The application can answer questions such as:

- "What was the military budget for 2022?"
- "Compare defense spending between 2022 and 2023 by quarter"
- "How has the education budget changed from 2020 to 2023?"
- "Show me the top 5 ministries by spending in 2023"
- "What is the trend of government net cash flow in 2023 by month?"
- "How much has defense spending grown between 2020 and 2024?"
- "Compare budget utilization rates across ministries in 2023"

## Technical Details

### LLM Integration

The application uses Vertex AI's Gemini models with specifically designed prompts to:

1. Parse natural language questions
2. Generate SQL queries
3. Explain results in natural language
4. Suggest visualization types

### Visualization Logic

The system automatically selects the most appropriate visualization based on:

- Query intent (comparison, trend, breakdown)
- Data structure (time series, categorical)
- Number of dimensions and measures

### Error Handling

The application implements robust error handling for:

- API rate limiting and timeouts
- SQL generation failures
- Query execution errors
- Empty result sets

## Project Structure

```
finnish-budget-explorer/
├── app.py                      # Main application entry point
├── components/                 # UI components
│   ├── query_input.py          # Natural language input component
│   ├── sidebar.py              # Filters and settings sidebar
│   └── visualization_display.py # Results and visualization display
├── models/
│   └── llm_interface.py        # LLM interaction logic
├── sql/
│   └── query_templates.py      # SQL query templates
├── utils/
│   ├── api_client.py           # Tutkihallintoa API client
│   ├── bigquery_loader.py      # BigQuery data loading utilities
│   ├── bigquery_schema.py      # Schema definitions
│   ├── nl_to_sql.py            # Natural language to SQL conversion
│   ├── prompt_templates.py     # LLM prompt templates
│   ├── sql_executor.py         # SQL execution utilities
│   └── visualization.py        # Visualization utilities
└── tests/                      # Unit and integration tests
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GPL3 - see the LICENSE file for details.

## Acknowledgments

- Data provided by the [Tutkihallintoa.fi](https://tutkihallintoa.fi/) API
- Built with [Streamlit](https://streamlit.io/), [BigQuery](https://cloud.google.com/bigquery), and [Vertex AI](https://cloud.google.com/vertex-ai)