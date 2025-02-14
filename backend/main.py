import os
import sys

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)
# Get the directory path of the current file
current_dir_path = os.path.dirname(current_file_path)
# Get the parent directory path
parent_dir_path = os.path.dirname(current_dir_path)
# Add the parent directory path to the sys.path
sys.path.insert(0, parent_dir_path)
# Placeholder for main logic, can include background jobs, scheduled tasks, etc.
import asyncio
import time
import os
import json
import pandas as pd
import dspy
import groq
import litellm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from agents import SQLAgent, error_reasoning_agent, error_fix_agent
from backend.database import SessionLocal
from backend.log import logger
from dotenv import load_dotenv
from backend.config import db_info 

# Load environment variables from .env file
load_dotenv()


class GroqLM(dspy.LM):
    def __init__(self, model="groq/llama3-8b-8192", temperature=0.1):
        super().__init__(model=model)
        self.model = model
        self.temperature = temperature
        self.api_key = os.getenv("GROQ_API_KEY")

    async def generate(self, prompt, max_tokens=256):
        """
        Generate a response using the Groq API asynchronously for better performance.
        """
        try:
            response = await asyncio.to_thread(
                litellm.completion,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except litellm.BadRequestError as e:
            logger.error(f"Bad request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Groq API call: {str(e)}")
            return None


# Update DSPy to use the async `GroqLM`
dspy.configure(lm=GroqLM(model="groq/llama3-8b-8192"))


def clean_llm_response(text):
    """
    Cleans the raw response text from the LLM and extracts the SQL query if present.
    """
    splits = text.split("```")
    if len(splits) == 1:
        return splits[0].replace("sql", "").strip()
    return splits[1].replace("sql", "").strip()


class AgentSystem(dspy.Module):
    """
    Handles the full workflow of generating, executing, and debugging SQL queries.
    """

    def __init__(self, dataset_information, max_retry=3):
        self.max_retry = max_retry
        self.sql_agent = dspy.Predict(SQLAgent)
        self.error_reasoning_agent = dspy.Predict(error_reasoning_agent)
        self.error_fix_agent = dspy.ChainOfThought(error_fix_agent)
        self.dataset_information = dataset_information

    async def execute_query(self, sql_query, session):
        """
        Executes a SQL query safely, handling errors and transactions asynchronously.
        """
        try:
            result = await asyncio.to_thread(session.execute, text(sql_query))
            df = pd.DataFrame(result.fetchall(), columns=[col for col in result.keys()])
            return df
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            session.close()

    async def forward(self, query):
        """
        Processes a user query, generates SQL, executes it, and handles errors asynchronously.
        """
        return_dict = {"response": [], "sql": [], "error_reason": [], "df": []}
        session = SessionLocal()

        try:
            # Wrap the prediction call in asyncio.to_thread to prevent blocking
            response = await asyncio.to_thread(
                self.sql_agent,
                user_query=query,
                dataset_information=self.dataset_information,
                sql_dialect="MySQL",
            )
            return_dict["response"].append(response)

            for attempt in range(self.max_retry):
                sql = clean_llm_response(response.generated_sql)
                return_dict["sql"].append(sql)

                try:
                    df = await self.execute_query(sql, session)
                    return_dict["df"].append(df)
                    if df.empty:
                        raise ValueError("Query returned an empty result set.")
                    break

                except Exception as e:
                    logger.error(f"SQL Execution Error: {e}")
                    error_reason = await asyncio.to_thread(
                        self.error_reasoning_agent,
                        error_message=str(e),
                        incorrect_sql=sql,
                        information=self.dataset_information,
                    )
                    return_dict["error_reason"].append(error_reason.error_fix_reasoning)

                    if "NOT ASKING FOR SQL" in error_reason.error_fix_reasoning:
                        break

                    response = await asyncio.to_thread(
                        self.error_fix_agent,
                        instruction=error_reason.error_fix_reasoning,
                    )
                    return_dict["response"].append(response)

        except Exception as e:
            logger.error(f"Critical failure in query processing: {e}")

        finally:
            session.close()

        return return_dict

    async def rate_limited_request(self, prompt):
        """
        Handles Groq rate limit error and retries with exponential backoff.
        """
        backoff = 1
        while True:
            try:
                return await self.lm.generate(prompt)
            except litellm.RateLimitError:
                logger.warning("Rate limit exceeded, retrying after backoff...")
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff
                if backoff > 60:  # Max backoff of 60 seconds
                    logger.error("Max retries reached, aborting.")
                    break

async def get_sql_query(query: str):
    sql_system = AgentSystem(dataset_information=db_info, max_retry=3)
    try:
        responses = await sql_system.forward(query=query)
        logger.debug(f"sql generated: {responses}")
        return responses
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise

