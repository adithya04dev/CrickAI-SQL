import streamlit as st
from search_database import search
from sql_engine import critiquer_chat, generate_initial_query,generate_critique_query, get_sql_query
from bigquery_engine import query_to_dataframe
import os 
from visualisations import generate_chart_config, process_chart_configuration, DatawrapperClient,main
st.title("Analytics App")

def add_markdown(text, role):
    st.session_state.messages.append({"role": role, "content": text})
    # st.chat_message(role).markdown(text)

def set_relevant_column():
    st.session_state.relevant_column = st.session_state.json_response['output']
    st.session_state.initial = True
    st.session_state.set_clicked = True

def choose_relevant_column():
    st.session_state.choose_clicked = True

def confirm_choose():
    st.session_state.relevant_column = st.session_state.temp_column
    st.session_state.initial = True
    st.session_state.confirm_clicked = True
    add_markdown(f"Chosen relevant Columns: {st.session_state.relevant_column}", "user")

def retry_preprocessing():
    st.session_state.pop('json_response', None)
    st.session_state.pop('user_query', None)
    st.session_state.retry_clicked = True


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": 'assistant', "content": 'Prompt what stats you want to calculate and press submit'}]
if 'json_response' not in st.session_state:
    st.session_state.json_response = None
for message in st.session_state.messages:
    if message["role"] == "bigquery":
        st.chat_message("bigquery").dataframe(message["content"])
        
    else:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
if 'data_frame' not in st.session_state:
    st.session_state.data_frame = None

if 'critiquer_chat' not in st.session_state:
    st.session_state.critiquer_chat = critiquer_chat()
if 'sql_query' not in st.session_state:
    st.session_state.sql_query = None

if 'error' not in st.session_state:
    st.session_state.error = None

if 'initial' not in st.session_state:
    st.session_state.initial=True
if 'critique_response' not in st.session_state:
    st.session_state.critique_response = ' '


# def search(prompt):
#     # Placeholder for your custom search function
#     return f"Search results for: {prompt}"


# Create a horizontal layout with dropdown and text input
col1, col2= st.columns([1, 4])  # Adjust the ratios as needed

with col1:
    option = st.selectbox(
        "Select Mode",
        ("Preprocess", "Querying", "Visualising"),
        label_visibility="visible"
    )

with col2:
    prompt = st.text_input("Prompt", key="main_input")


        

if 'state' not in st.session_state:
    st.session_state.state = 'initial'
def add_markdown(text,role):
    st.session_state.messages.append({"role": role, "content": text})
if option == "Preprocess":
    
    
    submit = st.button("Submit", key="submit_button")
    if prompt:
        if   submit:

            st.session_state.user_query = prompt
            add_markdown(prompt, "user")
            st.session_state.json_response, search_result = search(prompt)
            usr_messg="The above are extracted value present in database,if u think they are appropriate then press set else retry by pressing submit again"
            add_markdown(f"{search_result}\n{usr_messg}", "assistant")


            st.rerun()
        col1, col2  = st.columns(2)
        with col1:
            if st.button("Set", key="set_button"):
                
                set_relevant_column()
        
        with col2:
            if st.button("Choose", key="choose_button"):
                choose_relevant_column()



        if 'set_clicked' in st.session_state and st.session_state.set_clicked:
            add_markdown(f"Relevant column set to: {str(st.session_state.relevant_column)}", "user")
            st.session_state.set_clicked = False

            add_markdown("Now u can proceed to query mode", "assistant")
            # re run
            st.rerun()
            

        if 'choose_clicked' in st.session_state and st.session_state.choose_clicked:
            st.session_state.temp_column = st.text_input("Enter the column name", key="column_input")
            if st.button("Confirm", key="confirm_button"):
                confirm_choose()
                st.session_state.choose_clicked = False
                st.rerun()

        if 'retry_clicked' in st.session_state and st.session_state.retry_clicked:
            st.rerun()
elif option == "Querying":
    # st.write("Querying option selected. Implement your querying logic here.")
    
    if st.session_state.initial :
        
        query_button = st.button("Write Query", key="query_button")
        if query_button:    
            initial_response = generate_initial_query(st.session_state.user_query, st.session_state.relevant_column)              
            st.session_state.critique_response = generate_critique_query(st.session_state.user_query, get_sql_query(initial_response), st.session_state.relevant_column, st.session_state.critiquer_chat, initial_response)
            
            add_markdown(f"Verified Query: {st.session_state.critique_response}", "assistant")
            st.session_state.initial = False
            st.rerun()
            
            #add and execute button 
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Execute"):
            # sql_query = get_sql_query(st.session_state.critique_response)
            bigquery_json = query_to_dataframe(st.session_state.sql_query)
            if bigquery_json['response'] == 'error':
                st.session_state.error = bigquery_json['error']
                add_markdown(f"Error: {st.session_state.error}", "assistant")
                add_markdown("Above is the result of Execution\n Now u can Ask AI for rectifications if needed or can go to visualisation mode","assistant")

                st.rerun()
                

            else:
                st.session_state.error = None
                dataframe = bigquery_json['dataframe']
                st.session_state.data_frame = dataframe
                st.chat_message("assistant").dataframe(dataframe)
                st.session_state.messages.append({"role": "bigquery", "content": dataframe.to_dict()})
                add_markdown("Above is the result of Execution\n Now u can Ask AI for rectifications if needed or can go to visualisation mode","assistant")

                st.rerun()

    with col2:
        if st.button("Ask/Rectify"):
            prompt = f"These are my suggestions: {prompt}"
            if st.session_state.error is not None:
                prompt = f"These error occured while executing { st.session_state.error }" +prompt

            
            st.session_state.critique_response = st.session_state.critiquer_chat.invoke({"input": prompt},{"configurable": {"session_id": "unused"}}).content
            add_markdown(prompt, "user")
            add_markdown(st.session_state.critique_response, "assistant")
            st.rerun()
    if get_sql_query(st.session_state.critique_response) != None and get_sql_query(st.session_state.critique_response) != st.session_state.sql_query:
        st.session_state.sql_query = get_sql_query(st.session_state.critique_response)
        st.rerun()
elif option == "Visualising":
    if st.session_state.data_frame is not None and st.button("Visualise"):
        # st.write("Visualising option selected. Implement your visualization logic here.")
        chart_url,logs = main(st.session_state.data_frame, prompt)
        add_markdown(logs, "assistant")
        add_markdown(chart_url, "assistant")
        st.rerun()



# Display the current relevant column if it exists
# if 'relevant_column' in st.session_state:
#     st.write(f"Current relevant column: {st.session_state.relevant_column}")

# Reset button
# if st.button("Reset"):
#     st.session_state.state = 'initial'
#     if 'relevant_column' in st.session_state:
#         del st.session_state.relevant_column
#     st.experimental_rerun()
