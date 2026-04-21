import os
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

openrouter = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key)

MODELS = {
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct",
    "Llama 3.2 3B": "meta-llama/llama-3.2-3b-instruct",
    "Gemini 2.5 Flash": "google/gemini-2.5-flash",
    "Claude Sonnet 4": "anthropic/claude-sonnet-4",
    "GPT-4.1 Mini": "openai/gpt-4.1-mini",
    "DeepSeek V3.1": "deepseek/deepseek-chat-v3.1",
}


def get_openrouter_credits():
    """Fetch current credit balance from OpenRouter."""
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {openrouter_api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        balance = data.get("limit_remaining")
        usage = data.get("usage")
        limit = data.get("limit")
        return {"balance": balance, "usage": usage, "limit": limit}
    except Exception as e:
        return {"error": str(e)}


def get_generation_cost(generation_id):
    """Fetch the cost of a specific generation from OpenRouter."""
    try:
        resp = requests.get(
            f"https://openrouter.ai/api/v1/generation?id={generation_id}",
            headers={"Authorization": f"Bearer {openrouter_api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "total_cost": float(data.get("total_cost", 0)),
            "tokens_prompt": data.get("tokens_prompt", 0),
            "tokens_completion": data.get("tokens_completion", 0),
        }
    except Exception:
        return None


st.set_page_config(page_title="LLM Query", page_icon="🤖")
st.title("🤖 LLM Query")
st.caption("Ask any question and choose which model answers it")

# --- Sidebar: Credits & Session Cost ---
with st.sidebar:
    st.header("💰 OpenRouter Credits")
    credits = get_openrouter_credits()
    if "error" in credits:
        st.error(f"Could not fetch credits: {credits['error']}")
    else:
        if credits["limit"] is not None:
            st.metric("Remaining Balance", f"${credits['balance']:.4f}")
            st.metric("Total Used (all time)", f"${credits['usage']:.4f}")
        else:
            st.info("Unlimited plan (no credit limit set)")

    st.divider()
    st.header("📊 Session Usage")
    if "session_costs" not in st.session_state:
        st.session_state.session_costs = []
    if "session_total" not in st.session_state:
        st.session_state.session_total = 0.0

    st.metric("Session Total", f"${st.session_state.session_total:.6f}")
    st.metric("Queries This Session", len(st.session_state.session_costs))

    if st.session_state.session_costs:
        with st.expander("Call details"):
            for i, entry in enumerate(st.session_state.session_costs, 1):
                st.markdown(
                    f"**{i}.** {entry['model']} — "
                    f"${entry['cost']:.6f} "
                    f"({entry['tokens_prompt']}→{entry['tokens_completion']} tokens)"
                )

selected_model = st.selectbox("Select a model", list(MODELS.keys()))

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Querying {selected_model}..."):
            try:
                response = openrouter.chat.completions.create(
                    model=MODELS[selected_model],
                    messages=st.session_state.messages,
                )
                reply = response.choices[0].message.content

                # Track cost via generation ID
                gen_id = response.id
                import time
                time.sleep(1)  # brief delay for OpenRouter to finalize cost
                cost_info = get_generation_cost(gen_id)
                if cost_info:
                    st.session_state.session_costs.append({
                        "model": selected_model,
                        "cost": cost_info["total_cost"],
                        "tokens_prompt": cost_info["tokens_prompt"],
                        "tokens_completion": cost_info["tokens_completion"],
                    })
                    st.session_state.session_total += cost_info["total_cost"]

            except Exception as e:
                reply = f"⚠️ Error from {selected_model}: {e}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
