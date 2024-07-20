import streamlit as st
import psycopg2
import pandas as pd
from psycopg2 import sql
from st_aggrid import AgGrid, GridOptionsBuilder

# Database connection without caching
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
def run_query(query, params=None):
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()

# Function to get table columns
def get_table_columns(table_name, schema):
    query = sql.SQL("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
    """)
    return [col[0] for col in run_query(query, (schema, table_name))]

# Function to get metadata fields
def get_metadata_fields():
    query = """
    SELECT table_name, column_name, data_element_name, definition, standard_unit, additional_info
    FROM public.column_metadata
    """
    return run_query(query)

# Streamlit app
st.set_page_config(layout="wide")

st.title('Maritime Reporting Database Viewer')

# Sidebar for filters
st.sidebar.header('Filters')

# Get all schemas, including 'public'
schemas = run_query("""
    SELECT schema_name 
    FROM information_schema.schemata 
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
""")
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
        
        # Display data using AgGrid
        df = pd.DataFrame(data, columns=columns)
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(resizable=True, wrapText=True, autoHeight=True)
        gridOptions = gb.build()
        st.subheader(f'Data from {selected_schema}.{selected_table}')
        AgGrid(df, gridOptions=gridOptions, height=500, theme='light')
        
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
st.header(f'Metadata for {selected_table}')
metadata = get_metadata_fields()

if metadata:
    # Convert metadata to DataFrame
    metadata_df = pd.DataFrame(metadata, columns=['Table Name', 'Column', 'Data Element', 'Definition', 'Unit', 'Additional Info'])
    
    # Filter metadata based on the selected table
    filtered_metadata_df = metadata_df[metadata_df['Table Name'] == selected_table]
    
    if show_mandatory:
        filtered_metadata_df = filtered_metadata_df[filtered_metadata_df['Additional Info'].str.contains('mandatory', case=False, na=False)]
    
    if not filtered_metadata_df.empty:
        # Display metadata using AgGrid with increased width
        gb = GridOptionsBuilder.from_dataframe(filtered_metadata_df)
        gb.configure_default_column(resizable=True, wrapText=True, autoHeight=True)
        gb.configure_grid_options(suppressHorizontalScroll=False)
        gridOptions = gb.build()
        st.subheader(f'Metadata for {selected_schema}.{selected_table}')
        AgGrid(filtered_metadata_df, gridOptions=gridOptions, height=500, theme='light')
    else:
        st.write("No metadata found for this table.")
else:
    st.write("No metadata found.")
