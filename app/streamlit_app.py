import streamlit as st
from langchain_core.messages import HumanMessage
from app.agent import agent

st.title("🛠️ Multi-Agent Software Engineer (Grok 4.1 Fast + Debug)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Describe the task (mention the repo once — team will remember)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Team working... (watch Docker logs for live trace)"):
            config = {
                "configurable": {"thread_id": "multi_agent_session"},
                "recursion_limit": 50   # increased safety
            }
            response = agent.invoke(
                {"messages": [HumanMessage(content=prompt)], "turn": 0},
                config=config
            )
            final = response["messages"][-1].content
            st.write(final)
            st.session_state.messages.append({"role": "assistant", "content": final})