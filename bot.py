import os
from telethon import TelegramClient

api_id = "You Api_id"
api_hash = 'Yoy Api_hash'

client = TelegramClient('explorer_session', api_id, api_hash)
BASE_FOLDER = 'Variety'


async def main():
  print('🚀 Connecting to Telegram...')
  await client.start()
  print('✅Successfully logged into the account!')

  if not os.path.exists(BASE_FOLDER):
    os.makedirs(BASE_FOLDER)

  print('⏳ Starting chat download...')

  async for dialog in client.iter_dialogs():
    try:
      if not dialog.is_user:
        continue
      entity = dialog.entity
      if getattr(entity, 'bot', False):
        continue

      name = getattr(entity, 'first_name', 'Unknown')
      if getattr(entity, 'last_name', None):
        name += f' {entity.last_name}'

      print(f'📥 Downloading chat: {name}...')

      uid = str(dialog.id)
      safe_name = ''.join(
          c for c in name if c.isalnum() or c in (' ', '_', '-')
      ).strip()
      chat_folder_name = f'{safe_name}_{uid}'
      chat_path = os.path.join(BASE_FOLDER, chat_folder_name)

      if not os.path.exists(chat_path):
        os.makedirs(chat_path)

      log_file = os.path.join(chat_path, 'переписка.txt')

      messages_count = 0
      with open(log_file, 'w', encoding='utf-8') as f:
        async for message in client.iter_messages(dialog.id):
          sender_name = 'Я' if message.out else name
          date_str = (
              message.date.strftime('%Y-%m-%d %H:%M')
              if message.date
              else '2026-00-00 00:00'
          )

          media_label = ''
          if message.media:
            try:
              file_path = await message.download_media(file=chat_path)
              if file_path:
                file_name = os.path.basename(file_path)
                if message.photo:
                  media_label = f'[Фото: {file_name}]'
                elif message.video:
                  media_label = f'[Видео: {file_name}]'
                elif message.voice:
                  media_label = f'[Голосовое: {file_name}]'
                elif message.video_note:
                  media_label = f'[Кружок: {file_name}]'
                else:
                  media_label = f'[Файл: {file_name}]'
            except Exception:
              media_label = '[Медиа]'

          txt = message.text or ''
          if media_label:
            text = f'{media_label} {txt}'.strip()
          else:
            text = txt or '[Пустое сообщение]'

          text_clean = text.replace('\n', ' ')
          f.write(f'[{date_str}] {sender_name}: {text_clean}\n')
          messages_count += 1

      print(f'✅ Готово: {name} (сообщений: {messages_count})')
    except Exception as e:
      print(f'⚠️ Ошибка с чатом: {e}')

  print('🎉 Полная выгрузка завершена!')
  input('Нажми Enter, чтобы закрыть окно...')


if __name__ == '__main__':
  with client:
    client.loop.run_until_complete(main())
