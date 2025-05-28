# Medical Data Analysis Platform

A comprehensive platform designed for managing, analyzing, and visualizing medical data. This system provides robust features for user authentication, project management, data versioning, schema management, asynchronous task processing, experiment tracking, and a centralized model registry. It is built with a FastAPI backend and a Vue.js frontend, offering a powerful and intuitive interface for data scientists and researchers.

## Features

### Backend (FastAPI)

*   **User Management:** Secure user authentication and authorization.
*   **Project Management:** Create, manage, and organize data science projects.
*   **Data Versioning & History:** Track changes and maintain versions of datasets within projects.
*   **System Settings:** Configurable system-wide settings.
*   **Data Schema Management:** Define and enforce data schemas for consistency.
*   **Asynchronous Task Processing:** Utilize Celery and Redis for background tasks (e.g., data processing, model training).
*   **Experiment Tracking:** Log and manage machine learning experiments.
*   **Model Registry:** Centralized repository for managing and deploying machine learning models.

### Frontend (Vue.js)

*   **Dashboard:** Overview of projects and system status.
*   **Data Management:**
    *   **Data Upload:** Upload new datasets.
    *   **Data List:** View and manage uploaded data.
    *   **Data Clean:** Tools for data cleaning and preprocessing.
    *   **Data Schema Management:** UI for managing data schemas.
*   **Data Analysis:**
    *   **Data Explorer:** Browse and inspect datasets.
    *   **Data Visualization:** Interactive plots and charts for data exploration.
    *   **Feature Engineering:** Tools for creating and transforming features.
    *   **Statistics Analysis:** Perform statistical analysis on data.
*   **Machine Learning:**
    *   **Model Training:** Initiate and monitor model training processes.
    *   **Model Evaluation:** Evaluate model performance.
    *   **Model Prediction:** Make predictions using trained models.
    *   **Model Management:** Manage trained models in the registry.

## Technologies Used

### Backend

*   **Framework:** FastAPI
*   **Database ORM:** SQLAlchemy
*   **Data Validation:** Pydantic
*   **Settings Management:** Pydantic-settings
*   **Asynchronous Tasks:** Celery, Redis
*   **Data Manipulation:** Pandas, NumPy
*   **Plotting:** Plotly
*   **Scientific Computing:** SciPy
*   **Machine Learning:** Scikit-learn
*   **Database Migrations:** Alembic
*   **Authentication:** Python-jose (JWT), Passlib (Bcrypt)
*   **Web Server:** Uvicorn

### Frontend

*   **Framework:** Vue.js
*   **Routing:** Vue Router
*   **State Management:** Pinia
*   **UI Library:** Element Plus
*   **HTTP Client:** Axios
*   **Charting:** ECharts, Plotly.js
*   **Build Tool:** Vite

## Development Status

Please note the current status of the project:
*   **Backend:** The backend has not yet undergone comprehensive testing. Additionally, some older API endpoints are still present and require refactoring or removal to align with the new project structure.
*   **Frontend:** The frontend is not yet fully adapted to all backend functionalities and may require further integration work.

## Getting Started

### Prerequisites

*   Python 3.9+
*   Node.js (LTS recommended)
*   npm or yarn
*   Redis server (for Celery)

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/medical-data-analysis-platform.git
    cd medical-data-analysis-platform/backend
    ```
2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables:**
    Create a `.env` file in the `backend/` directory based on `backend/.env.example` (if it exists, otherwise infer from `backend/core/config.py`).
    Example `.env` content:
    ```
    DATABASE_URL="sqlite:///./datascience_project_management.db"
    SECRET_KEY="your_super_secret_key"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    STORAGE_BASE_PATH="./data"
    CELERY_BROKER_URL="redis://localhost:6379/0"
    CELERY_RESULT_BACKEND="redis://localhost:6379/0"
    ```
5.  **Run database migrations:**
    ```bash
    alembic upgrade head
    ```
6.  **Start the FastAPI application:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    (Run from the `backend/` directory)

7.  **Start the Celery worker:**
    ```bash
    celery -A tasks worker --loglevel=info
    ```
    (Run from the `backend/` directory)

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../frontend
    ```
2.  **Install dependencies:**
    ```bash
    npm install # or yarn install
    ```
3.  **Start the development server:**
    ```bash
    npm run dev # or yarn dev
    ```
    The frontend will typically run on `http://localhost:5173` (or another port as indicated by Vite).

## Project Structure

```
.
├── backend/                  # FastAPI backend application
│   ├── alembic/              # Database migrations
│   ├── core/                 # Core configurations, security, utilities
│   ├── crud/                 # CRUD operations for database models
│   ├── data/                 # Data storage (processed, features, models, schemas, uploads)
│   ├── models/               # SQLAlchemy database models and Pydantic schemas
│   ├── routers/              # FastAPI routers (API endpoints)
│   ├── services/             # Business logic and service layer
│   ├── tests/                # Unit and integration tests
│   ├── .env                  # Environment variables
│   ├── main.py               # Main FastAPI application entry point
│   ├── requirements.txt      # Python dependencies
│   ├── tasks.py              # Celery tasks definitions
│   └── celery_worker.py      # Celery worker setup
├── frontend/                 # Vue.js frontend application
│   ├── public/               # Static assets
│   ├── src/                  # Frontend source code
│   │   ├── api/              # API client interactions
│   │   ├── components/       # Reusable Vue components
│   │   ├── router/           # Vue Router configuration
│   │   ├── stores/           # Pinia state management stores
│   │   ├── utils/            # Utility functions
│   │   ├── views/            # Vue views (pages)
│   │   ├── App.vue           # Main Vue component
│   │   └── main.js           # Frontend entry point
│   ├── index.html            # Main HTML file
│   ├── package.json          # Frontend dependencies and scripts
│   └── vite.config.js        # Vite configuration
├── data/                     # Root data directory (symlinked or used by backend)
├── data_preprocessor_gui.py  # Standalone data preprocessor GUI (if applicable)
├── feature_extractor_gui.py  # Standalone feature extractor GUI (if applicable)
├── datascience_project_management.db # Default SQLite database file
└── README.md                 # Project README
```

## Data Structure

The `./example` folder contains instance data. The structure is as follows:
- The first level of folders represents different patient IDs.
- The second level of folders is named by time ranges.
- The third level contains different data files for that patient.

Specifically:
- CSV files starting with `ECG` contain columns for "体温 (Body Temperature), 心率 (Heart Rate), 收缩压 (Systolic Blood Pressure), 舒张压 (Diastolic Blood Pressure)".
- CSV files starting with `MV` contain columns for "FiO2, 频率 (Frequency), 目标容量 (Target Volume), 目标压力 (Target Pressure), PEEP, 吸气时间 (Inspiratory Time), 呼出潮气量 (Exhaled Tidal Volume), 分钟通气量 (Minute Ventilation), 总呼吸频率 (Total Respiratory Rate), Ppeak(气道峰压) (Peak Airway Pressure), Pmean(气道平均压) (Mean Airway Pressure), pplat(平台压) (Plateau Pressure), peep(呼末正压) (Positive End-Expiratory Pressure), 动态顺应性 (Dynamic Compliance), 静态顺应性 (Static Compliance), 呼吸功 (Work of Breathing), 呼气时间 (Expiratory Time), 最大吸气流速 (Max Inspiratory Flow), 最大呼气流速 (Max Expiratory Flow)".
These are structures for low-frequency time series data.

Other high-frequency time series data files, such as `*RSP*.csv`, contain only one metric and no header. The first column is the time, precise to the second, and the remaining 50 columns represent 1 second divided into 50 parts, meaning 50Hz data.

## Usage

Once both the backend and frontend servers are running, navigate to the frontend URL (e.g., `http://localhost:5173`) in your web browser. You can then register a new user, create projects, upload data, perform analysis, and manage your machine learning models.

## Contributing

Contributions are welcome! Please follow standard GitHub flow: fork the repository, create a feature branch, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
