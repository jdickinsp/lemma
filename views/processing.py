from typing import Tuple, List, Any
import streamlit as st
from views.config import (
    DiffData, 
    AnalysisContext,
    ModelConfig
)
from llm_client import LLMType
from chat_client import ChatClient
from db import insert_file

async def process_stream_response(stream: Any, client_type: LLMType, sys_out: Any, key: str) -> None:
    """Process streaming response from the LLM."""
    async for chunk in stream:
        if client_type == LLMType.OPENAI:
            content = chunk.choices[0].delta.content or ""
        elif client_type == LLMType.CLAUDE:
            content = chunk.text
        else:
            content = chunk['message']['content']
        st.session_state[key] += content
        sys_out.markdown(st.session_state[key])

async def generate_analysis(context: AnalysisContext, model_config: ModelConfig) -> str:
    """Generate analysis using the configured LLM."""
    chat = ChatClient(model_config.client_type, model_config.model_name)
    
    patch_content = (context.diffs.contents[context.idx] 
                if context.config.analyze_whole_file 
                else context.patch)  # Use the individual patch passed in context
    
    prompts = chat.prepare_prompts(
        context.config.prompt_input,
        context.config.prompt_template_selected,
        patch_content
    )
    
    if context.config.stream_checked:
        stream = await chat.async_chat_response(prompts)
        key = f"ai_comment_{context.idx}"
        st.session_state[key] = ""
        await process_stream_response(stream, model_config.client_type, context.sys_out, key)
        response = st.session_state[key]
    else:
        response = chat.chat_response(prompts)
    
    return response

def get_patches(diffs: DiffData, is_per_file: bool) -> Tuple[List[str], List[str]]:
    """Get patches based on configuration."""
    if is_per_file:
        return diffs.patches, diffs.file_names
    combined_patch = "\n".join([f"{patch}" for patch in diffs.patches])
    return [combined_patch], ["Combined Files"]

def save_analysis(
    context: AnalysisContext,
    response: str
) -> None:
    """Save the analysis results to the database."""
    code_content = (
        context.diffs.contents[context.idx] 
        if context.config.per_file_analysis 
        else " "
    )
    
    insert_file(
        context.conn,
        context.review_id,
        context.file_name,
        context.patch,
        code_content,
        response
    )
