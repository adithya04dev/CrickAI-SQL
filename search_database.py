
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools import tool
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
import time
import requests
import re
import os
import ast
import requests
import os
def initialise_agent(model='gpt-4o-mini'):
    if model=='sonnet':
        llm = ChatAnthropic(temperature=0, model_name="claude-3-sonnet-20240229")
    elif model =='gpt-4o-mini':
        llm = ChatOpenAI(model="gpt-4o-mini")
    else:
        llm = ChatGroq(model='llama-3.1-70b-versatile')  
    @tool
    def get_value_from_column(list1:str) -> str:
        """
        This function retrieves the specific value present in database column_name that is most similar to the search_value.
        input: 2D list of lists  with the format shown below.
        ([[column_name1,search_value1], [column_name2,search_value2], [column_name3,search_value3]]

        """
        def get_value_from_column1(list1:list) -> str:



            column_name=list1[0]
            search_value=list1[1]
            if column_name not in ['venue', 'series_name',  'tournament_name',   'match_type',  'team_bat',  'team_bowl',  
            'bowler_type', 'batter','bowler', 'bowler_kind','batter_hand']:
                return """Can only  search for this columns ['venue', 'series_name',  'tournament_name',   'match_type',  'team_bat',  'team_bowl',  
            'bowler_type', 'batter','bowler', 'bowler_kind','batter_hand']  in database"""
            if column_name=='batter' or column_name=='bowler':
                URL = "https://api.bing.microsoft.com/v7.0/search"

                HEADERS = {"Ocp-Apim-Subscription-Key": os.environ.get('BING_API_KEY')}
                PARAMS = {
                    "q": search_value + ' cricinfo ',
                    "count": 10,
                    "offset": 0,
                    "mkt": "en-US",
                    "safeSearch": "Moderate"
                }

                response = requests.get(URL, headers=HEADERS, params=PARAMS)
                results = response.json()
                flag = False

                for result in results["webPages"]["value"]:
                    url = result["url"]
                    if 'https://www.espncricinfo.com/cricketers/' in url:
                        flag = True
                        break

                if flag is False:
                    return "Player not found Leave this column's value  empty."

                parts = url.split("-")
                id = parts[-1]
                res = requests.get('http://core.espnuk.org/v2/sports/cricket/athletes/' + str(id))
                name = res.json()['displayName']
                return str(name)
            else:

            # Load FAISS index for specified column
                embeddings = OpenAIEmbeddings(
                    model='text-embedding-ada-002'
                )
                vector_db_path = os.path.join(os.getcwd(), 'vector_databases')
                
                db = FAISS.load_local(os.path.join(vector_db_path, column_name), embeddings, allow_dangerous_deserialization=True)

                # Create document retriever and find most relevant document to player name
                retriever = db.as_retriever(search_type='mmr', search_kwargs={'k': 5, 'lambda_mult': 1})
                matched_value = retriever.get_relevant_documents(search_value)
                res=[]
                for i in matched_value:
                    res.append(i.page_content)
                return str(res)

        # print(type(list1))
        # print(list1)


        list_str = re.search(r'\[.*\]', list1)
        if list_str:
            list_str = list_str.group()
        else:
            return "Invalid input format: No list found"
        list1 = ast.literal_eval(list_str)
        # list1 = eval(list_str)
        # list1=eval(list1)

        # print(type(list1))
        # print(list1)
        l=[]
        for list2 in list1:
            if len(list2)!=2:
                print("list2",list2)
                return "Inputs are not in correct format."
                
            res=get_value_from_column1(list2)
            l.append(list2+[res])
        print(l)
        return l 
        
    @tool
    def add_2_numbers(a,b) :
        """ 
        This function adds 2 numbers.
      """
        return a+b
        

    tools = [get_value_from_column,add_2_numbers]


    prompt = PromptTemplate.from_template(
    """
  
    You are an intelligent agent designed to assist in generating SQL queries(specifically filtering dataset i.e in where clause) by processing  based on user query.


    You will be given a user query,in which users may provide vague references to  names, such as batter,bowler,bowler_type,
    batter_hand,bowler_kind,match_type,team_bat,team_bowl,tournament_name,series_name,venue in a cricket database,
    but directly using those names/values of that column for filtering the dataset in sql may not work always.
    -so you need to search for the exact name of that column in the database using the tool get_value_from_column ( except for bowler_kind,batter_hand,match_type which have only few values and i have provided below  you with the list of those values).


    Thus you need  to preprocess these user queries by searching in the database using the tool get_value_from_column and 
    then return the final answer.


    Remember:
    -Even if in the query users mentioned other columns other than the ones mentioned above,you need to ignore them.    




    Important important columns,and its values in the database are:
    columns that has many distinct values are:
    - venue 
    - series_name
    - tournament_name
    - batter
    - bowler
    - team_bat
    - team_bowl

    you may need to search for values in above columns in database.
    info about tournament_name and series_name:

        -tournament_name column  mentions the  general name of series/event but the series_name column
        specifies both the series/event with a season/year (i.e the series_name=tournament_name +season/year).  
        -thus for queries involving just the name of event  can use directly the tournament_name,if specifically
        mentioned the event/tournament with a season/year  can use series_name.




    columns that has few distinct values and its values are known to us are:
    - bowler_kind: ['pace bowler','spin bowler'] 
    - batter_hand :['Right Hand Batter','Left Hand Batter'] 
    - match_type : ['ODI','MDM','Test','IT20','T20','ODM'] 
    - bowler_type : ['RAP'(means  right arm pace),'OB'(means off break),'LWS'(means left wrist spin),
    'LAP'(means left arm pace),'LB'(means left arm break),'SLA'(means slow left arm)
    ] 
    you many need not to search in database for these columns as their values are known to us.




    ---------------------
    You have access to the following tools:

    {tools}
    ---
    Tool names:
    {tool_names}
    ---------------------------------------------------------------------------------------------------

    Use the following format:

    User Query: {input}

    Thought: Analyze the user query and determine what information needs to be retrieved from the database. 
    Consider which columns are relevant and what search terms to use.

    Action: get_value_from_column

    Action Input: [['column_name1', 'search_value1'],['column_name2', 'search_value2'], ...]

    Observation: result of action.


    (Repeat the Thought/Action/Action Input/Observation steps N times, but dont repeat the same action again and again)

    After you have done the above steps N times,

    -understand/reason which values found in database are most relevant and accurate for filtering the dataset for user query. 



    Thought: Analyze the observations from all actions. 


    Final Answer: Provide  Final Answer that includes
    -The relevant column names,appropriate values based on results of actions found for each column. from the database.



    -But Dont include  sql query.



    Begin!

    User Query: {input}
    Thought: {agent_scratchpad}


    """
    )


    agent = create_react_agent(llm, tools, prompt)    
    # agent = create_tool_calling_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False,handle_parsing_errors=True,return_intermediate_steps=True) 
    
    return agent_executor 

agent=initialise_agent()

def parse_search_agent_response(result):
    intermediate_output=""
    # print("in parse_search_agent_response",result)
    for step in result['intermediate_steps']:
        intermediate_output += f"{step[0].log } \n"  
        for i in step[1]:
            intermediate_output += f" {i} \n \n"
    # { result['input']}\n   
    string=f" {intermediate_output}  \n {result['output']}  \n   "
    return result,string

def search(user_query,model='gpt-4o-mini',stream=True):

    global agent

    result=agent.invoke({"input": user_query})

    return parse_search_agent_response(result)
