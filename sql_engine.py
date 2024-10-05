from langchain_openai import ChatOpenAI
import time 
import pandas 
import re
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
task=""" 
I have a ball by ball  database of cricket matches named bbbdata.ballsnew_2406 in bigquery.

I want to write  SQL query for this user query:  {user_query}



Schema and info about columns of  Database:  

{schema}
Some of sample queries for calculating metrics on this database are:

{sample_codes}

-More info about exact column names and values from userquery present in Datbase: {res_gem}.
 Use only  this to filter dataset i.e in where of sql query.


Suggestions:
1.Use backslash as delimeter before ' is present in sql query.

 """

with open('schema.txt', 'r') as file:
    schema = file.read()
with open('sample_codes.txt', 'r') as file:
    sample_codes = file.read()
verifier_system_prompt = f"""Remeber this as Context:
I have a ball by ball  database of cricket matches.
The schema of the database is as follows:
{schema}
The sample queries for calculating metrics on this database are:
{sample_codes}

I will give u task later based on this database. Understand and remember this context.

"""


critique = """


My assistant had wrote this sql query for finding the answer for this user query: {user_query}.
His SQL Query: {sql_query}.

Can u check/verify step by step if he committed any logical error in writing sql query.
-verify if he has aggregated the data correctly to obtain the metrics.





And finally return the final sql query.


"""

def critiquer_chat():
    """ return a chat object of critiquer """
    # critiquer_llm=ChatOpenAI(model='gpt-4o-mini')
    critiquer_llm=ChatGoogleGenerativeAI(model="gemini-1.5-pro-002",temperature=0.1)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. Answer all questions to the best of your ability.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

    critiquer_chain = prompt | critiquer_llm
    history=ChatMessageHistory()
    chat = RunnableWithMessageHistory(
        critiquer_chain,
        lambda session_id: history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    result=chat.invoke({"input": verifier_system_prompt},{"configurable": {"session_id": "unused"}})
    return chat



def generate_initial_query(user_query,res_gem,sample_codes=sample_codes):
    """ generate initial vague sql query that needs to iterated on """
    global critique,task
    # llm=ChatOpenAI(model='gpt-4o-mini')
    llm=ChatGoogleGenerativeAI(model="gemini-1.5-flash-002",temperature=0.1)
    f_user_query=task.format(user_query=user_query,res_gem=res_gem,schema=schema,sample_codes=sample_codes)
    model_response=llm.invoke(f_user_query).content 
    model_initial_sql_query = get_sql_query(model_response)
    return model_response


def generate_critique_query(user_query,sql_query,res_gem,critiquer_chat,model_initial_sql_query,sample_codes=sample_codes):
    #pass initial randomly generated sql query to critiquer to verify its correctness..step by step
    critique_prompt=critique.format(user_query=user_query,sql_query=model_initial_sql_query,res_gem=res_gem)        
    critique_response=critiquer_chat.invoke({"input": critique_prompt},{"configurable": {"session_id": "unused"}}).content
    return critique_response






# def coding(json_data):
#     res_gem=json_data['response']
#     user_query=json_data['query']
#     f=json_data['f']

#     remarks=user_query
#     global n,critique
#     n+=1

#     #if after 4 iterations no valid dataframe is obtained as result then return remarks.
#     if n>7:
#         remarks="Cannot be processed further. Simplify the Quey and try again."
#         return [remarks,"error"]
    


#     #if a valid dataframe is obtained as result then return ask user for suggestions for sql query to be improved or else return the result    
#     if type(f)==pandas.core.frame.DataFrame:
#         print("Result:\n")
#         print(f)
#         s=input("Are u satisfied with the result or want to give any suggestion for the sql query to be improved ? ")

#         if s=='':
#             n=10
#             return [remarks,f]
#         else:
            
#             f=s

      
#     #based on which iteration it is ask ai 
#     ti=time.time()

#     # for first iteration
#     if n==1:
#         f_user_query=task.format(user_query=user_query,res_gem=res_gem,schema=schema,sample_codes=sample_codes)
#         model_response=chat.invoke({"input": f_user_query},{"configurable": {"session_id": "unused"}}).content
#         sql_query = get_sql_query(model_response)
#         print(f"\n\ntime taken for sql query generation for {n}th iteration:  {time.time()-ti} \n")
#         print(f"sql query generated for {n}th iteration by model  :",model_response)




#         critique=critique.format(user_query=user_query,sql_query=sql_query,schema=schema,res_gem=res_gem,sample_codes=sample_codes)        
#         critique_response=chat2.invoke({"input": critique},{"configurable": {"session_id": "unused"}}).content
#         critique_query=get_sql_query(critique_response)
#         print(f"\n\ntime taken for sql query critique for {n} th iteration {time.time()-ti} \n") 

#         print(f"the critiqued response  for {n} th iteration is :",critique_response)
#         time.sleep(3)
#         print("\n\n")
#         if critique_query:
#             sql_query = critique_query


#     #for 2nd to 7th iteration
      
#     else:
#         ti=time.time()


#         failed_prompt=f"""while executing  the  sql query you previously  in bigquery,
#             this error had occurred: {f}.
#             Solve it..

#             """
#         critique_response=chat2.invoke({"input":  failed_prompt},{"configurable": {"session_id": "unused"}}).content
#         critique_query=get_sql_query(critique_response) 
#         if critique_query:
#             sql_query = critique_query
            

#     while True:
#         human_suggestion_for_query=input("Any suggestion do u want to give to critiquer ? ")


#         if human_suggestion_for_query=='':
#             break 
#         elif human_suggestion_for_query=='exit':
#             exit()

#         critique_response=chat2.invoke({"input":  human_suggestion_for_query},{"configurable": {"session_id": "unused"}}).content
#         sql_query=get_sql_query(critique_response)    
#         print(f" critique response for human in loop component : \n {critique_response}")

#         time.sleep(3)
        



#     return [sql_query,f]





def get_sql_query(model_response):

    pattern = r'```sql\n(.*?)```'
    match_sql = re.findall(pattern, model_response, re.DOTALL)
    
    if match_sql:
        sql_query = match_sql[-1].strip()
        # print(sql_query)
        return sql_query
    else:
        return None