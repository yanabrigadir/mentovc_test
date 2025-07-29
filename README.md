# Y Combinator and LinkedIn Company Scraper

## Installation
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   Run:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

## Setup
1. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```
   DB_HOST=localhost
   DB_PORT=5439
   DB_NAME=test
   DB_USER=test_user
   DB_PASSWORD=test_password
   ```
   Update with your PostgreSQL database credentials.

2. **Set Up LinkedIn Cookies**:
   Create `linkedin_cookies.json` in the project root with LinkedIn cookies:
   ```json
   [
       {
           "name": "cookie_name",
           "value": "cookie_value",
           "domain": ".linkedin.com",
           "path": "/",
           "secure": true,
           "httpOnly": true,
           "sameSite": "None",
           "expires": 1785238922
       }
   ]
   ```
   Export cookies from a logged-in LinkedIn session (e.g., via browser extension).

3. **Set Up Database**:
   Ensure PostgreSQL is running and accessible with `.env` credentials. Create the database schema (handled by `company_service.py`).

## Usage
1. **Run the Scraper**:
   ```bash
   python main.py
   ```
   Scrapes Y Combinator and LinkedIn concurrently, saving data to the database.

2. **View Data with Streamlit**:
   ```bash
   streamlit run combinator_sites.py
   ```
   Opens a web interface at `http://localhost:8501` to display scraped data.
