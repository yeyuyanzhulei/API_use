import streamlit as st
from openai import OpenAI

# 1. 页面设置
st.set_page_config(page_title="智能对话助手", page_icon="💬", layout="wide")
st.title("智能对话助手 💬")

# 2. 侧边栏配置
with st.sidebar:
    st.markdown("### 参数设置")
    # 这里的key默认为空，你可以填入你的key
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ 已检测到云端配置的 API Key")
    else:
        api_key = st.text_input("OpenAI API Key", type="password")
    
    # 如果你使用官方 API，base_url 不需要改。
    # 如果你使用中转服务 (如 OhMyGPT, DeepSeek 等)，请修改这里。
    if "BASE_URL" in st.secrets:
        base_url = st.secrets["BASE_URL"]
        st.success("✅ 已检测到云端配置的 Base URL")
    else:
        base_url = st.text_input("Base URL (可选)", value="https://api.deepseek.com")
    
    st.markdown("---")
    # 增加一个清空历史的按钮，方便测试
    if st.button("清空历史记录"):
        st.session_state.messages = []
        st.rerun()
        
# 3. 初始化 OpenAI 客户端
# 只有当用户输入了 Key 才初始化，否则后续会报错
if api_key:
    client = OpenAI(api_key=api_key, base_url=base_url)
else:
    # 如果没填Key，给个提示并停止运行后续代码
    st.warning("API 错误！！！")
    st.stop()
    
# 4. 初始化
if "messages" not in st.session_state:
    # 可以在这里加一个系统提示词，定义 AI 的人设
    st.session_state.messages = [
        {"role": "system", "content":"你是一个智能AI助手"}
    ]

# 5. 渲染历史消息
for msg in st.session_state.messages:
    # 假如是 system 消息，我们通常不在界面显示
    if msg["role"] == "system":
        continue
    
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
   
   
        
# 6. 处理输入与调用API

if prompt := st.chat_input("有什么可以帮你的？"):
    # A. 用户发消息
    # 1. 存入历史
    st.session_state.messages.append({"role":"user", "content": prompt})
    # 2.界面显示
    with st.chat_message("user"):
        st.write(prompt)
        
    # B. AI 回复
    # 1. 界面显示一个“思考中”的状态
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 关键步骤：调用 API
            # 注意：我们将st.session_state.messages（整个历史）传给了API
            # 这就是“记忆”的来源！
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=st.session_state.messages,
                temperature=0.7,
                stream=True,
            )
            # ai_content = response.choices[0].message.content
            # message_placeholder.markdown(ai_content)
            # 循环处理数据流
            for chunck in response:
                # 检查这个数据块里有没有内容
                if chunck.choices[0].delta.content is not None:
                    # 获取这一小块文本
                    content = chunck.choices[0].delta.content
                    # 拼接到总回复中
                    full_response += content
                    # 实时更新界面显示,加一个光标模拟打字感
                    message_placeholder.markdown(full_response + "▌")
            # 最后把完整回复显示出来，去掉光标
            message_placeholder.markdown(full_response)
                
            # 2. 把 AI 回复存入历史
            st.session_state.messages.append({"role":"assistant", "content": full_response})
        except Exception as e:
            message_placeholder.markdown(f"出错了: {e}")
            
            
            
