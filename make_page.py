import html
import json
import os
import re

BASE_FOLDER = 'Сорт'


def main():
  if not os.path.exists(BASE_FOLDER):
    print('❌ Папка Сорт не найдена!')
    return

  chats_data = {}
  sidebar_items = ''
  count = 0

  try:
    folders = sorted(os.listdir(BASE_FOLDER))
  except Exception as e:
    print(f'❌ Ошибка чтения папки Сорт: {e}')
    return

  for folder in folders:
    try:
      full_path = os.path.join(BASE_FOLDER, folder)
      if not os.path.isdir(full_path):
        continue

      parts = folder.rsplit('_', 1)
      name = parts[0]
      uid = parts[1] if len(parts) > 1 else ''

      log_file = os.path.join(full_path, 'переписка.txt')
      messages = []
      if os.path.exists(log_file):
        try:
          with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
              if line.strip():
                messages.append(line.strip())
        except Exception:
          pass

      chat_files = {}
      for root, dirs, files in os.walk(full_path):
        for file in files:
          if file == 'переписка.txt':
            continue
          try:
            rel_path = os.path.relpath(
                os.path.join(root, file), full_path
            ).replace('\\', '/')
            chat_files[file] = rel_path
          except Exception:
            pass

      msgs_html = ''

      for line in messages:
        try:
          match = re.match(r'^\[(.*?)\]\s+(.+?):\s+(.*)$', line)
          if match:
            date_time, sender, text = match.groups()
          else:
            date_time, sender, text = '', 'Собеседник', line

          media_type = 'text'
          display_html = ''

          photo_match = re.search(
              r'\[Фото:\s*([^\]]+)\]', text, flags=re.IGNORECASE
          )
          video_match = re.search(
              r'\[Видео:\s*([^\]]+)\]', text, flags=re.IGNORECASE
          )
          vnote_match = re.search(
              r'\[Кружок:\s*([^\]]+)\]', text, flags=re.IGNORECASE
          )
          voice_match = re.search(
              r'\[Голосовое:\s*([^\]]+)\]', text, flags=re.IGNORECASE
          )
          file_match = re.search(
              r'\[Файл:\s*([^\]]+)\]', text, flags=re.IGNORECASE
          )

          clean_text = re.sub(
              r'\[(Фото|Видео|Кружок|Голосовое|Файл|Документ)[^\]]*\]',
              '',
              text,
          ).strip()

          def get_file_path(matched_str):
            try:
              base_name = os.path.basename(matched_str.strip())
              if base_name in chat_files:
                return chat_files[base_name]
            except Exception:
              pass
            return matched_str.strip()

          web_prefix = f'{BASE_FOLDER}/{folder}'

          if photo_match:
            media_type = 'photo'
            img_rel = get_file_path(photo_match.group(1))
            full_img_path = f'{web_prefix}/{img_rel}'
            display_html = (
                '<div class="media-container"><img'
                f' src="{html.escape(full_img_path)}" class="chat-photo"'
                ' loading="lazy" alt="Фото"'
                f" onclick=\"openModal('{html.escape(full_img_path)}')\"></div>"
            )
          elif vnote_match or video_match:
            matched_val = (
                vnote_match.group(1) if vnote_match else video_match.group(1)
            )
            vid_rel = get_file_path(matched_val)
            full_vid_path = f'{web_prefix}/{vid_rel}'

            # Жесткое правило: если это явный маркер кружка ИЛИ в имени файла/пути есть признаки кружка
            # (но избегаем обычных длинных видео, если они называются как попало)
            low_val = vid_rel.lower()
            is_circle = (
                vnote_match is not None
                or 'note' in low_val
                or 'circle' in low_val
                or 'round' in low_val
                or 'vnote' in low_val
                or 'video_note' in low_val
            )

            if is_circle:
              media_type = 'video_note'
              display_html = (
                  '<div class="video-note-wrap"><video'
                  f' src="{html.escape(full_vid_path)}" controls'
                  ' preload="metadata" class="chat-video-note"></video></div>'
              )
            else:
              media_type = 'video'
              display_html = (
                  '<div class="media-container"><video'
                  f' src="{html.escape(full_vid_path)}" controls'
                  ' class="chat-video" preload="metadata"></video></div>'
              )
          elif voice_match:
            media_type = 'voice'
            aud_rel = get_file_path(voice_match.group(1))
            full_aud_path = f'{web_prefix}/{aud_rel}'
            display_html = (
                '<div class="voice-wrap"><audio controls preload="metadata"'
                ' class="chat-audio"><source'
                f' src="{html.escape(full_aud_path)}" type="audio/ogg"><source'
                f' src="{html.escape(full_aud_path)}" type="audio/mpeg"></audio></div>'
            )
          elif file_match:
            media_type = 'file'
            file_rel = get_file_path(file_match.group(1))
            full_file_path = f'{web_prefix}/{file_rel}'
            display_html = (
                '<div class="file-attachment">📎 <a'
                f' href="{html.escape(full_file_path)}" download'
                ' style="color: var(--accent); text-decoration: underline;'
                ' font-weight: 500;">Скачать файл</a></div>'
            )
          else:
            display_html = (
                f'<div class="msg-text-content">{html.escape(text)}</div>'
            )

          if clean_text and media_type != 'text':
            display_html += (
                '<div class="msg-text-content" style="margin-top:'
                f' 4px;">{html.escape(clean_text)}</div>'
            )

          cls = 'msg-out' if sender == 'Я' else 'msg-in'

          msgs_html += (
              f'<div class="msg {cls}" data-type="{media_type}">{display_html}'
              f'<div class="msg-time">{html.escape(date_time)}</div></div>'
          )
        except Exception:
          continue

      chats_data[folder] = {
          'name': name,
          'total': len(messages),
          'html': msgs_html or '<div class="empty-state">Сообщений нет</div>',
      }

      sidebar_items += (
          f'<div class="chat-item" onclick="selectChat(\'{folder}\')"'
          f' id="item_{folder}"><div class="chat-name">{html.escape(name)}</div>'
          f'<div class="chat-id">ID: {html.escape(uid)} ({len(messages)}'
          ' сообщ.)</div></div>'
      )
      count += 1
    except Exception as chat_err:
      print(f'⚠️ Пропущен проблемный чат {folder}: {chat_err}')

  if count == 0:
    print('❌ Нет доступных чатов для генерации!')
    return

  chats_json = json.dumps(chats_data, ensure_ascii=False)

  with open('index.html', 'w', encoding='utf-8') as f:
    f.write('<!DOCTYPE html>\n<html lang="ru">\n<head>\n')
    f.write('    <meta charset="UTF-8">\n')
    f.write('    <title>Архив Telegram</title>\n')
    f.write('    <style>\n')
    f.write(
        '        :root { --bg-main: #0e1621; --bg-sidebar: #17212b;'
        ' --bg-hover: #202b36; --bg-active: #2b5278; --text: #f5f5f5; --muted:'
        ' #7f91a4; --border: #101921; --msg-in: #182533; --msg-out: #2b5278;'
        ' --accent: #6ab2f2; }\n'
        '        .light-theme { --bg-main: #ffffff; --bg-sidebar: #f0f2f5;'
        ' --bg-hover: #e4e8ec; --bg-active: #3390ec; --text: #000000; --muted:'
        ' #707579; --border: #e0e0e0; --msg-in: #eef2f5; --msg-out: #effdde;'
        ' --accent: #2481cc; }\n'
        '        * { box-sizing: border-box; margin: 0; padding: 0;'
        ' font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,'
        ' sans-serif; }\n'
        '        body { display: flex; height: 100vh; background:'
        ' var(--bg-main); color: var(--text); overflow: hidden; }\n'
        '        .sidebar { width: 320px; background: var(--bg-sidebar);'
        ' border-right: 1px solid var(--border); display: flex;'
        ' flex-direction: column; }\n'
        '        .sidebar-header { padding: 16px; border-bottom: 1px solid'
        ' var(--border); display: flex; justify-content: space-between;'
        ' align-items: center; font-weight: bold; }\n'
        '        .theme-btn { background: none; border: none; font-size: 18px;'
        ' cursor: pointer; padding: 4px; border-radius: 4px; }\n'
        '        .theme-btn:hover { background: var(--bg-hover); }\n'
        '        .search-input { width: 100%; padding: 8px 12px; background:'
        ' var(--bg-main); border: 1px solid var(--border); border-radius: 6px;'
        ' color: var(--text); font-size: 14px; outline: none; margin-top:'
        ' 10px; }\n'
        '        .chat-list { overflow-y: auto; flex: 1; }\n'
        '        .chat-item { padding: 14px 18px; border-bottom: 1px solid'
        ' var(--border); cursor: pointer; transition: background 0.15s; }\n'
        '        .chat-item:hover { background: var(--bg-hover); }\n'
        '        .chat-item.active { background: var(--bg-active); color: #fff;'
        ' }\n'
        '        .chat-name { font-weight: 600; font-size: 15px; margin-bottom:'
        ' 3px; }\n'
        '        .chat-id { font-size: 12px; color: var(--muted); }\n'
        '        .chat-item.active .chat-id { color: #d0e1f9; }\n'
        '        .main { flex: 1; display: flex; flex-direction: column;'
        ' background: var(--bg-main); position: relative; }\n'
        '        .chat-header { padding: 12px 24px; background:'
        ' var(--bg-sidebar); border-bottom: 1px solid var(--border); display:'
        ' flex; justify-content: space-between; align-items: center; }\n'
        '        .chat-title-info { font-weight: bold; font-size: 16px; }\n'
        '        .filter-bar { display: flex; gap: 6px; align-items: center;'
        ' flex-wrap: wrap; }\n'
        '        .filter-btn { background: var(--bg-main); border: 1px solid'
        ' var(--border); color: var(--text); padding: 5px 10px; border-radius:'
        ' 14px; font-size: 12px; cursor: pointer; transition: 0.2s; }\n'
        '        .filter-btn:hover, .filter-btn.active { background:'
        ' var(--accent); color: #fff; border-color: var(--accent); }\n'
        '        .content-area { flex: 1; overflow-y: auto; padding: 20px 24px;'
        ' display: flex; flex-direction: column; gap: 8px; }\n'
        '        .empty-state { margin: auto; color: var(--muted); font-size:'
        ' 16px; text-align: center; }\n'
        '        .msg { max-width: 65%; padding: 8px 12px 6px 12px;'
        ' border-radius: 12px; font-size: 14px; line-height: 1.4; word-break:'
        ' break-word; position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.1);'
        ' }\n'
        '        .msg-in { align-self: flex-start; background: var(--msg-in);'
        ' border-bottom-left-radius: 4px; }\n'
        '        .msg-out { align-self: flex-end; background: var(--msg-out);'
        ' border-bottom-right-radius: 4px; }\n'
        '        .msg-text-content { margin-bottom: 2px; }\n'
        '        .msg-time { font-size: 10px; color: var(--muted); text-align:'
        ' right; float: right; margin-left: 8px; margin-top: 2px; }\n'
        '        .msg-out .msg-time { color: rgba(255,255,255,0.7); }\n'
        '        .media-container { margin: 4px 0 6px 0; border-radius: 8px;'
        ' overflow: hidden; max-width: 320px; }\n'
        '        .chat-photo { width: 100%; border-radius: 8px; display: block;'
        ' object-fit: cover; max-height: 400px; cursor: pointer; transition:'
        ' opacity 0.2s; }\n'
        '        .chat-photo:hover { opacity: 0.9; }\n'
        '        .chat-video { width: 100%; border-radius: 8px; display: block;'
        ' max-height: 250px; background: #000; }\n'
        '        .video-note-wrap { width: 160px; height: 160px; border-radius:'
        ' 50%; overflow: hidden; margin: 4px 0; background: #000; display: flex;'
        ' align-items: center; justify-content: center; }\n'
        '        .chat-video-note { width: 100%; height: 100%; object-fit:'
        ' cover; border-radius: 50%; display: block; }\n'
        '        .voice-wrap { width: 240px; margin: 4px 0; }\n'
        '        .chat-audio { width: 100%; height: 36px; display: block; }\n'
        '        .file-attachment { padding: 6px 0; font-size: 13px; }\n'
        '        .modal { display: none; position: fixed; z-index: 1000; left:'
        ' 0; top: 0; width: 100%; height: 100%; background-color:'
        ' rgba(0,0,0,0.85); align-items: center; justify-content: center; }\n'
        '        .modal img { max-width: 90%; max-height: 90%; border-radius:'
        ' 8px; box-shadow: 0 5px 25px rgba(0,0,0,0.5); }\n'
        '        .modal-close { position: absolute; top: 20px; right: 30px;'
        ' color: #fff; font-size: 35px; font-weight: bold; cursor: pointer;'
        ' background: rgba(0,0,0,0.4); width: 50px; height: 50px;'
        ' border-radius: 50%; display: flex; align-items: center;'
        ' justify-content: center; transition: background 0.2s; }\n'
        '        .modal-close:hover { background: rgba(255,255,255,0.2); }\n'
    )
    f.write('    </style>\n</head>\n<body>\n')
    f.write('    <div class="sidebar">\n')
    f.write('        <div class="sidebar-header">\n')
    f.write(f'            <span>📁 Архив ({count})</span>\n')
    f.write(
        '            <button class="theme-btn" onclick="toggleTheme()"'
        ' title="Сменить тему">🌙</button>\n'
    )
    f.write('        </div>\n')
    f.write(
        '        <div style="padding: 10px 16px; border-bottom: 1px solid'
        ' var(--border);">\n'
    )
    f.write(
        '            <input type="text" id="searchInput"'
        ' oninput="filterChats()" placeholder="🔍 Поиск по имени..."'
        ' class="search-input">\n'
    )
    f.write('        </div>\n')
    f.write('        <div class="chat-list" id="chatList">\n')
    f.write(f'            {sidebar_items}\n')
    f.write('        </div>\n')
    f.write('    </div>\n')
    f.write('    <div class="main">\n')
    f.write('        <div class="chat-header">\n')
    f.write(
        '            <div class="chat-title-info" id="chatHeader">Выберите чат'
        ' слева</div>\n'
    )
    f.write(
        '            <div class="filter-bar" id="filterBar" style="display:'
        ' none;">\n'
    )
    f.write(
        '                <button class="filter-btn active"'
        ' onclick="filterMessages(\'all\', this)">Все</button>\n'
    )
    f.write(
        '                <button class="filter-btn"'
        ' onclick="filterMessages(\'photo\', this)">📷 Фото</button>\n'
    )
    f.write(
        '                <button class="filter-btn"'
        ' onclick="filterMessages(\'video\', this)">🎥 Видео</button>\n'
    )
    f.write(
        '                <button class="filter-btn"'
        ' onclick="filterMessages(\'voice\', this)">🎤 Голос</button>\n'
    )
    f.write(
        '                <button class="filter-btn"'
        ' onclick="filterMessages(\'video_note\', this)">⭕ Кружки</button>\n'
    )
    f.write(
        '                <button class="filter-btn"'
        ' onclick="filterMessages(\'file\', this)">📎 Файлы</button>\n'
    )
    f.write('            </div>\n')
    f.write('        </div>\n')
    f.write(
        '        <div class="content-area" id="chatContent">\n'
        '            <div class="empty-state">👈 Выберите диалог слева.</div>\n'
        '        </div>\n'
        '    </div>\n\n'
    )
    f.write(
        '    <div id="photoModal" class="modal" onclick="closeModal()">\n'
        '        <span class="modal-close">&times;</span>\n'
        '        <img id="modalImg" src="">\n'
        '    </div>\n\n'
    )
    f.write('    <script>\n')
    f.write(f'        const chats = {chats_json};\n')
    f.write(
        '        function selectChat(folder) {\n'
        "            document.querySelectorAll('.chat-item').forEach(el =>"
        " el.classList.remove('active'));\n"
        "            const activeItem = document.getElementById('item_' +"
        ' folder);\n'
        "            if (activeItem) activeItem.classList.add('active');\n"
        '            const chat = chats[folder];\n'
        '            if (chat) {\n'
        "                document.getElementById('chatHeader').innerText ="
        ' chat.name + " (" + chat.total + " сообщ.)";\n'
        "                document.getElementById('filterBar').style.display ="
        " 'flex';\n"
        "               "
        " document.querySelectorAll('.filter-btn').forEach(b =>"
        " b.classList.remove('active'));\n"
        "                document.querySelector('.filter-btn').classList.add('active');\n"
        "                const content = document.getElementById('chatContent');\n"
        '                content.innerHTML = chat.html;\n'
        '                content.scrollTop = content.scrollHeight;\n'
        '            }\n'
        '        }\n\n'
        '        function openModal(imgSrc) {\n'
        "            const modal = document.getElementById('photoModal');\n"
        "            const modalImg = document.getElementById('modalImg');\n"
        "            modal.style.display = 'flex';\n"
        '            modalImg.src = imgSrc;\n'
        '        }\n\n'
        '        function closeModal() {\n'
        "            document.getElementById('photoModal').style.display ="
        " 'none';\n"
        '        }\n\n'
        '        function filterMessages(type, btn) {\n'
        "           "
        " document.querySelectorAll('.filter-btn').forEach(b =>"
        " b.classList.remove('active'));\n"
        "            btn.classList.add('active');\n"
        "            const content = document.getElementById('chatContent');\n"
        "            const messages = content.querySelectorAll('.msg');\n"
        '            messages.forEach(msg => {\n'
        "                if (type === 'all' || msg.getAttribute('data-type') ==="
        ' type) {\n'
        "                    msg.style.display = 'block';\n"
        '                } else {\n'
        "                    msg.style.display = 'none';\n"
        '                }\n'
        '            });\n'
        '        }\n\n'
        '        function filterChats() {\n'
        "            const query ="
        " document.getElementById('searchInput').value.toLowerCase();\n"
        "            const items = document.querySelectorAll('.chat-item');\n"
        '            items.forEach(item => {\n'
        "                const name ="
        " item.querySelector('.chat-name').innerText.toLowerCase();\n"
        "                item.style.display = name.includes(query) ? 'block'"
        " : 'none';\n"
        '            });\n'
        '        }\n\n'
        '        function toggleTheme() {\n'
        "            document.body.classList.toggle('light-theme');\n"
        "            const button = document.querySelector('.theme-btn');\n"
        "            button.innerText ="
        " document.body.classList.contains('light-theme') ? '☀️' : '🌙';\n"
        '        }\n'
    )
    f.write('    </script>\n</body>\n</html>')

  print(
      f'✅ Готово! Кружки теперь отфильтрованы и встали в свой раздел. Чатов:'
      f' {count}.'
  )


if __name__ == '__main__':
  main()