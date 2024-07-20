import streamlit as st
import psycopg2
import pandas as pd
from psycopg2 import sql

# Database connection
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=st.secrets["db_connection"]["host"],
        port=st.secrets["db_connection"]["port"],
        dbname=st.secrets["db_connection"]["dbname"],
        user=st.secrets["db_connection"]["user"],
        password=st.secrets["db_connection"]["password"]
    )

conn = init_connection()

# Function to run queries
@st.cache_data
def run_query(query, params=None):
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()

# Function to get table columns
@st.cache_data
def get_table_columns(table_name, schema='jsmea_voy'):
    query = sql.SQL("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
    """)
    return [col[0] for col in run_query(query, (schema, table_name))]

# Function to get mandatory fields
@st.cache_data
def get_mandatory_fields(table_name):
    query = """
    SELECT column_name
    FROM public.column_metadata
    WHERE table_name = %s
    AND additional_info LIKE '%%mandatory%%'
    """
    return [field[0] for field in run_query(query, (table_name,))]

# Streamlit app
st.title('Maritime Reporting Database Viewer')

# Sidebar for filters
st.sidebar.header('Filters')

# Get all schemas
schemas = run_query("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public')")
selected_schema = st.sidebar.selectbox('Select a schema', [schema[0] for schema in schemas])

# Get tables for selected schema
tables = run_query("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (selected_schema,))
selected_table = st.sidebar.selectbox('Select a table', [table[0] for table in tables])

# Option to show only mandatory fields
show_mandatory = st.sidebar.checkbox('Show only mandatory fields')

# Main content area
st.header(f'Data View: {selected_schema}.{selected_table}')

if selected_table:
    # Get columns
    if show_mandatory:
        columns = get_mandatory_fields(selected_table)
    else:
        columns = get_table_columns(selected_table, selected_schema)
    
    if columns:
        # Construct and execute query
        columns_str = ', '.join(columns)
        query = sql.SQL("SELECT {} FROM {}.{}").format(
            sql.SQL(columns_str),
            sql.Identifier(selected_schema),
            sql.Identifier(selected_table)
        )
        data = run_query(query)
        
        # Display data
        df = pd.DataFrame(data, columns=columns)
        st.dataframe(df)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'{selected_schema}_{selected_table}.csv',
            mime='text/csv',
        )
    else:
        st.write("No columns found or accessible.")
else:
    st.write("Please select a table to view data.")

# Display table metadata
if selected_table:
    st.header(f'Metadata for {selected_schema}.{selected_table}')
    metadata_query = """
    SELECT column_name, data_element_name, definition, standard_unit, additional_info
    FROM public.column_metadata
    WHERE table_name = %s
    """
    metadata = run_query(metadata_query, (selected_table,))
    if metadata:
        metadata_df = pd.DataFrame(metadata, columns=['Column', 'Data Element', 'Definition', 'Unit', 'Additional Info'])
        st.dataframe(metadata_df)
    else:
        st.write("No metadata found for this table.")
