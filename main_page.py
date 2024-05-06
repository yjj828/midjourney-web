import streamlit as st
import requests
import time
from configs import API_URL, API_SECRET

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "您好，请开始您的创作吧。"}]

for msg in st.session_state.messages:
    if msg["content"][:5] == "https":
        st.chat_message(msg["role"]).image(msg["content"])
    else:
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    headers = {"mj-api-secret": API_SECRET}
    data = {"prompt": f"{prompt}"}
    submission = requests.post(url=f"{API_URL}/mj/submit/imagine",
                             json=data,
                             headers=headers)
    if submission.status_code != 200:
        st.write(f"请求失败：{submission.status_code}")
    else:
        submission = submission.json()
        if submission["code"] not in [1, 21, 22]:
            st.chat_message("assistant").write("❌提交失败，失败请稍后重试")
            st.session_state["messages"].append({"role": "assistant", "content": "❌提交失败，失败请稍后重试"})
        else:
            st.chat_message("assistant").write(
                f"✅提交成功，code:{submission['code']}，task id: {submission['result']}，生成中..."
            )
            task_id = submission["result"]
            task = requests.get(url=f"{API_URL}/mj/task/{task_id}/fetch",
                                headers=headers)
            if task.status_code != 200:
                st.write(f"请求失败：{submission.status_code}")
            else:
                task = task.json()
                progress_hint = st.status(label="")
                bar = st.progress(0)
                while task["status"] not in ["FAILURE", "SUCCESS"]:
                    progress_hint.update(label=f"任务状态：{task['status']}。任务进度：{task['progress']}",
                                         state="running")
                    bar.progress(int(task['progress'][:-1]))
                    time.sleep(5)
                    task = requests.get(url=f"{API_URL}/mj/task/{task_id}/fetch",
                                        headers=headers)
                    if task.status_code != 200:
                        st.write(f"请求失败：{submission.status_code}")
                        break
                    else:
                        task = task.json()
                if "status" in task:
                    if task["status"] == "SUCCESS":
                        progress_hint.update(label=f"任务状态：Complete。任务进度：100%",
                                             state="complete")
                        bar.progress(100)
                        with st.chat_message("assistant"):
                            st.write("生成成功!")
                            st.image(task["imageUrl"])
                        st.session_state["messages"].append({"role": "assistant", "content": "生成成功!"})
                        st.session_state["messages"].append({"role": "assistant", "content": task['imageUrl']})

                    elif task["status"] == "FAILURE":
                        progress_hint.update(label=f"任务状态：{task['status']}。任务进度：{task['progress']}",
                                             state="error")
                        st.chat_message("assistant").write("生成失败!")
                        st.session_state["messages"].append({"role": "assistant", "content": "生成失败!"})
                    else:
                        st.write(task["status"])
                else:
                    pass

