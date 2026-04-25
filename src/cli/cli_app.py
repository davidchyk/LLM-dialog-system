from __future__ import annotations

from src.core.chat_manager import ChatManager, ChatTitleError
from src.core.models import Chat

def run_cli(chat_manager: ChatManager | None = None) -> None:
    manager = chat_manager or ChatManager()
    print("LLM Dialog System - CLI, Version 0.1 (in working)\n")

    while True:

        print("Main menu:")
        print("1. Create new chat")
        print("2. Select existing chat")
        print("3. Exit")

        choice = input("Choose option: ").strip()

        if choice == "1":
            title = input("Chat title (leave empty for default): ").strip()

            try:
                chat = manager.create_chat(title or None)

            except ChatTitleError as error:
                print(error)
                continue

            print(f"Created chat: \"{chat.title}\"")
            _chat_loop(manager, chat)

        elif choice == "2":
            chat = _select_chat(manager)
            if chat is not None:
                _print_history(chat)
                _chat_loop(manager, chat)

        elif choice == "3":
            print("Goodbye! See you later <3")
            return

        else:
            print("Invalid option. Please choose 1, 2, or 3.")


def _select_chat(manager: ChatManager) -> Chat | None:

    chats = manager.list_chats()

    if not chats:
        print("No chats found.")
        return None

    print("\nExisting chats:")

    for index, chat in enumerate(chats, start=1):
        print(f"{index}. {chat.title} ({chat.updated_at})")

    choice = input("Choose chat number: ").strip()

    try:
        selected_index = int(choice)
    except ValueError:
        print("Invalid number.")
        return None

    if not 1 <= selected_index <= len(chats):
        print("Chat number is out of range.")
        return None

    return chats[selected_index - 1]


def _chat_loop(manager: ChatManager, chat: Chat) -> None:

    print("\nChat mode. Type /exit to return to menu or /quit to quit.")

    while True:
        user_input = input("You: ").strip()

        if user_input == "/exit":
            return

        if user_input == "/quit":
            raise SystemExit(0)

        if not user_input:
            print("Message cannot be empty.")
            continue

        result = manager.send_message(chat.id, user_input)

        if result is None:
            print("Unable to save message. Chat was not found.")
            return

        chat, assistant_response = result
        print(f"Assistant: {assistant_response}")


def _print_history(chat: Chat) -> None:

    if not chat.messages:
        print("Chat history is empty.")
        return

    print("\nChat history:")

    for message in chat.messages:
        author = "You" if message.role == "user" else "Assistant"
        print(f"{author}: {message.content}")