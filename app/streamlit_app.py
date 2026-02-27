import streamlit as st
from langchain_core.messages import HumanMessage
from app.agent import agent   # note: absolute import for safety

st.title("🛠️ Local Software Engineer Agent (Grok 4.1 Fast + Memory)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("What should I build/fix? (mention the repo once — I'll remember it)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking (with memory)..."):
            # Only send the new message — MemorySaver handles the full history
            config = {"configurable": {"thread_id": "local_agent_session"}}
            response = agent.invoke(
                {"messages": [HumanMessage(content=prompt)]},
                config=config
            )
            final = response["messages"][-1].content
            st.write(final)
            st.session_state.messages.append({"role": "assistant", "content": final})