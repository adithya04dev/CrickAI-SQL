import openai
import json
import pandas as pd
import re
# Ensure you have your OpenAI API key set up
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# df_columns=''' The extracted columns from the image are:

# * **Batsman**
# * **Innings**
# * **Not Out**
# * **Total Runs**
# * **Total Balls**
# * **Total Outs**
# * **Average**
# * **Strike Rate**
# * **Dot Percentage**
# * **Highest Score**
# * **Fifties**
# * **Hundreds**
# * **Total Fours**
# * **Total Sixes**
# '''
# user_query='''
# bar chart plot for avg of batters
# '''
def get_json(model_response):

    pattern = r'```json\n(.*?)```'
    match_sql = re.findall(pattern, model_response, re.DOTALL)
    
    if match_sql:
        json = match_sql[-1].strip()
        # print(sql_query)
        return json
    else:
        return None
template='''  # chart_configs.py

chart_configs = {
    {
    "type": "bar",
    "data": {
        "x": "",  // Replace with the column name for the x-axis
        "y": ""   // Replace with the column name for the y-axis
    },
    "settings": {
        "orientation": "",  // Options: "vertical", "horizontal"
        "grouped": ,            // Boolean: true or false
        "colors": [ "", "", "" ],  // Optional: Customize colors
        "labels": ,              // Boolean: true or false
        "legend":                // Boolean: true or false
    }
}
,{
    "type": "line",
    "data": {
        "x": "",  // Replace with the column name for the x-axis(should always be single value not list)
        "y": ""   // Replace with the column name for the y-axis(should always be single value not list)    
    },
    "settings": {
        "markers": ,                  // Boolean: true or false
        "line_style": "",          // Options: "solid", "dashed", etc.
        "colors": [ "", "" ],  // Optional: Customize colors
        "labels": ,                    // Boolean: true or false
        "legend":                      // Boolean: true or false
    }
}
{
    "type": "heatmap",
    "data": {
        "x": "",      // Replace with the column name for the x-axis
        "y": "",      // Replace with the column name for the y-axis
        "value": ""     // Replace with the column name for heatmap values
    },
    "settings": {
        "color_scheme": "",  // Example options: "YlGnBu", "RdYlGn", etc.
        "labels": ,                // Boolean: true or false
        "legend":                  // Boolean: true or false
    }
}
{
    "type": "scatter",
    "data": {
        "x": "",     // Replace with the column name for the x-axis
        "y": "",     // Replace with the column name for the y-axis
        "size": "",    // (Optional) Replace with the column name for marker sizes
        "color": ""   // (Optional) Replace with the column name for marker colors
    },
    "settings": {
        "marker_shape": "",  // Options: "circle", "square", etc.
        "marker_size": ,      // Integer value for marker size
        "colors": [ "", "" ],  // Optional: Customize colors
        "labels": ,                 // Boolean: true or false
        "legend":                   // Boolean: true or false
    }
}

'''
def generate_chart_config(user_query: str, df_columns: str) -> dict:
    """
    Generates a Datawrapper chart configuration based on the user query and DataFrame columns.
    
    Args:
        user_query (str): The user's natural language request for a chart.
        df (pd.DataFrame): The DataFrame containing the data.
        
    Returns:
        dict: A dictionary representing the Datawrapper chart configuration.
    """
    # Prepare the list of DataFrame columns
    # df_columns = ', '.join(df.columns.tolist())
    
    # Craft the prompt for the LLM
    prompt = f"""
    I have a df with the following columns: {df_columns}.
    A user has requested the following visualition based on df: "{user_query}".
    Based on it please select any one type of chart that suits from this {template}  and fill the json with the appropriate values.
    """
    # llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    llm=ChatGoogleGenerativeAI(model="gemini-1.5-pro-002", temperature=0.1)
    result=llm.invoke(prompt).content
    # config = json.loads(result)
        
    return result
# print(generate_chart_config(user_query,df_columns))
import requests
import json
import pandas as pd
import time
import re
import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Set your API keys securely


class DatawrapperClient:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.datawrapper.de/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        self.logs=''





    def upload_data(self, chart_id: str, df: pd.DataFrame):
        url = f"{self.base_url}/charts/{chart_id}/data"
        data_csv = df.to_csv(index=False)
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "text/csv"
        }
        response = requests.put(url, headers=headers, data=data_csv.encode('utf-8'))
        if response.status_code in [200, 201]:
            print(f"Data uploaded successfully for chart ID: {chart_id}")
            self.logs+=f"Data uploaded successfully for chart ID: {chart_id}\n"
        else:
            self.logs+=f"Failed to upload data: {response.text}"
            raise Exception(f"Failed to upload data: {response.text}")

    def create_chart(self) -> str:
            url = f"{self.base_url}/charts"
            payload = {
                "title": "New Chart",
                "type": "d3-scatter-plot",  # Set a default type, can be changed later
                "language": "en-US",
                "theme": "datawrapper"
            }
            response = requests.post(url, headers=self.headers, data=json.dumps(payload))
            if response.status_code == 201:
                chart_id = response.json()["id"]
                print(f"Chart created with ID: {chart_id}")
                self.logs+=f"Chart created with ID: {chart_id}\n"
                return chart_id
            else:
                self.logs+=f"Failed to create chart: {response.text}\n"
                raise Exception(f"Failed to create chart: {response.text}")

    def set_chart_type(self, chart_id: str, chart_type: str):
        url = f"{self.base_url}/charts/{chart_id}"
        payload = {"type": chart_type}
        response = requests.patch(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code == 200:
            print(f"Chart type set to {chart_type} for chart ID: {chart_id}")
        else:
            self.logs+=f"Failed to set chart type: {response.text}\n"
            raise Exception(f"Failed to set chart type: {response.text}")

    def apply_settings(self, chart_id: str, settings: dict):
        chart_info = self.get_chart_info(chart_id)
        current_metadata = chart_info.get("metadata", {})
        merged_metadata = self.deep_merge(current_metadata, settings.get("metadata", {}))
        
        url = f"{self.base_url}/charts/{chart_id}"
        payload = {
            "metadata": merged_metadata,
            "title": settings.get("title", chart_info.get("title")),
            "theme": settings.get("theme", chart_info.get("theme")),
            "language": settings.get("language", chart_info.get("language"))
        }
        print(payload)
        response = requests.patch(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code in [200, 201]:
            print(f"Settings applied successfully for chart ID: {chart_id}")
        else:
            self.logs+=f"Failed to apply settings: {response.text}\n"
            raise Exception(f"Failed to apply settings: {response.text}")


    def deep_merge(self, dict1, dict2):
        result = dict1.copy()
        for key, value in dict2.items():
            if isinstance(value, dict):
                result[key] = self.deep_merge(result.get(key, {}), value)
            else:
                result[key] = value
        return result

    def publish_chart(self, chart_id: str) -> str:
        url = f"{self.base_url}/charts/{chart_id}/publish"
        response = requests.post(url, headers=self.headers)
        if response.status_code == 200:
            published_url = response.json().get("url")
            if not published_url:
                for _ in range(5):
                    time.sleep(2)
                    chart_info = self.get_chart_info(chart_id)
                    published_url = chart_info.get("publicUrl")
                    if published_url:
                        break
            print(f"Chart published successfully: {published_url}")
            return published_url
        else:
            self.logs+=f"Failed to publish chart: {response.text}\n"
            raise Exception(f"Failed to publish chart: {response.text}")

    def get_chart_info(self, chart_id: str) -> dict:
        url = f"{self.base_url}/charts/{chart_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            self.logs+=f"Failed to retrieve chart info: {response.text}\n"
            raise Exception(f"Failed to retrieve chart info: {response.text}")
def process_chart_configuration(client: DatawrapperClient, config: dict, df: pd.DataFrame) -> str:
    chart_type_map = {
        "bar": "d3-bars",
        "line": "d3-lines",
        "scatter": "d3-scatter-plot"
    }
    
    chart_type = chart_type_map.get(config["type"])
    if not chart_type:
        raise ValueError(f"Unsupported chart type: {config['type']}")
    
    chart_id = client.create_chart()
    client.set_chart_type(chart_id, chart_type)

    x_axis = config["data"]["x"]
    
    y_axis = config["data"].get("y")
    labels = config["data"].get("labels")
    
    # df_filtered = df[[x_axis, y_axis, labels]] if labels else df[[x_axis, y_axis]]
    df_filtered=df
    client.upload_data(chart_id, df_filtered)

    settings = {
        "metadata": {
            "axes": {
                "x": x_axis

            },
            "visualize": config["settings"]
        },
        "title": config["settings"]["title"],
        "theme": "datawrapper",
        "language": "en-US"
    }
    if y_axis:
        settings["metadata"]["axes"]["y"]=y_axis
    if labels:
        settings["metadata"]["axes"]["labels"]=labels
    
    client.apply_settings(chart_id, settings)
    chart_url = client.publish_chart(chart_id)
    return chart_url
def generate_chart_config(user_query: str, df_columns: str) -> dict:
    template = '''
    {   
        "type": "",  // "bar", "line", or "scatter",
        filtered_rows: [column1,column2,..] //for line plots
        "data": {
            "x": "",  // Column name for x-axis  
            "y": "",  // Column name for y-axis  
            "labels": ""  // Column name for labels (optional)
               

        },
        "settings": {
            "title": "",
            "chart_type": "",  // "d3-bars", "d3-lines", or "d3-scatter-plot"
            "colors": [],
            "opacity": 1,
            "tooltip": {
                "enabled": true,
                "title": "{{ labels }}",
                "body": ""
            },
            "x_axis": {
                "label": "",
                "grid": "on"
            },
            "y_axis": {
                "label": "",
                "grid": "on"
            },
            // Bar chart specific
            "orientation": "vertical",
            "stack_to_100": false,
            "sort_bars": false,
            // Line chart specific
            "interpolation": "linear",
            "connector_lines": true,
            // Scatter plot specific
            "symbol": {
                "shape": "circle",
                "size": 5
            }
        }
    }
    '''

    prompt = f"""
    I have a dataframe with the following columns: {df_columns}.
    A user has requested the following visualization based on the dataframe: "{user_query}".
    Based on this, please fill in the JSON template below with the appropriate values:

    {template}.
    Make sure to specify the correct chart type, data columns, and relevant settings.
    Please provide only the filled JSON without any additional text.



    Regarading line plots ..
    For line plots filtered_rows should be a list of values that should be plotted..and include x-axis valuein data  x..no need for y axis..

    """

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-002", temperature=0.1)
    result = llm.invoke(prompt).content
    
    config_json = get_json(result)
    if config_json:
        config = json.loads(config_json)
        return config
    else:
        raise ValueError("Failed to extract JSON configuration from LLM response.")
def get_json(model_response: str):
    pattern = r'```json\n(.*?)```'
    matches = re.findall(pattern, model_response, re.DOTALL)
    if matches:
        return matches[-1].strip()
    else:
        return None
def main(df,query):
    client = DatawrapperClient(api_token=DATAWRAPPER_API_TOKEN)

    # data = {
    #     "Batsman": ["Player A", "Player B", "Player C", "Player D"],
    #     "Average": [45.2, 38.5, 50.1, 42.3],
    #     "Strike Rate": [130.5, 125.3, 140.2, 128.7],
    #     "Region": ["North", "South", "East", "West"]
    # }
    # df = pd.DataFrame(data)

    # df_columns = '''
    # * Batsman
    # * Average
    # * Strike Rate
    # * Region
    # '''

    # queries = [
    #     "bar chart of average scores for each batsman",
    #     "line chart showing strike rate trends by regions",
    #     "scatter plot comparing average and strike rate"
    # ]
    queries=[query]
    df_columns=df.columns.tolist()

    for query in queries:
        print(f"\nProcessing query: {query}")
        try:
            config = generate_chart_config(query, df_columns)

            if config.get("filtered_rows"):
                df=df[config['filtered_rows']]
            print("Generated Chart Configuration:")
            print(json.dumps(config, indent=4))
            # https://www.datawrapper.de/_/DbTNp/
            chart_url = process_chart_configuration(client, config, df)
            chart_display=f'https://www.datawrapper.de/_/{chart_url.split("/")[-3]}/'
            return chart_display,client.logs
        except Exception as e:
            print(f"Failed to create chart: {e}")
            return "Failed to create chart",client.logs

# main(df,query)
