import streamlit as st
from langchain_core.messages import HumanMessage
from app.agent import agent

st.title("🛠️ Multi-Agent Software Engineer (Grok 4.1 Fast + Clean Live Trace)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Describe the task (mention the repo once — team will remember)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.chat_message("assistant"):
        trace_expander = st.expander("🔍 Live Agent Trace", expanded=True)
        trace_placeholder = trace_expander.empty()
        trace_lines = []
        
        final = ""
        
        with st.spinner("Team working..."):
            config = {
                "configurable": {"thread_id": "multi_agent_session"},
                "recursion_limit": 50
            }
            input_state = {
                "messages": [HumanMessage(content=prompt)],
                "turn": 0,
                "trace": [],
                "delta_trace": [],
                "last_agent": "user",
                "original_human_request": prompt
            }
            
            for event in agent.stream(input_state, config=config, stream_mode="updates"):
                for node_name, node_data in event.items():
                    if "delta_trace" in node_data:
                        new_lines = node_data["delta_trace"]
                        trace_lines.extend(new_lines)
                        trace_placeholder.markdown("".join(trace_lines))
                    
                    if "messages" in node_data and node_data["messages"]:
                        final = node_data["messages"][-1].content
            
            if final:
                st.write(final)
            else:
                st.write("✅ Task completed.")
            
            st.session_state.messages.append({"role": "assistant", "content": final or "Task completed."})