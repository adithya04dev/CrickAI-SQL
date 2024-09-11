# AI-Assisted SQL Engine for Cricket Data (Cursor for Cricket Analytics).


## About

This project features an intuitive AI-assisted SQL engine designed specifically for cricket data analysis.    
The engine simplifies the calculation of complex and granular statistics, enhancing the way cricket analytics are performed.    
In layman terms its just chatgpt with a sql query executing capabilty in google bigquery with searching agent.   
More and complex queries/granular stats can be calculated by a human with basic sql,cricket knowledge as he can iterate/give feedback based on queries or the result generated on queries.Thus code business(i.e Cricket) logic, not plumbing.  
    
   
   
Similar project to this project i had mad sql assitant using langgraph to itself generate stats/results  following certain steps/stages iteratively rather than than chat based.   
Link: https://github.com/adithya04dev/advanced-cricket-stats

## Technologies/Packages Used

- **Langchain**: For chat based component of this sytem,that can respond based on user suggestions.And also using langchain tool calling agent(specifically ReAct) for preprocessing step in inital phase
- **SQL**: For data querying.
- **Bigquery**: Backend for executing sql queries.

