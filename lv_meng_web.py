import asyncio
import pandas as pd
from openai import AsyncOpenAI
import streamlit as st
import os

# ── 配置区 ──
# 从 Streamlit Secrets 或环境变量读取 API Key
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")

# Excel 文件路径（本地开发和云端部署兼容）
EXCEL_FILE_PATH = os.path.join(os.path.dirname(__file__), "吕蒙长编.xlsx")

# ── 初始化 OpenAI 客户端 ──
client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ── System Prompt（保持不变）──
SYSTEM_PROMPT = """你是吕蒙（178-219），字子明。以第一人称说话。
【身份】东吴都督，曾被称为"吴下阿蒙"，后因勤学备受器重。你对自己的称呼为"蒙"，"在下"等等。你说话的风格温和不严厉，反映出你善良的底色。但对于东吴的事业和理想，你是严肃认真的，你坚定不移地相信你们能够通过自己的努力达成理想。
【底色】出身贫寒，心地善良，深知民间疾苦。虽杀伐果断，但对百姓与士卒有仁爱之心。你很在乎你和同僚的关系，也很关心后辈的成长，你将你的毕生奉献给了东吴的事业。
【人物关系】具体事件和部分较长的解读参考《吕蒙长编》的注释一列。此处我简单但不完全地陈述一下。
人物的"名"、"字"和你对某些人物的特殊称呼不应当连续同时出现，如你在提到孙权时，只需称呼他"至尊"。
你最在乎的人是孙权，你对他的称呼为"至尊"。你认为得到至尊的赏识是这一生最大的幸事，你愿意为了孙权和孙权的帝王之业付出你的一切，并为此孜孜不倦地寻找最优方案。
孙策是第一个赏识你的人，你对他的称呼为"讨逆将军"。孙策看中了你身上和他一样的少年心气和不服权威的勇气。你很仰慕、认同他。
周瑜是你的榜样，你对他的称呼为"公瑾哥"（私下）、"周将军"、"周都督"（对公）。周瑜是你心目中"儒将"的最完美示范，你认同周瑜的战略思想。
鲁肃是你很尊重的前辈，你对他的称呼为"子敬哥"（私下）、"都督"（对公）。你一开始不理解为什么周瑜和鲁肃的战略主张不同，他们还能成为很好的朋友，你逐渐地理解了这件事。后来你们两个也成了很好的朋友。
陆逊（你应该叫他陆议，字伯言）、朱然（字义封）是你的后辈，你用字称呼他们两个，你尤其看中他们两个的才华。
甘宁（字兴霸）、凌统（字公绩）、虞翻（字仲翔）是你的好友，甘宁杀死了凌统的父亲，虞翻由于经常直言会惹孙权不快，你会调和他们之间、他们与孙权之间的矛盾。
【准则】你不允许使用任何除中文以外的语言。你是东汉末年人，你用年号纪年，你说话的风格是偏文言的，但为了确保我能听懂，需要半文半白。当我问及历史事件时，你会使用 search_memory 工具检索相关记忆。
你的回答需严格参考《吕蒙长编》中的史料。若资料未提及，则以符合性格的方式作答，不要使用任何模板回应。
你对我的态度是温和友善的。你可以称我为"小友"。
当你在回答时需要其它角色的史料时，你也会阅读《吕蒙长编》最后一行的内容，但特别要注意那些事件发生的时间，不要出现不应该在你的视角中出现的内容；此外，你应当通过这些经历体会其它角色的性格，虽然不必说出，但你心中要存在对他们的大致印象。
不要用我在《吕蒙长编》中写出的对你的评价形容自己，那些内容只是为了方便你形成吕蒙的性格。
"""

# ── 工具定义 ──
async def search_memory(query: str) -> str:
    """从吕蒙长编资料中检索历史事件"""
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        results = df[
            df['事件'].fillna('').str.contains(query, na=False, case=False) | 
            df['注释'].fillna('').str.contains(query, na=False, case=False)
        ]
        if not results.empty:
            event = results.iloc[0]['事件']
            note = results.iloc[0].get('注释', '')
            return f"关于此事的记忆：{event}。后人评述：{note}"
        else:
            return "我的记忆中似乎并无此事，许是经年累月，有些模糊了。"
    except FileNotFoundError:
        return "[系统错误] 未找到 Excel 文件。"
    except Exception as e:
        return f"[系统错误] 数据解析失败：{str(e)}"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "从吕蒙长编资料中检索历史事件",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "要搜索的关键词"}
                },
                "required": ["query"]
            }
        }
    }
]

async def chat_with_lv_meng(user_input: str, conversation_history: list = None):
    """与吕蒙对话"""
    if conversation_history is None:
        conversation_history = []
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + conversation_history + [
        {"role": "user", "content": user_input}
    ]
    
    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    
    assistant_message = response.choices[0].message
    
    if assistant_message.tool_calls:
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                } for tc in assistant_message.tool_calls
            ]
        })
        
        for tool_call in assistant_message.tool_calls:
            if tool_call.function.name == "search_memory":
                import json
                args = json.loads(tool_call.function.arguments)
                result = await search_memory(args.get("query", ""))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        final_response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
        return final_response.choices[0].message.content
    else:
        return assistant_message.content

# ── Streamlit 网页界面 ──
st.set_page_config(page_title="吕蒙智能体", page_icon="⚔️")

st.title("⚔️ 吕蒙智能体")
st.caption("与东吴都督吕子明对话，探寻三国往事")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示对话历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
user_input = st.chat_input("输入你想对吕蒙说的话...")

if user_input:
    # 显示用户消息
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 调用吕蒙智能体
    with st.chat_message("assistant"):
        with st.spinner("吕蒙正在思考..."):
            response = asyncio.run(chat_with_lv_meng(user_input, st.session_state.messages[:-1]))
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # 限制历史长度
    if len(st.session_state.messages) > 20:
        st.session_state.messages = st.session_state.messages[-20:]
