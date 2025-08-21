# Telegram Tag Groups Bot

A Telegram bot that allows group members to create and manage **custom tag groups** in chats.  
Instead of tagging everyone manually, users can join specific groups (e.g., *Games*, *Work*, *Study*) and mention all members of a group with a single command.

---

## 🚀 Features
- Create up to **7 tag groups** per chat (admins only).
- Join or leave groups with a simple command.
- Tag all members of a selected group at once.
- List all groups with their members.
- Delete groups with confirmation via interactive menu.
- Interactive **ReplyKeyboard** menus for selecting groups (no need to type names).
- Built with:
  - **Python**
  - **python-telegram-bot**
  - **MongoDB**
  - **Flask**

---

## 📌 Commands
- `/start` — Show welcome message and help.
- `/create_group <name>` — Create a new tag group (admins only, max 7 per chat).
- `/join_group` — Join an existing group via interactive menu.
- `/leave_group` — Leave a group via interactive menu.
- `/tag_group` — Mention all members of a selected group.
- `/list_groups` — Show all groups and their members.
- `/delete_group` — Delete a group (admins only, with confirmation).

---
