import os

import pandas as pd
import tiktoken


from graphrag.config import load_config
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.indexer_adapters import (
    read_indexer_entities,
    read_indexer_covariates,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.query.input.loaders.dfs import (
    store_entity_semantic_embeddings,
)
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.question_gen.local_gen import LocalQuestionGen
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores.lancedb import LanceDBVectorStore
import streamlit as st

config = load_config("./")

INPUT_DIR = "./output"
LANCEDB_URI = f"{INPUT_DIR}/lancedb"

COMMUNITY_REPORT_TABLE = "create_final_community_reports"
ENTITY_TABLE = "create_final_nodes"
ENTITY_EMBEDDING_TABLE = "create_final_entities"
RELATIONSHIP_TABLE = "create_final_relationships"
COVARIATE_TABLE = "create_final_covariates"
TEXT_UNIT_TABLE = "create_final_text_units"
COMMUNITY_LEVEL = 2

@st.cache_resource
def create_search_engine():
    # read nodes table to get community and degree data
    entity_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(
        f"{INPUT_DIR}/{ENTITY_EMBEDDING_TABLE}.parquet"
    )

    entities = read_indexer_entities(entity_df, entity_embedding_df, COMMUNITY_LEVEL)

    # load description embeddings to an in-memory lancedb vectorstore
    # to connect to a remote db, specify url and port values.
    description_embedding_store = LanceDBVectorStore(
        collection_name="entity_description_embeddings",
    )
    description_embedding_store.connect(db_uri=LANCEDB_URI)
    entity_description_embeddings = store_entity_semantic_embeddings(
        entities=entities, vectorstore=description_embedding_store
    )
    relationship_df = pd.read_parquet(f"{INPUT_DIR}/{RELATIONSHIP_TABLE}.parquet")
    relationships = read_indexer_relationships(relationship_df)

    covariate_df = pd.read_parquet(f"{INPUT_DIR}/{COVARIATE_TABLE}.parquet")
    claims = read_indexer_covariates(covariate_df)
    covariates = {"claims": claims}

    report_df = pd.read_parquet(f"{INPUT_DIR}/{COMMUNITY_REPORT_TABLE}.parquet")
    reports = read_indexer_reports(report_df, entity_df, COMMUNITY_LEVEL)

    text_unit_df = pd.read_parquet(f"{INPUT_DIR}/{TEXT_UNIT_TABLE}.parquet")
    text_units = read_indexer_text_units(text_unit_df)

    llm = ChatOpenAI(
        api_key=config.llm.api_key,
        api_type=OpenaiApiType.OpenAI,
        model=config.llm.model,
        max_retries=20,
    )

    token_encoder = tiktoken.get_encoding("cl100k_base")

    text_embedder = OpenAIEmbedding(
        api_key=config.embeddings.llm.api_key,
        api_base=config.embeddings.llm.api_base,
        api_type=OpenaiApiType.OpenAI,
        model=config.embeddings.llm.model,
        deployment_name=config.embeddings.llm.model,
        max_retries=20,
    )
    context_builder = LocalSearchMixedContext(
        community_reports=reports,
        text_units=text_units,
        entities=entities,
        relationships=relationships,
        covariates=covariates,
        entity_text_embeddings=description_embedding_store,
        embedding_vectorstore_key=EntityVectorStoreKey.ID,
        text_embedder=text_embedder,
        token_encoder=token_encoder,
    )
    local_context_params = {
        "text_unit_prop": 0.5,
        "community_prop": 0.1,
        "conversation_history_max_turns": 5,
        "conversation_history_user_turns_only": True,
        "top_k_mapped_entities": 10,
        "top_k_relationships": 10,
        "include_entity_rank": True,
        "include_relationship_weight": True,
        "include_community_rank": False,
        "return_candidate_context": False,
        "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
        "max_tokens": 4000,
    }
    llm_params = {
        "max_tokens": 2_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
        "temperature": 0.0,
    }
    return LocalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        llm_params=llm_params,
        context_builder_params=local_context_params,
        response_type="single paragraph",  # free form text describing the response type and format, can be anything, e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
    )
