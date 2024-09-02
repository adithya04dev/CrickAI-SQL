import streamlit as st
import os

from search_database import search
from sql_engine import critiquer_chat, generate_initial_query,generate_critique_query, get_sql_query
from bigquery_engine import query_to_dataframe

# Set the OpenAI API key

st.title("Sql assistant")

# Initialize chat history and other states
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_query" not in st.session_state:
    st.session_state.user_query = None

if "state" not in st.session_state:
    st.session_state.state = 'search'

if "critique_response" not in st.session_state:
    st.session_state.critique_response = None
if 'json_response' not in st.session_state:
    st.session_state.json_response = None
if 'critiquer_chat' not in st.session_state:
    st.session_state.critiquer_chat = critiquer_chat()
if 'error' not in st.session_state:
    st.session_state.error = None
# Display chat messages from history on app rerun

for message in st.session_state.messages:
    if message["role"] == "bigquery":
        st.chat_message("bigquery").dataframe(message["content"])
        
    else:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
if st.checkbox("Click to Search", value=False):
    st.session_state.state = 'search'
# React to user input
if prompt := st.chat_input("What is your question?"):
    # Take a small checkbox for state, set default to search

    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)

    if st.session_state.state == 'search':
        # First iteration
        if st.session_state.user_query is None:
            st.session_state.user_query = prompt
            st.session_state.json_response, string_response = search(st.session_state.user_query)            
            st.chat_message("assistant").markdown(string_response)
            st.session_state.messages.append({"role": "ai", "content": string_response})
        # Subsequent iterations
        else:
            if prompt == 'retry':
                st.session_state.json_response, string_response = search(st.session_state.user_query)
                st.chat_message("assistant").markdown(string_response)
                st.session_state.messages.append({"role": "ai", "content": string_response})

            elif prompt.startswith('new'):
                st.session_state.user_query = prompt[4:]  # Extract new query
                st.session_state.json_response, string_response = search(st.session_state.user_query)
                st.chat_message("assistant").markdown(string_response)
                st.session_state.messages.append({"role": "ai", "content": string_response})
            elif prompt == 'continue':
                searched_values =  st.session_state.json_response['output']

                initial_response = generate_initial_query(st.session_state.user_query, searched_values)              
                st.chat_message("assistant").markdown(initial_response)
                critique_response = generate_critique_query(st.session_state.user_query, get_sql_query(initial_response), searched_values, st.session_state.critiquer_chat, initial_response)
                st.chat_message("assistant").markdown(critique_response)

                st.session_state.messages.append({"role": "ai", "content": initial_response})
                st.session_state.messages.append({"role": "ai", "content": critique_response})
                st.session_state.state = 'critiquer'
                st.session_state.critique_response = critique_response
            else:
                searched_values = prompt
                initial_response = generate_initial_query(st.session_state.user_query, searched_values)              
                st.chat_message("assistant").markdown(initial_response)
                critique_response = generate_critique_query(st.session_state.user_query, get_sql_query(initial_response), searched_values, st.session_state.critiquer_chat, initial_response)
                st.chat_message("assistant").markdown(critique_response)

                st.session_state.messages.append({"role": "ai", "content": initial_response})
                st.session_state.messages.append({"role": "ai", "content": critique_response})
                st.session_state.state = 'critiquer'
                st.session_state.critique_response = critique_response

    elif st.session_state.state == 'critiquer':
        if prompt == 'exe':
            sql_query = get_sql_query(st.session_state.critique_response)
            bigquery_json = query_to_dataframe(sql_query)
            if bigquery_json['response'] == 'error':
                st.session_state.error = bigquery_json['error']
                st.chat_message("assistant").markdown(f"This error occurred while executing the query: {st.session_state.error}")
                st.session_state.messages.append({"role": "ai", "content": f"This error occurred while executing the query: {st.session_state.error}"})
            else:
                st.session_state.error = None
                dataframe = bigquery_json['dataframe']
                st.chat_message("assistant").dataframe(dataframe)
                st.session_state.messages.append({"role": "bigquery", "content": dataframe.to_dict()})
        else:
            prompt = f"These are my suggestions: {prompt}"
            if st.session_state.error is not None:
                prompt = f"These error occured while executing { st.session_state.error }" +prompt

            st.session_state.critique_response = st.session_state.critiquer_chat.invoke({"input": prompt},{"configurable": {"session_id": "unused"}}).content
            st.chat_message("assistant").markdown(st.session_state.critique_response)
            st.session_state.messages.append({"role": "ai", "content": st.session_state.critique_response})

    # Store user input and assistant response in chat history
        