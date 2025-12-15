import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. 頁面設定與初始化 ---
st.set_page_config(page_title="專業排球紀錄表 Pro", layout="wide")

# 初始化 Session State
if 'logs' not in st.session_state:
    st.session_state.logs = pd.DataFrame(columns=['時間', '局數', '隊伍', '背號', '動作類別', '詳細原因', '結果', '目前比分'])

# 紀錄每一局的比分結果 (例如: ["25:23", "20:25"])
if 'set_history' not in st.session_state:
    st.session_state.set_history = []

if 'current_set' not in st.session_state:
    st.session_state.current_set = 1

if 'score_a' not in st.session_state:
    st.session_state.score_a = 0
if 'score_b' not in st.session_state:
    st.session_state.score_b = 0

# --- 2. 側邊欄：設定 ---
st.sidebar.header("⚙️ 比賽設定")
team_a_name = st.sidebar.text_input("A 隊名稱", value="Team A")
team_b_name = st.sidebar.text_input("B 隊名稱", value="Team B")

team_a_roster = st.sidebar.text_area("A 隊球員 (逗號隔開)", value="1, 2, 3, 4, 5, 6, 12, L").split(',')
team_b_roster = st.sidebar.text_area("B 隊球員 (逗號隔開)", value="7, 8, 9, 10, 11, 13, L").split(',')
team_a_players = [x.strip() for x in team_a_roster]
team_b_players = [x.strip() for x in team_b_roster]

# --- 3. 動作定義 (同前) ---
action_map = {
    "攻擊 (Attack)": {
        "扣球得分 (Kill)": ("Self", "得分"), "打手出界 (Touch Out)": ("Self", "得分"), 
        "吊球得分 (Tip Kill)": ("Self", "得分"), "攻擊出界 (Out)": ("Opponent", "失誤"), 
        "攻擊掛網 (Net)": ("Opponent", "失誤"), "被攔死 (Blocked)": ("Opponent", "失誤")
    },
    "發球 (Serve)": {
        "發球得分 (Ace)": ("Self", "得分"), "發球出界 (Out)": ("Opponent", "失誤"), 
        "發球掛網 (Net)": ("Opponent", "失誤"), "8秒違例": ("Opponent", "失誤")
    },
    "攔網 (Block)": {
        "攔網得分 (Kill Block)": ("Self", "得分"), "觸網 (Net Touch)": ("Opponent", "失誤")
    },
    "一般失誤 (Faults)": {
        "連擊 (Double)": ("Opponent", "失誤"), "持球 (Catch)": ("Opponent", "失誤"), 
        "觸網 (Net)": ("Opponent", "失誤"), "越界 (Center Line)": ("Opponent", "失誤"), 
        "輪轉錯誤": ("Opponent", "失誤"), "接發球失誤": ("Opponent", "失誤")
    },
    "其他 (Other)": {
        "自訂": ("Self", "得分") # 預設，會被下方邏輯覆蓋
    }
}

# --- 4. 頂部計分板與局數控制 ---
st.title(f"🏐 {team_a_name} vs {team_b_name}")

# 顯示過去局數的比分
if st.session_state.set_history:
    history_str = " | ".join([f"第{i+1}局: {s}" for i, s in enumerate(st.session_state.set_history)])
    st.info(f"📜 歷史局數比分: {history_str}")

# 計分板
col1, col2, col3 = st.columns([1, 0.8, 1])
with col1:
    st.markdown(f"<h1 style='text-align: center; color: blue;'>{st.session_state.score_a}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>{team_a_name}</h3>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<h4 style='text-align: center;'>第 {st.session_state.current_set} 局</h4>", unsafe_allow_html=True)
    
    # === 功能按鈕區 (撤銷 & 結束本局) ===
    c2_1, c2_2 = st.columns(2)
    with c2_1:
        # 撤銷功能
        if st.button("↩️ 撤銷上一步"):
            if not st.session_state.logs.empty:
                # 1. 抓出最後一筆紀錄
                last_log = st.session_state.logs.iloc[-1]
                
                # 只有當最後一筆紀錄屬於「目前這一局」時才動作，避免跨局刪除出錯
                if last_log['局數'] == st.session_state.current_set:
                    # 2. 判斷要扣誰的分數
                    current_score_str = last_log['目前比分'] # 例如 "12:10"
                    score_parts = current_score_str.split(':')
                    log_score_a = int(score_parts[0])
                    log_score_b = int(score_parts[1])
                    
                    # 簡單邏輯：直接把分數倒退回該筆紀錄「之前」的狀態？
                    # 更好的方法：看那筆紀錄是誰得分，就扣誰分
                    if "得分" in last_log['結果']:
                        # 誰做的動作誰得分
                        if last_log['隊伍'] == team_a_name: st.session_state.score_a -= 1
                        else: st.session_state.score_b -= 1
                    elif "失分" in last_log['結果']:
                        # 誰做的動作誰失誤 -> 對方得分 -> 扣對方分
                        if last_log['隊伍'] == team_a_name: st.session_state.score_b -= 1
                        else: st.session_state.score_a -= 1
                    
                    # 3. 刪除 DataFrame 最後一行
                    st.session_state.logs = st.session_state.logs[:-1]
                    st.rerun()
                else:
                    st.warning("無法撤銷上一局的紀錄！")
            else:
                st.warning("目前沒有紀錄可以撤銷")

    with c2_2:
        # 換局功能
        if st.button("🏁 結束本局"):
            # 記錄這一局的比分
            final_score = f"{st.session_state.score_a}:{st.session_state.score_b}"
            st.session_state.set_history.append(final_score)
            
            # 進入下一局
            st.session_state.current_set += 1
            st.session_state.score_a = 0
            st.session_state.score_b = 0
            st.rerun()

with col3:
    st.markdown(f"<h1 style='text-align: center; color: red;'>{st.session_state.score_b}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>{team_b_name}</h3>", unsafe_allow_html=True)

st.divider()

# --- 5. 紀錄輸入區 ---
st.subheader("📝 紀錄輸入")
input_col1, input_col2, input_col3 = st.columns([1, 1, 1])

with input_col1:
    who_team = st.radio("操作隊伍", [team_a_name, team_b_name], horizontal=True)
    if who_team == team_a_name:
        who_player = st.selectbox("背號", team_a_players, key="p_a")
    else:
        who_player = st.selectbox("背號", team_b_players, key="p_b")

with input_col2:
    category = st.selectbox("動作類別", list(action_map.keys()))
    detail_action = st.selectbox("詳細原因", list(action_map[category].keys()))

with input_col3:
    # 自訂敘述功能
    st.write("自訂選項 (可選)")
    custom_desc = st.text_input("📝 手動輸入原因 (若填寫將覆蓋選單)")
    
    # 手動指定得失分邏輯 (當使用手動輸入原因時，需要指定結果)
    custom_result_type = st.radio("這球結果是？", ["得分 (我方+1)", "失誤 (對方+1)"], horizontal=True)

# 送出按鈕
if st.button("確認送出", type="primary", use_container_width=True):
    
    # --- 邏輯判斷 ---
    # 如果有填寫「自訂原因」，以自訂的為主
    if custom_desc:
        final_reason = custom_desc
        if "得分" in custom_result_type:
            who_gets_point = "Self"
            result_desc = "得分"
        else:
            who_gets_point = "Opponent"
            result_desc = "失分"
    else:
        # 使用選單的邏輯
        final_reason = detail_action
        who_gets_point, result_desc = action_map[category][detail_action]
    
    # --- 分數計算 ---
    if who_team == team_a_name:
        if who_gets_point == "Self":
            st.session_state.score_a += 1
        else:
            st.session_state.score_b += 1
    else: # B隊
        if who_gets_point == "Self":
            st.session_state.score_b += 1
        else:
            st.session_state.score_a += 1

    # --- 寫入紀錄 ---
    new_record = {
        '時間': datetime.now().strftime("%H:%M:%S"),
        '局數': st.session_state.current_set,
        '隊伍': who_team,
        '背號': who_player,
        '動作類別': category if not custom_desc else "自訂",
        '詳細原因': final_reason,
        '結果': f"{result_desc}",
        '目前比分': f"{st.session_state.score_a}:{st.session_state.score_b}"
    }
    
    st.session_state.logs = pd.concat([pd.DataFrame([new_record]), st.session_state.logs], ignore_index=True)
    st.rerun()

# --- 6. 顯示紀錄表 ---
st.divider()
st.subheader(f"📊 第 {st.session_state.current_set} 局 - 紀錄明細")

# 只顯示目前這一局的紀錄
current_set_logs = st.session_state.logs[st.session_state.logs['局數'] == st.session_state.current_set]

def highlight_row(row):
    color = '#ffe6e6' if '失分' in row['結果'] else '#e6ffe6'
    return [f'background-color: {color}' for _ in row]

if not current_set_logs.empty:
    st.dataframe(current_set_logs.style.apply(highlight_row, axis=1), use_container_width=True)
else:
    st.caption("本局尚未開始")

# 下載區
csv = st.session_state.logs.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 下載完整比賽紀錄 (CSV)", csv, "match_log.csv", "text/csv")