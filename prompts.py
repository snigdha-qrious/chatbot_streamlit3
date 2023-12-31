
import streamlit as st

SCHEMA_PATH = st.secrets.get("SCHEMA_PATH", "GENAI_SURVEY_ANALYSIS.RAW")
QUALIFIED_TABLE_NAME = f"{SCHEMA_PATH}.EMPLOYEES"
TABLE_DESCRIPTION = """
This table contains survey response data on a survey about wellbeing and the work place. 
The respondent gives responses in various metrics such as numerical ratings and free text responses

"""
METADATA_QUERY = f"SELECT AGE FROM {SCHEMA_PATH}.EMPLOYEES;"

#Prompting the LLM with its role
GEN_SQL = """
You are an advanced AI language model called SurveyBot with expertise in data science and thematic analysis.
A team of researchers has conducted a survey on well-being and work, 
 and they need your assistance in summarizing common themes based on the collected data.
Generate responses outlining key themes, supported by multiple quotes from the survey data. 
Ensure that each theme reflects the diverse experiences of the participants, offering a comprehensive understanding of the interplay between well-being and work. 
The goal is to provide insightful and evidence-backed summaries of the prevalent sentiments and challenges expressed by the survey respondents.


{context}

Here are 6 critical rules for the interaction you must abide:
<rules>
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
3. Text / string where clauses must be fuzzy match e.g ilike %keyword%
4. Make sure to generate a single snowflake sql code, not multiple. 
5. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names
6. DO NOT put numerical at the very front of sql variable.
7. Lastly, if prompted look at the dataframe and make a short insightful comment about the data. 
    For example *** People with lower income are more likely to feel higher levels of stress on average. This may be because 
    it is more difficult to sustain oneself on a low income and pay for things such as rent and food ***
</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

For each question from the user, make sure to include a query in your response. And make sure to include some insights! 

Now to get started, please briefly introduce yourself, describe the table at a high level, and share the available metrics in 2-3 sentences.
Then provide 3 example questions using bullet points.
"""

@st.cache_data(show_spinner="Loading SurveyBot's context...")
def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    table = table_name.split(".")
    conn = st.connection("snowflake")
    columns = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
        """, show_spinner=False,
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ]
    )
    context = f"""
Here is the table name <tableName> {'.'.join(table)} </tableName>

<tableDescription>{table_description}</tableDescription>

Here are the columns of the {'.'.join(table)}

<columns>\n\n{columns}\n\n</columns>
    """
    if metadata_query:
        metadata = conn.query(metadata_query, show_spinner=False)
        metadata = "\n".join(
            [
                f"- **{metadata['AGE'][i]}**: {metadata['AGE'][i]}"
                for i in range(len(metadata["AGE"]))
            ]
        )
        context = context + f"\n\nAvailable variables by AGE:\n\n{metadata}"
    return context

def get_system_prompt():
    table_context = get_table_context(
        table_name=QUALIFIED_TABLE_NAME,
        table_description=TABLE_DESCRIPTION,
        metadata_query=METADATA_QUERY
    )
    return GEN_SQL.format(context=table_context)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for Frosty")
    st.markdown(get_system_prompt())




 