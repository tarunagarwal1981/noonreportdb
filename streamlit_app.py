import streamlit as st

# Minimal Streamlit app to confirm frontend is working
st.title('Maritime Reporting Database Viewer')

st.header('Welcome to the Maritime Reporting Database Viewer')

st.write('This is a minimal Streamlit app to ensure the frontend is working correctly.')

# Sidebar for filters
st.sidebar.header('Filters')

# Placeholder for schema and table selection
selected_schema = st.sidebar.selectbox('Select a schema', ['Schema1', 'Schema2', 'Schema3'])
selected_table = st.sidebar.selectbox('Select a table', ['Table1', 'Table2', 'Table3'])

st.write(f'Selected schema: {selected_schema}')
st.write(f'Selected table: {selected_table}')

# Placeholder for main content area
st.header(f'Data View: {selected_schema}.{selected_table}')
st.write('This is where the table data will be displayed.')

# Placeholder for metadata display
st.header(f'Metadata for {selected_schema}.{selected_table}')
st.write('This is where the table metadata will be displayed.')
