"""
Municipal Budget ETL Pipeline
Author: Generated for budget analysis
Description: Extracts, transforms, and loads municipal budget data from Excel file
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text

# Default arguments for the DAG
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Initialize DAG
dag = DAG(
    'budget_municipal_etl',
    default_args=default_args,
    description='Municipal Budget ETL Pipeline',
    schedule=timedelta(days=1),  # Run daily
    catchup=False,
    tags=['budget', 'municipal', 'etl', 'excel'],
)

# File paths
EXCEL_FILE_PATH = '/opt/airflow/data/Budget_municipal.xlsx'
OUTPUT_DIR = '/opt/airflow/output'
PROCESSED_DIR = '/opt/airflow/processed'

def extract_budget_data(**context):
    """
    Extract data from municipal budget Excel file
    """
    try:
        logging.info("Starting data extraction from municipal budget file")
        
        # Create output directories if they don't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        
        # Read all sheets from Excel file
        excel_data = pd.read_excel(EXCEL_FILE_PATH, sheet_name=None, engine='openpyxl')
        
        logging.info(f"Found {len(excel_data)} sheets in the Excel file")
        
        # Store sheet information
        sheet_info = {}
        for sheet_name, df in excel_data.items():
            logging.info(f"Sheet '{sheet_name}': {df.shape[0]} rows, {df.shape[1]} columns")
            sheet_info[sheet_name] = {
                'rows': df.shape[0],
                'columns': df.shape[1],
                'columns_list': df.columns.tolist()
            }
            
            # Save each sheet as CSV for processing
            csv_path = f"{OUTPUT_DIR}/raw_{sheet_name}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            logging.info(f"Saved sheet '{sheet_name}' to {csv_path}")
        
        # Save extraction metadata
        context['task_instance'].xcom_push(key='sheet_info', value=sheet_info)
        context['task_instance'].xcom_push(key='extraction_timestamp', value=datetime.now().isoformat())
        
        logging.info("Data extraction completed successfully")
        return "Extraction completed"
        
    except Exception as e:
        logging.error(f"Error during extraction: {str(e)}")
        raise

def transform_budget_data(**context):
    """
    Transform and clean the municipal budget data
    """
    try:
        logging.info("Starting data transformation")
        
        # Get sheet information from previous task
        sheet_info = context['task_instance'].xcom_pull(key='sheet_info', task_ids='extract_data')
        
        transformed_data = {}
        
        for sheet_name in sheet_info.keys():
            logging.info(f"Transforming sheet: {sheet_name}")
            
            # Read the raw CSV
            csv_path = f"{OUTPUT_DIR}/raw_{sheet_name}.csv"
            df = pd.read_csv(csv_path)
            
            # Basic data cleaning
            # Remove completely empty rows and columns
            df = df.dropna(how='all')
            df = df.dropna(axis=1, how='all')
            
            # Clean column names
            df.columns = df.columns.str.strip()
            df.columns = df.columns.str.replace(r'[^\w\s]', '_', regex=True)
            df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
            
            # Detect and clean numeric columns (budget amounts)
            numeric_columns = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Try to convert to numeric, handling currency symbols and formatting
                    cleaned_series = df[col].astype(str).str.replace(r'[€$,\s]', '', regex=True)
                    cleaned_series = pd.to_numeric(cleaned_series, errors='ignore')
                    
                    if cleaned_series.dtype in ['int64', 'float64']:
                        df[col] = cleaned_series
                        numeric_columns.append(col)
            
            # Add metadata columns
            df['sheet_source'] = sheet_name
            df['processed_date'] = datetime.now().date()
            df['fiscal_year'] = datetime.now().year  # Can be adjusted based on data
            
            # Handle missing values appropriately
            # For numeric columns, fill with 0 (assuming budget items)
            for col in numeric_columns:
                df[col] = df[col].fillna(0)
            
            # For text columns, fill with 'Unknown'
            text_columns = df.select_dtypes(include=['object']).columns
            for col in text_columns:
                if col not in ['sheet_source', 'processed_date']:
                    df[col] = df[col].fillna('Unknown')
            
            # Save transformed data
            transformed_path = f"{PROCESSED_DIR}/transformed_{sheet_name}.csv"
            df.to_csv(transformed_path, index=False, encoding='utf-8')
            
            # Store transformation summary
            transformed_data[sheet_name] = {
                'original_rows': sheet_info[sheet_name]['rows'],
                'cleaned_rows': len(df),
                'numeric_columns': numeric_columns,
                'total_columns': len(df.columns),
                'file_path': transformed_path
            }
            
            logging.info(f"Transformed {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
        
        # Save transformation metadata
        context['task_instance'].xcom_push(key='transformed_data', value=transformed_data)
        
        logging.info("Data transformation completed successfully")
        return "Transformation completed"
        
    except Exception as e:
        logging.error(f"Error during transformation: {str(e)}")
        raise

def create_database_tables(**context):
    """
    Create database tables for storing budget data
    """
    try:
        logging.info("Creating database tables")
        
        # Create direct PostgreSQL connection using SQLAlchemy
        from sqlalchemy import create_engine, text
        
        # Use the internal PostgreSQL database from Docker Compose
        # Connect to the same database Airflow uses
        db_url = "postgresql://airflow:airflow@postgres:5432/airflow"
        engine = create_engine(db_url)
        
        logging.info("Connected to internal PostgreSQL database: airflow")
        
        # SQL to create tables
        create_tables_sql = """
        -- Create a separate schema for budget data
        CREATE SCHEMA IF NOT EXISTS budget;
        
        -- Drop tables if they exist (for development)
        DROP TABLE IF EXISTS budget.budget_summary CASCADE;
        DROP TABLE IF EXISTS budget.budget_data CASCADE;
        DROP TABLE IF EXISTS budget.etl_audit CASCADE;
        
        -- Main budget data table
        CREATE TABLE budget.budget_data (
            id SERIAL PRIMARY KEY,
            sheet_source VARCHAR(255),
            fiscal_year INTEGER,
            processed_date DATE,
            budget_category VARCHAR(255),
            budget_item VARCHAR(255),
            budget_amount DECIMAL(15,2),
            budget_description TEXT,
            department VARCHAR(255),
            account_code VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Summary table for aggregated data
        CREATE TABLE budget.budget_summary (
            id SERIAL PRIMARY KEY,
            sheet_name VARCHAR(255),
            fiscal_year INTEGER,
            total_records INTEGER,
            total_budget_amount DECIMAL(15,2),
            max_budget_item DECIMAL(15,2),
            min_budget_item DECIMAL(15,2),
            average_budget_item DECIMAL(15,2),
            processing_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- ETL audit table
        CREATE TABLE budget.etl_audit (
            id SERIAL PRIMARY KEY,
            dag_run_id VARCHAR(255),
            task_id VARCHAR(255),
            execution_date TIMESTAMP,
            status VARCHAR(50),
            records_processed INTEGER,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for better performance
        CREATE INDEX idx_budget_data_sheet_source ON budget.budget_data(sheet_source);
        CREATE INDEX idx_budget_data_fiscal_year ON budget.budget_data(fiscal_year);
        CREATE INDEX idx_budget_data_processed_date ON budget.budget_data(processed_date);
        CREATE INDEX idx_budget_summary_fiscal_year ON budget.budget_summary(fiscal_year);
        """
        
        # Execute table creation
        with engine.begin() as conn:
            conn.execute(text(create_tables_sql))
        
        logging.info("Database tables created successfully")
        return "Tables created"
        
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
        raise

def load_budget_data(**context):
    """
    Load transformed data into PostgreSQL database and create summary reports
    """
    try:
        logging.info("Starting data loading to PostgreSQL database")
        
        # Create direct PostgreSQL connection
        from sqlalchemy import create_engine, text, inspect
        db_url = "postgresql://airflow:airflow@postgres:5432/airflow"
        engine = create_engine(db_url)
        
        # Ensure budget schema exists before proceeding
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS budget;"))
        
        # Get transformation metadata
        transformed_data = context['task_instance'].xcom_pull(key='transformed_data', task_ids='transform_data')
        
        summary_reports = {}
        all_budget_data = []
        total_records_loaded = 0
        
        for sheet_name, info in transformed_data.items():
            logging.info(f"Loading data from {sheet_name} to database")
            
            # Read transformed data
            df = pd.read_csv(info['file_path'])
            all_budget_data.append(df)
            
            # Prepare data for database insertion
            df_db = df.copy()
            
            # Map columns to database schema
            column_mapping = {}
            for col in df_db.columns:
                if 'amount' in col.lower() or 'budget' in col.lower() or any(keyword in col.lower() for keyword in ['cost', 'expense', 'revenue', 'income']):
                    column_mapping[col] = 'budget_amount'
                elif 'category' in col.lower() or 'type' in col.lower():
                    column_mapping[col] = 'budget_category'
                elif 'item' in col.lower() or 'description' in col.lower():
                    column_mapping[col] = 'budget_item'
                elif 'department' in col.lower() or 'dept' in col.lower():
                    column_mapping[col] = 'department'
                elif 'code' in col.lower() or 'account' in col.lower():
                    column_mapping[col] = 'account_code'
            
            # Create standardized dataframe for database
            db_df = pd.DataFrame()
            db_df['sheet_source'] = df_db['sheet_source']
            db_df['fiscal_year'] = df_db['fiscal_year']
            db_df['processed_date'] = df_db['processed_date']
            
            # Handle dynamic column mapping
            numeric_cols = [col for col in df_db.columns if df_db[col].dtype in ['int64', 'float64'] 
                           and col not in ['fiscal_year', 'processed_date']]
            
            # If we have multiple numeric columns, we'll create multiple rows
            if numeric_cols:
                expanded_rows = []
                for idx, row in df_db.iterrows():
                    for col in numeric_cols:
                        if pd.notna(row[col]) and row[col] != 0:
                            new_row = {
                                'sheet_source': row['sheet_source'],
                                'fiscal_year': row['fiscal_year'],
                                'processed_date': row['processed_date'],
                                'budget_category': column_mapping.get(col, 'General'),
                                'budget_item': f"{col}_{idx}" if col in column_mapping else col,
                                'budget_amount': row[col],
                                'budget_description': f"Budget item from {col}",
                                'department': 'Municipal',
                                'account_code': f"ACC_{idx}_{col[:10]}"
                            }
                            expanded_rows.append(new_row)
                
                if expanded_rows:
                    db_df = pd.DataFrame(expanded_rows)
                else:
                    # Fallback: create basic structure with available data
                    db_df['budget_category'] = 'General'
                    db_df['budget_item'] = f'Item from {sheet_name}'
                    db_df['budget_amount'] = 0.0
                    db_df['budget_description'] = f'Data from sheet {sheet_name}'
                    db_df['department'] = 'Municipal'
                    db_df['account_code'] = 'GENERAL'
            else:
                # No numeric data, create placeholder records
                db_df['budget_category'] = 'General'
                db_df['budget_item'] = f'Item from {sheet_name}'
                db_df['budget_amount'] = 0.0
                db_df['budget_description'] = f'Non-numeric data from sheet {sheet_name}'
                db_df['department'] = 'Municipal'
                db_df['account_code'] = 'GENERAL'
            
            # Insert data into PostgreSQL
            if not db_df.empty:
                db_df.to_sql('budget_data', engine, schema='budget', if_exists='append', index=False, method='multi')
                records_inserted = len(db_df)
                total_records_loaded += records_inserted
                logging.info(f"Inserted {records_inserted} records from {sheet_name}")
            
            # Create sheet-specific summary for database
            if numeric_cols:
                sheet_summary = {
                    'sheet_name': sheet_name,
                    'total_records': len(df),
                    'numeric_columns_count': len(numeric_cols),
                    'total_budget_amount': float(df[numeric_cols].sum().sum()) if numeric_cols else 0.0,
                    'max_budget_item': float(df[numeric_cols].max().max()) if numeric_cols else 0.0,
                    'min_budget_item': float(df[numeric_cols].min().min()) if numeric_cols else 0.0,
                    'average_budget_item': float(df[numeric_cols].mean().mean()) if numeric_cols else 0.0
                }
            else:
                sheet_summary = {
                    'sheet_name': sheet_name,
                    'total_records': len(df),
                    'numeric_columns_count': 0,
                    'total_budget_amount': 0.0,
                    'max_budget_item': 0.0,
                    'min_budget_item': 0.0,
                    'average_budget_item': 0.0
                }
            
            # Insert summary into database
            summary_df = pd.DataFrame([{
                'sheet_name': sheet_summary['sheet_name'],
                'fiscal_year': datetime.now().year,
                'total_records': sheet_summary['total_records'],
                'total_budget_amount': sheet_summary['total_budget_amount'],
                'max_budget_item': sheet_summary['max_budget_item'],
                'min_budget_item': sheet_summary['min_budget_item'],
                'average_budget_item': sheet_summary['average_budget_item'],
                'processing_date': datetime.now()
            }])
            summary_df.to_sql('budget_summary', engine, schema='budget', if_exists='append', index=False)
            
            summary_reports[sheet_name] = sheet_summary
        
        # Combine all data if multiple sheets
        if len(all_budget_data) > 1:
            combined_df = pd.concat(all_budget_data, ignore_index=True)
            combined_path = f"{PROCESSED_DIR}/combined_municipal_budget.csv"
            combined_df.to_csv(combined_path, index=False, encoding='utf-8')
            logging.info(f"Combined dataset saved to {combined_path}")
        
        # Create overall summary report
        overall_summary = {
            'processing_date': datetime.now().isoformat(),
            'total_sheets_processed': len(transformed_data),
            'total_records_processed': sum([info['cleaned_rows'] for info in transformed_data.values()]),
            'total_records_loaded_to_db': total_records_loaded,
            'sheets_summary': summary_reports
        }
        
        # Save summary as JSON
        import json
        summary_path = f"{PROCESSED_DIR}/budget_summary_report.json"
        with open(summary_path, 'w') as f:
            json.dump(overall_summary, f, indent=2, default=str)
        
        # Log ETL audit information (optional - don't fail if table doesn't exist)
        try:
            audit_sql = """
            INSERT INTO budget.etl_audit (dag_run_id, task_id, execution_date, status, records_processed)
            VALUES (:dag_run_id, :task_id, :execution_date, :status, :records_processed)
            """
            with engine.begin() as conn:
                conn.execute(text(audit_sql), {
                    'dag_run_id': context['dag_run'].dag_id,
                    'task_id': 'load_data',
                    'execution_date': context.get('execution_date') or context.get('logical_date') or datetime.now(),
                    'status': 'SUCCESS',
                    'records_processed': total_records_loaded
                })
            logging.info("ETL audit record inserted successfully")
        except Exception as audit_error:
            logging.warning(f"Could not insert audit record (table may not exist): {audit_error}")
        
        logging.info(f"Summary report saved to {summary_path}")
        logging.info(f"Total records loaded to database: {total_records_loaded}")
        
        # Push final results to XCom
        context['task_instance'].xcom_push(key='load_summary', value=overall_summary)
        
        logging.info("Data loading to PostgreSQL completed successfully")
        return "Loading completed"
        
    except Exception as e:
        logging.error(f"Error during loading: {str(e)}")
        
        # Log error to audit table (optional)
        try:
            db_url = "postgresql://airflow:airflow@postgres:5432/airflow"
            engine_error = create_engine(db_url)
            audit_sql = """
            INSERT INTO budget.etl_audit (dag_run_id, task_id, execution_date, status, error_message)
            VALUES (:dag_run_id, :task_id, :execution_date, :status, :error_message)
            """
            with engine_error.begin() as conn:
                conn.execute(text(audit_sql), {
                    'dag_run_id': context['dag_run'].dag_id,
                    'task_id': 'load_data',
                    'execution_date': context.get('execution_date') or context.get('logical_date') or datetime.now(),
                    'status': 'FAILED',
                    'error_message': str(e)
                })
        except:
            pass  # Don't fail if audit logging fails
        
        raise

def validate_etl_process(**context):
    """
    Validate the ETL process and generate final report
    """
    try:
        logging.info("Starting ETL validation")
        
        # Get all previous task results
        extraction_time = context['task_instance'].xcom_pull(key='extraction_timestamp', task_ids='extract_data')
        transformed_data = context['task_instance'].xcom_pull(key='transformed_data', task_ids='transform_data')
        load_summary = context['task_instance'].xcom_pull(key='load_summary', task_ids='load_data')
        
        # Perform validation checks
        validation_results = {
            'etl_start_time': extraction_time,
            'etl_end_time': datetime.now().isoformat(),
            'status': 'SUCCESS',
            'checks_performed': [],
            'issues_found': []
        }
        
        # Check if all expected files exist
        expected_files = []
        for sheet_name in transformed_data.keys():
            expected_files.extend([
                f"{OUTPUT_DIR}/raw_{sheet_name}.csv",
                f"{PROCESSED_DIR}/transformed_{sheet_name}.csv"
            ])
        expected_files.append(f"{PROCESSED_DIR}/budget_summary_report.json")
        
        for file_path in expected_files:
            if os.path.exists(file_path):
                validation_results['checks_performed'].append(f"File exists: {file_path}")
            else:
                validation_results['issues_found'].append(f"Missing file: {file_path}")
                validation_results['status'] = 'WARNING'
        
        # Data quality checks
        total_processed_records = load_summary.get('total_records_processed', 0)
        if total_processed_records > 0:
            validation_results['checks_performed'].append(f"Processed {total_processed_records} records")
        else:
            validation_results['issues_found'].append("No records were processed")
            validation_results['status'] = 'ERROR'
        
        # Save validation report
        validation_path = f"{PROCESSED_DIR}/etl_validation_report.json"
        import json
        with open(validation_path, 'w') as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        logging.info(f"ETL validation completed with status: {validation_results['status']}")
        logging.info(f"Validation report saved to {validation_path}")
        
        return validation_results
        
    except Exception as e:
        logging.error(f"Error during validation: {str(e)}")
        raise

# Define tasks
create_tables_task = PythonOperator(
    task_id='create_database_tables',
    python_callable=create_database_tables,
    dag=dag,
    doc_md="""
    ## Create Database Tables
    
    Creates PostgreSQL tables for storing budget data:
    - budget_data: Main table for budget records
    - budget_summary: Aggregated summary data
    - etl_audit: ETL process tracking
    """
)

extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_budget_data,
    dag=dag,
    doc_md="""
    ## Extract Budget Data
    
    Extracts municipal budget data from Excel file and converts to CSV format.
    
    **Input**: Budget_municipal.xlsx
    **Output**: Raw CSV files for each sheet
    """
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_budget_data,
    dag=dag,
    doc_md="""
    ## Transform Budget Data
    
    Cleans and transforms the extracted budget data:
    - Removes empty rows/columns
    - Standardizes column names
    - Converts currency values to numeric
    - Handles missing values
    - Adds metadata columns
    """
)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_budget_data,
    dag=dag,
    doc_md="""
    ## Load Budget Data
    
    Loads transformed data and generates summary reports:
    - Creates individual sheet summaries
    - Combines all data if multiple sheets
    - Generates budget analytics
    - Creates JSON summary report
    """
)

validate_task = PythonOperator(
    task_id='validate_etl',
    python_callable=validate_etl_process,
    dag=dag,
    doc_md="""
    ## Validate ETL Process
    
    Validates the entire ETL process:
    - Checks file existence
    - Validates data quality
    - Generates validation report
    - Reports ETL status
    """
)

# Set task dependencies
create_tables_task >> extract_task >> transform_task >> load_task >> validate_task