"""
AI 聊天 API — SSE 流式响应 + 工具调用（Function Calling）

支持的 AI API：兼容 OpenAI 格式（DeepSeek、OpenAI、Claude 等）
"""
from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.setting import Setting
from models.group import Group
from models.bookmark import Bookmark
from models.todo import Todo
from models.scratch_note import Notebook, Note
from utils.response import success, error
import json
import re
import requests
import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


# ── 工具定义（AI 能调用的操作） ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_bookmark",
            "description": "添加一个网页书签到收藏",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "书签标题"},
                    "url": {"type": "string", "description": "网页链接"},
                    "description": {"type": "string", "description": "书签描述（可选）"},
                    "group_name": {"type": "string", "description": "分组名称，不传则自动归类"},
                },
                "required": ["title", "url"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_bookmarks",
            "description": "搜索收藏的书签",
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["q"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_bookmarks",
            "description": "列出某个分组的所有书签",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_name": {"type": "string", "description": "分组名称，不传则列出全部"},
                },
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_bookmark",
            "description": "删除一个书签",
            "parameters": {
                "type": "object",
                "properties": {
                    "title_or_url": {"type": "string", "description": "书签标题或 URL"},
                },
                "required": ["title_or_url"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_todo",
            "description": "添加待办事项。支持指定日期（date）添加到摸鱼日历，或留空date添加到右侧待办面板。支持设置提醒时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "待办内容"},
                    "label": {"type": "string", "description": "标签（可选）"},
                    "date": {"type": "string", "description": "日期（格式：YYYY-MM-DD）。有值=添加到摸鱼日历对应日期；不传或null=添加到右侧待办栏", "nullable": True},
                    "reminder_at": {"type": "string", "description": "提醒时间（格式：YYYY-MM-DD HH:mm）。如果用户说'明天'、'下周一'等，请先转换为具体日期", "nullable": True},
                },
                "required": ["title"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_todos",
            "description": "列出待办事项",
            "parameters": {"type": "object", "properties": {}},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_todo",
            "description": "切换待办完成/未完成状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "title_contains": {"type": "string", "description": "按标题搜索"},
                },
                "required": ["title_contains"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_todo",
            "description": "删除待办事项",
            "parameters": {
                "type": "object",
                "properties": {
                    "title_contains": {"type": "string", "description": "按标题搜索要删除的待办"},
                },
                "required": ["title_contains"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "在笔记本中创建一条笔记",
            "parameters": {
                "type": "object",
                "properties": {
                    "notebook_title": {"type": "string", "description": "笔记本名称，不传则使用默认笔记本"},
                    "title": {"type": "string", "description": "笔记标题"},
                    "content": {"type": "string", "description": "笔记内容"},
                },
                "required": ["title", "content"],
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_groups",
            "description": "列出所有收藏分组",
            "parameters": {"type": "object", "properties": {}},
        }
    },

    {
        "type": "function",
        "function": {
            "name": "create_group",
            "description": "创建收藏分组",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "分组名称"},
                },
                "required": ["name"],
            }
        }
    },
]


# ── 工具执行器 ──

def _get_ai_config(user_id):
    """读取 AI 设置"""
    setting = Setting.query.filter_by(user_id=user_id).first()
    if not setting:
        return None
    try:
        config = json.loads(setting.layout_config or '{}')
        return {
            'api_url': config.get('ai_api_url', 'https://api.deepseek.com/v1').rstrip('/'),
            'api_key': config.get('ai_api_key', ''),
            'model': config.get('ai_model', 'deepseek-chat'),
            'enabled': config.get('ai_enabled', False),
        }
    except (json.JSONDecodeError, TypeError):
        return None


def execute_tool(user_id, tool_name, args):
    """执行 AI 工具调用，返回结果"""
    try:
        if tool_name == 'add_bookmark':
            title = args.get('title', '')
            url = args.get('url', '')
            desc = args.get('description', '')
            group_name = args.get('group_name', '')
            # 找分组
            if group_name:
                group = Group.query.filter_by(user_id=user_id, name=group_name).first()
                if not group:
                    group = Group(user_id=user_id, name=group_name, sort_order=0)
                    db.session.add(group)
                    db.session.flush()
            else:
                group = Group.query.filter_by(user_id=user_id).order_by(Group.sort_order).first()
                if not group:
                    group = Group(user_id=user_id, name='默认', sort_order=0)
                    db.session.add(group)
                    db.session.flush()
            bm = Bookmark(
                user_id=user_id, group_id=group.id,
                title=title, url=url, description=desc,
                sort_order=0,
            )
            db.session.add(bm)
            db.session.commit()
            return {'success': True, 'message': f'已添加书签「{title}」到分组「{group.name}」'}

        elif tool_name == 'search_bookmarks':
            q = args.get('q', '')
            bms = Bookmark.query.filter(
                Bookmark.user_id == user_id,
                Bookmark.title.ilike(f'%{q}%')
            ).limit(10).all()
            return {'success': True, 'data': [{'title': b.title, 'url': b.url, 'group_id': b.group_id} for b in bms]}

        elif tool_name == 'list_bookmarks':
            group_name = args.get('group_name', '')
            query = Bookmark.query.filter_by(user_id=user_id)
            if group_name:
                group = Group.query.filter_by(user_id=user_id, name=group_name).first()
                if group:
                    query = query.filter_by(group_id=group.id)
                else:
                    return {'success': True, 'data': [], 'message': f'未找到分组「{group_name}」'}
            bms = query.order_by(Bookmark.sort_order).limit(20).all()
            return {'success': True, 'data': [{'title': b.title, 'url': b.url} for b in bms]}

        elif tool_name == 'delete_bookmark':
            q = args.get('title_or_url', '')
            bm = Bookmark.query.filter(
                Bookmark.user_id == user_id,
                (Bookmark.title.ilike(f'%{q}%') | Bookmark.url.ilike(f'%{q}%'))
            ).first()
            if bm:
                title = bm.title
                db.session.delete(bm)
                db.session.commit()
                return {'success': True, 'message': f'已删除书签「{title}」'}
            return {'success': False, 'message': '未找到匹配的书签'}

        elif tool_name == 'add_todo':
            title = args.get('title', '')
            label = args.get('label', '')
            reminder_at = args.get('reminder_at', '')
            date_str = args.get('date', '')
            max_sort = db.session.query(db.func.max(Todo.sort_order)).filter_by(user_id=user_id).scalar() or 0
            # 从前端 NOTE_COLORS 调色板选一个颜色，保证跨面板一致 + 深色模式映射正确
            TOD_COLORS = ['#FF6B6B','#FDCB6E','#A29BFE','#2ECC71','#4ECDC4',
                          '#FF9FF3','#74B9FF','#FAB1A0','#DDA0DD','#FFEAA7']
            color = TOD_COLORS[(len(title) + user_id) % len(TOD_COLORS)]
            todo = Todo(user_id=user_id, title=title, label=label, color=color, done=False, sort_order=max_sort + 1)
            # 解析日期
            if date_str:
                try:
                    from datetime import datetime
                    todo.date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            # 解析提醒时间
            if reminder_at:
                try:
                    from datetime import datetime
                    dt = datetime.strptime(reminder_at, '%Y-%m-%d %H:%M')
                    todo.reminder_at = dt
                    todo.reminded = False
                except ValueError:
                    try:
                        dt = datetime.strptime(reminder_at, '%Y-%m-%d')
                        todo.reminder_at = dt
                        todo.reminded = False
                    except ValueError:
                        pass
            db.session.add(todo)
            db.session.commit()
            msg = f'已添加待办「{title}」'
            if todo.date:
                msg += f'，日期：{todo.date.strftime("%m月%d日")}'
            if todo.reminder_at:
                msg += f'，提醒时间：{todo.reminder_at.strftime("%m月%d日 %H:%M")}'
            elif not todo.date:
                # 没有日期也没有提醒，说明是在右侧待办栏
                msg += '（右侧待办栏）'
            return {'success': True, 'message': msg}

        elif tool_name == 'list_todos':
            todos = Todo.query.filter_by(user_id=user_id).order_by(Todo.sort_order).limit(20).all()
            return {'success': True, 'data': [{'title': t.title, 'done': t.done} for t in todos]}

        elif tool_name == 'toggle_todo':
            q = args.get('title_contains', '')
            todo = Todo.query.filter(
                Todo.user_id == user_id, Todo.title.ilike(f'%{q}%')
            ).first()
            if todo:
                todo.done = not todo.done
                db.session.commit()
                status = '已完成' if todo.done else '已标记为未完成'
                return {'success': True, 'message': f'待办「{todo.title}」{status}'}
            return {'success': False, 'message': '未找到匹配的待办'}

        elif tool_name == 'delete_todo':
            q = args.get('title_contains', '')
            todo = Todo.query.filter(
                Todo.user_id == user_id, Todo.title.ilike(f'%{q}%')
            ).first()
            if todo:
                title = todo.title
                db.session.delete(todo)
                db.session.commit()
                return {'success': True, 'message': f'已删除待办「{title}」'}
            return {'success': False, 'message': '未找到匹配的待办'}

        elif tool_name == 'create_note':
            notebook_title = args.get('notebook_title', '')
            title = args.get('title', '')
            content = args.get('content', '')
            if notebook_title:
                nb = Notebook.query.filter_by(user_id=user_id, title=notebook_title).first()
                if not nb:
                    nb = Notebook(user_id=user_id, title=notebook_title, color='#8B4513', color2='#5C2E0A', sort_order=0)
                    db.session.add(nb)
                    db.session.flush()
            else:
                nb = Notebook.query.filter_by(user_id=user_id).order_by(Notebook.sort_order).first()
                if not nb:
                    nb = Notebook(user_id=user_id, title='默认笔记本', color='#8B4513', color2='#5C2E0A', sort_order=0)
                    db.session.add(nb)
                    db.session.flush()
            note = Note(
                notebook_id=nb.id, title=title,
                content=content, sort_order=0
            )
            db.session.add(note)
            db.session.commit()
            return {'success': True, 'message': f'已创建笔记「{title}」'}

        elif tool_name == 'list_groups':
            groups = Group.query.filter_by(user_id=user_id).order_by(Group.sort_order).all()
            return {'success': True, 'data': [{'name': g.name, 'id': g.id} for g in groups]}

        elif tool_name == 'create_group':
            name = args.get('name', '')
            max_sort = db.session.query(db.func.max(Group.sort_order)).filter_by(user_id=user_id).scalar() or 0
            group = Group(user_id=user_id, name=name, sort_order=max_sort + 1)
            db.session.add(group)
            db.session.commit()
            return {'success': True, 'message': f'已创建分组「{name}」'}

        return {'success': False, 'message': f'未知工具: {tool_name}'}
    except Exception as e:
        logger.error(f'Tool {tool_name} error: {e}')
        db.session.rollback()
        return {'success': False, 'message': f'操作失败: {str(e)}'}


# ── 聊天 API（SSE 流式） ──

SYSTEM_PROMPT = """你是轻鸿主页的 AI 助手，是一个通用 AI 助手，可以回答问题、聊天、写作、计算、翻译、编程等，什么都可以聊。

你还可以帮用户管理轻鸿主页里的数据，包括：书签收藏、待办事项、笔记、收藏分组等，当用户提出相关需求时会自动调用工具完成操作。

系统说明（必须了解）：
- 今天是 {today_date}（{today_weekday}）
- 待办分为两种，互不冲突：
  · 日历待办（有 date 字段）：只显示在摸鱼日历对应日期格子中
  · 右侧待办（date 为 null）：只显示在右侧待办栏
- 创建规则：
  · 用户指定了日期（如"明天"、"下周一"、"5月28日"）→ 转成具体日期，传 date 参数，添加到摸鱼日历
  · 用户未指定日期 → 不传 date 参数，直接添加到右侧待办栏
- 创建待办后不需要问用户其他问题，直接告知结果即可
- 涉及相对时间（"明天"、"下周"等），请根据今天的日期准确计算

【输出格式铁律——违反将严重破坏用户体验】
1. 表格：必须用管道格式，示例如下。严禁使用 tab 或空格对齐的文本表格。
   | 姓名 | 年龄 | 城市 |
   |------|------|------|
   | 张三 | 25   | 北京 |
2. 代码：必须用三重反引号包裹并注明语言。严禁使用 `excel复制`、`python复制` 等文字标签代替代码块。
   ```excel
   =COUNTIFS(A:A,">"&A2)
   ```
3. 标题：用 `# ` / `## ` / `### ` 
4. 列表：用 `- ` 或 `1. `
5. 粗体：用 `**`

重要规则：
1. 涉及操作书签、待办、笔记、分组等数据的请求，必须调用对应的函数，不能只说"已添加"而不调用函数。
2. 如果没有调用函数，就不能声称操作已完成。只回复能确认的信息。
3. 用户指令模糊时，主动推理（如"抖音"→"https://douyin.com"）
4. 如果缺少必要信息，主动询问用户
5. 回答简洁友好，适当使用 emoji"""


# 清洗 AI 输出：确保返回前端的是标准 markdown 格式
def clean_chunk(text):
    """逐块清洗：仅处理模型输出的常见格式瑕疵"""
    if not text:
        return text
    # xxx复制 → ```xxx （处理有无尾随换行两种情况）
    return re.sub(r'^([a-zA-Z+#]+)复制(?:\s*\n)?', r'```\1\n', text, flags=re.MULTILINE)


@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    messages = data.get('messages', [])

    # 读取 AI 配置
    config = _get_ai_config(user_id)
    if not config or not config.get('enabled'):
        return error('AI 功能未启用，请先在设置中配置', 400)
    if not config.get('api_key'):
        return error('API Key 未配置', 400)

    api_url = config['api_url'].rstrip('/')
    # 如果填的已经是完整地址（含 /chat/completions），则直接使用
    if not api_url.endswith('/chat/completions'):
        api_url += '/chat/completions'
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json',
    }

    # 构建带当前日期的系统提示
    from datetime import datetime as dt_now
    now = dt_now.now()
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    today_prompt = SYSTEM_PROMPT.format(
        today_date=now.strftime('%Y年%m月%d日'),
        today_weekday=weekday_names[now.weekday()],
    )

    req_messages = [{'role': 'system', 'content': today_prompt}]
    req_messages += messages[-20:]

    def generate():
        try:
            max_rounds = 30  # 防止无限循环
            round_num = 0
            retry_429 = 0  # 限流重试次数
            current_messages = req_messages
            use_tools = True  # 尝试使用工具调用，失败后降级
            import time as sleep_mod

            while round_num < max_rounds:
                round_num += 1
                # 间隔 1 秒，避免触发限流
                if round_num > 1:
                    sleep_mod.sleep(1)
                payload = {
                    'model': config['model'],
                    'messages': current_messages,
                    'stream': True,
                }
                if use_tools:
                    payload['tools'] = TOOLS

                try:
                    resp = requests.post(
                        api_url, headers=headers, json=payload,
                        stream=True, timeout=60,
                    )
                except requests.exceptions.RequestException as req_err:
                    # 网络层面异常，放弃
                    yield f'data: {json.dumps({"type": "error", "content": f"AI 服务请求失败: {str(req_err)[:80]}"})}\n\n'
                    return

                if resp.status_code != 200:
                    error_body = resp.text[:300]
                    user_msg = f'AI 服务返回错误 (HTTP {resp.status_code})'
                    # 如果是因为 tools 参数不被支持，降级重试
                    if use_tools and (resp.status_code == 400 or resp.status_code == 404):
                        logger.info(f'AI tools 不被支持，降级为普通对话重试')
                        use_tools = False
                        round_num -= 1  # 不计入轮次
                        continue
                    # 429 限流：等待后重试（不消耗轮次）
                    if resp.status_code == 429 and retry_429 < 2:
                        retry_429 += 1
                        logger.warning(f'触发限流(429)，第{retry_429}次重试')
                        yield f'data: {json.dumps({"type": "text", "content": "⏳ 请求过于频繁，稍等..."})}\n\n'
                        sleep_mod.sleep(2)
                        # 开启缓冲模式：下次成功响应用于清洗后替换
                        round_num -= 1
                        continue
                    if error_body:
                        try:
                            err_json = json.loads(error_body)
                            if err_json.get('error', {}).get('message'):
                                user_msg += f'：{err_json["error"]["message"]}'
                            elif err_json.get('message'):
                                user_msg += f'：{err_json["message"]}'
                        except json.JSONDecodeError:
                            user_msg += f'：{error_body[:100]}'
                    logger.warning(f'AI API error {resp.status_code}: {error_body}')
                    yield f'data: {json.dumps({"type": "error", "content": user_msg})}\n\n'
                    return

                # 收集本轮响应
                full_content = ''
                tool_calls_buffer = {}

                for line in resp.iter_lines():
                    if not line:
                        continue
                    line = line.decode('utf-8')
                    if not line.startswith('data: '):
                        continue
                    chunk_str = line[6:]
                    if chunk_str == '[DONE]':
                        break

                    try:
                        chunk = json.loads(chunk_str)
                    except json.JSONDecodeError:
                        continue

                    choices = chunk.get('choices')
                    if not choices:
                        continue
                    delta = choices[0].get('delta', {})

                    # 普通文本 — 流式发出前清洗
                    if delta.get('content'):
                        part = clean_chunk(delta['content'])
                        full_content += part
                        yield f'data: {json.dumps({"type": "text", "content": part})}\n\n'

                    # 工具调用
                    tool_calls = delta.get('tool_calls')
                    if tool_calls:
                        for tc in tool_calls:
                            idx = tc.get('index', 0)
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {
                                    'id': tc.get('id', ''),
                                    'function': {'name': '', 'arguments': ''},
                                }
                            buf = tool_calls_buffer[idx]
                            if tc.get('id'):
                                buf['id'] = tc['id']
                            if tc['function'].get('name'):
                                buf['function']['name'] += tc['function']['name']
                            if tc['function'].get('arguments'):
                                buf['function']['arguments'] += tc['function']['arguments']

                # 如果有工具调用
                if tool_calls_buffer:
                    tc_message = {'role': 'assistant', 'content': full_content or None}
                    tc_message['tool_calls'] = []
                    for idx in sorted(tool_calls_buffer.keys()):
                        tc = tool_calls_buffer[idx]
                        tc_message['tool_calls'].append({
                            'id': tc['id'],
                            'type': 'function',
                            'function': {
                                'name': tc['function']['name'],
                                'arguments': tc['function']['arguments'],
                            }
                        })
                    current_messages.append(tc_message)

                    # 执行工具
                    for idx in sorted(tool_calls_buffer.keys()):
                        tc = tool_calls_buffer[idx]
                        func_name = tc['function']['name']
                        try:
                            func_args = json.loads(tc['function']['arguments'])
                        except json.JSONDecodeError:
                            func_args = {}

                        # 通知前端正在执行
                        yield f'data: {json.dumps({"type": "tool_start", "tool": func_name})}\n\n'

                        result = execute_tool(user_id, func_name, func_args)
                        current_messages.append({
                            'role': 'tool',
                            'tool_call_id': tc['id'],
                            'content': json.dumps(result, ensure_ascii=False),
                        })

                        yield f'data: {json.dumps({"type": "tool_end", "tool": func_name, "result": result})}\n\n'

                    # 继续下一轮（把工具结果发给 AI 生成回复）
                    continue
                else:
                    # 没有工具调用，本轮结束
                    if full_content:
                        current_messages.append({'role': 'assistant', 'content': full_content})
                    break

            if round_num >= max_rounds:
                yield f'data: {json.dumps({"type": "text", "content": "\n\n（已到达最大对话轮次）"})}\n\n'

        except requests.Timeout:
            yield f'data: {json.dumps({"type": "error", "content": "AI 服务超时，请稍后重试"})}\n\n'
        except requests.exceptions.MissingSchema:
            yield f'data: {json.dumps({"type": "error", "content": "API 地址格式错误，缺少 http:// 或 https:// 前缀，请在设置中检查"})}\n\n'
        except requests.exceptions.ConnectionError:
            yield f'data: {json.dumps({"type": "error", "content": "无法连接到 AI 服务，请检查 API 地址和网络连接"})}\n\n'
        except requests.exceptions.InvalidURL:
            yield f'data: {json.dumps({"type": "error", "content": "API 地址格式不正确，请在设置中检查"})}\n\n'
        except Exception as e:
            logger.error(f'AI chat error: {e}')
            err_msg = str(e)
            # 常见 Python 错误消息中文化
            if 'No module named' in err_msg:
                yield f'data: {json.dumps({"type": "error", "content": "服务内部错误：缺少依赖模块"})}\n\n'
            elif 'Connection refused' in err_msg or 'Connection reset' in err_msg:
                yield f'data: {json.dumps({"type": "error", "content": "AI 服务连接被拒绝，请检查 API 地址是否正确"})}\n\n'
            elif '401' in err_msg or 'Unauthorized' in err_msg:
                yield f'data: {json.dumps({"type": "error", "content": "API Key 无效或未授权，请在设置中检查"})}\n\n'
            elif 'Timeout' in err_msg:
                yield f'data: {json.dumps({"type": "error", "content": "请求 AI 服务超时，请稍后重试"})}\n\n'
            else:
                yield f'data: {json.dumps({"type": "error", "content": f"AI 服务出错，请检查设置中的 API 地址和 Key 是否正确"})}\n\n'
        finally:
            yield 'data: [DONE]\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )
