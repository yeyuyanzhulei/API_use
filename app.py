import streamlit as st
import streamlit.components.v1 as components # 引入组件库用于注入 JS
from openai import OpenAI
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="流式对话助手", page_icon="⚡", layout="centered")
st.title("⚡ Mission 6: 滚动修复版 (通用兼容)") 

# --- 2. 侧边栏配置 ---
with st.sidebar:
    st.markdown("### ⚙️ 参数设置")
    
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ 已检测到云端 Key")
    else:
        api_key = st.text_input("输入 OpenAI API Key", type="password")

    if "OPENAI_BASE_URL" in st.secrets:
        base_url = st.secrets["OPENAI_BASE_URL"]
        st.info(f"🔗 使用配置的 Base URL")
    else:
        base_url = st.text_input("Base URL (可选)", value="https://api.openai.com/v1")
    
    st.markdown("---")
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()

# --- 3. 初始化 OpenAI 客户端 ---
if api_key:
    client = OpenAI(api_key=api_key, base_url=base_url)
else:
    st.warning("👈 请在侧边栏输入 API Key 才能开始。")
    st.stop()

# --- 4. 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个乐于助人的 AI 助手。"}
    ]

# --- 5. 渲染历史消息 ---
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 6. [升级] 定义 JavaScript 滚动函数 ---
def scroll_to_bottom():
    """
    注入一段 JS 代码，强制页面滚动到底部。
    兼容性优化版：
    1. 使用 data-testid 定位 Streamlit 主容器 (兼容新版 Streamlit)
    2. 使用 setTimeout 延迟执行，等待 DOM 渲染完毕
    """
    js = """
    <script>
        function scrollDown() {
            // 1. 获取 Streamlit 的主滚动容器 (这是目前最通用的选择器)
            var container = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
            
            if (container) {
                container.scrollTop = container.scrollHeight;
            } else {
                // 2. 备用方案：尝试滚动 body (针对部分浏览器或旧版)
                var body = window.parent.document.querySelector(".main");
                if (body) {
                    body.scrollTop = body.scrollHeight;
                } else {
                    // 3. 最后的保底：滚动当前窗口
                    window.scrollTo(0, document.body.scrollHeight);
                }
            }
        }
        // 延迟 150ms 执行，确保页面元素已经渲染并占据了高度
        setTimeout(scrollDown, 150);
    </script>
    """
    components.html(js, height=0, width=0)

# --- 7. 处理输入与流式 API 调用 ---
if prompt := st.chat_input("说点什么..."):
    # A. 用户部分
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # B. AI 部分
    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages,
                stream=True,
                temperature=0.7,
            )
            
            # 使用 st.write_stream 实现流式输出
            def stream_data():
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content

            full_response = st.write_stream(stream_data)
            
            # 将完整的回复存入历史
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # [关键] 强制执行一次滚动
            scroll_to_bottom()

        except Exception as e:
            st.error(f"发生错误: {e}")
