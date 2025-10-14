-- Municipal Budget Data Queries for pgAdmin
-- Use these queries in pgAdmin to explore your budget data

-- 1. Check if the budget schema and tables exist
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name = 'budget';

-- 2. List all tables in the budget schema
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'budget';

-- 3. Check table structures
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_schema = 'budget' AND table_name = 'budget_data'
ORDER BY ordinal_position;

-- 4. Count records in budget_data table
SELECT COUNT(*) as total_records 
FROM budget.budget_data;

-- 5. View sample budget data (first 10 records)
SELECT * 
FROM budget.budget_data 
ORDER BY id 
LIMIT 10;

-- 6. Budget summary by sheet source
SELECT 
    sheet_source,
    COUNT(*) as record_count,
    SUM(budget_amount) as total_amount,
    AVG(budget_amount) as avg_amount,
    MAX(budget_amount) as max_amount,
    MIN(budget_amount) as min_amount
FROM budget.budget_data 
GROUP BY sheet_source
ORDER BY total_amount DESC;

-- 7. Budget by category
SELECT 
    budget_category,
    COUNT(*) as item_count,
    SUM(budget_amount) as total_amount
FROM budget.budget_data 
GROUP BY budget_category
ORDER BY total_amount DESC;

-- 8. Budget by department
SELECT 
    department,
    COUNT(*) as item_count,
    SUM(budget_amount) as total_amount
FROM budget.budget_data 
GROUP BY department
ORDER BY total_amount DESC;

-- 9. Daily processing summary
SELECT 
    processed_date,
    COUNT(*) as records_processed,
    COUNT(DISTINCT sheet_source) as sheets_processed,
    SUM(budget_amount) as total_budget_amount
FROM budget.budget_data 
GROUP BY processed_date
ORDER BY processed_date DESC;

-- 10. View budget summary table
SELECT * 
FROM budget.budget_summary 
ORDER BY processing_date DESC;

-- 11. ETL audit log
SELECT * 
FROM budget.etl_audit 
ORDER BY created_at DESC;

-- 12. Top 10 highest budget items
SELECT 
    budget_item,
    budget_category,
    department,
    budget_amount,
    sheet_source
FROM budget.budget_data 
WHERE budget_amount > 0
ORDER BY budget_amount DESC 
LIMIT 10;

-- 13. Budget items by fiscal year
SELECT 
    fiscal_year,
    COUNT(*) as item_count,
    SUM(budget_amount) as total_budget,
    COUNT(DISTINCT sheet_source) as source_count
FROM budget.budget_data 
GROUP BY fiscal_year
ORDER BY fiscal_year DESC;

-- 14. Recent ETL runs status
SELECT 
    dag_run_id,
    task_id,
    execution_date,
    status,
    records_processed,
    error_message,
    created_at
FROM budget.etl_audit 
ORDER BY created_at DESC 
LIMIT 5;

-- 15. Data quality check - find potential issues
SELECT 
    'Zero amounts' as issue_type,
    COUNT(*) as count
FROM budget.budget_data 
WHERE budget_amount = 0

UNION ALL

SELECT 
    'Missing descriptions' as issue_type,
    COUNT(*) as count
FROM budget.budget_data 
WHERE budget_description IS NULL OR budget_description = ''

UNION ALL

SELECT 
    'Missing categories' as issue_type,
    COUNT(*) as count
FROM budget.budget_data 
WHERE budget_category IS NULL OR budget_category = '';
