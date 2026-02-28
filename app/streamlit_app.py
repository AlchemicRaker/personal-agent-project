import streamlit as st
from app.agent import run_agent

st.set_page_config(page_title="Personal Agent", layout="wide")

if "repo" not in st.session_state:
    st.session_state.repo = None
if "temp_prompt" not in st.session_state:
    st.session_state.temp_prompt = ""

st.title("🤖 Personal Agent System")

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Controls")
    task = st.text_area("Task", height=100, placeholder="e.g., improve the app")
    repo = st.text_input(
        "GitHub Repo", placeholder="owner/repo", value=st.session_state.repo or ""
    )
    if st.button("🚀 Run Agent"):
        st.session_state.repo = repo
        st.session_state.temp_prompt = ""
        st.rerun()

    if st.session_state.temp_prompt:
        task = st.session_state.temp_prompt

    st.subheader("File Browser")
    if st.button("Refresh"):
        st.cache_data.clear()

    @st.cache_data
    def get_files():
        from app.tools import list_dir

        return list_dir(".")

    if st.button("List Files"):
        files = get_files()
        st.text(files)

    search_filter = st.text_input("Search/Filter Files")
    st.caption("For subdirs, trigger agent with list_dir('subdir') in task")

    # New: Search Repo Issues button
    if st.button("🔍 Search Repo Issues") and st.session_state.repo:
        st.session_state.temp_prompt = f"Use list_issues('{st.session_state.repo}') tool and summarize open issues.\\n**PLAN COMPLETE**"
        st.rerun()

with col2:
    if task:
        with st.spinner("Running agent..."):
            result = run_agent(task, repo=st.session_state.repo)
            st.markdown(result)
