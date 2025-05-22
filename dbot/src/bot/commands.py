import discord
from discord.ext import commands

from observer.observer_client import observer, logger, Event, Param

from bot.bot_server import dbot
import bot.cmd_autocomplete as auto

import bot.utilities

bot = dbot.bot

#-------------------------------------------------------
# SECTION Bot for-all commands
#-------------------------------------------------------

# -- /reg
@bot.tree.command(name="reg", description="Регистрация пользователя с указанием steam_id")
async def cmd_reg(interaction: discord.Interaction, steam_id: str):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_REG, {
    Param.Interaction: interaction,
    "steam_id": steam_id
  })

# -- /unreg
@bot.tree.command(name="unreg", description="Удаляет данные пользователя по Discord ID")
async def cmd_unreg(interaction: discord.Interaction):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_UNREG, {
    Param.Interaction: interaction,
  })


# !SECTION
#-------------------------------------------------------
# SECTION Bot admin commands
#-------------------------------------------------------

# -- /clear
@bot.tree.command(name="clear",description="Удаляет сообщения в канале")
@discord.app_commands.describe(amount="Количество сообщений для удаления")
@commands.has_permissions(manage_messages=True) 
async def cmd_ping(interaction: discord.Interaction, amount: int=0):
  await interaction.response.defer(thinking=True, ephemeral=True)

  try:
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(content=f'Удалено {len(deleted)} сообщений.')
    # awaitч observer.notify(Event.BC_CLEAR)

    ch_name = interaction.channel.name
    ds_name = interaction.user.display_name
    g_name = interaction.user.name

    logger.info(f"{ds_name} удалил {len(deleted)} сообщений в {ch_name}")

  except Exception as e:
    await interaction.followup.send(content=f'Произошла ошибка: {str(e)}')

# !SECTION
#-------------------------------------------------------
# SECTION CS admin commands
#-------------------------------------------------------

# -- /connect_to_cs
@bot.tree.command(name="connect_to_cs", description="Подключается к серверу")
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_connect_to_cs(interaction: discord.Interaction):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_CONNECT_TO_CS, {
    Param.Interaction: interaction,
  })

# -- /rcon
@bot.tree.command(name="rcon", description="Отправляет произвольную команду в консоль сервера")
@commands.has_permissions(manage_messages=True)
async def cmd_rcon(interaction: discord.Interaction, command: str):     
  await interaction.response.defer(thinking=True, ephemeral=True)
  
  await observer.notify(Event.BC_CS_RCON, {
    Param.Interaction: interaction,
    "command": command
  })

# -- /kick
@bot.tree.command(name="kick", description="Кикает игрока с сервера")
@discord.app_commands.describe(target="Ник игрока, можно вставить steam_id", reason="Причина кика")
@discord.app_commands.autocomplete(target=auto.players_online)
@commands.has_permissions(manage_messages=True)
async def cmd_kick(interaction: discord.Interaction, target: str, reason: str=""):  
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_CS_KICK, {
    Param.Interaction: interaction,
    "target": target,
    "reason": reason
  })

# -- /ban
@bot.tree.command(name="ban", description="Банит игрока на сервера")
@discord.app_commands.describe(
  target="Ник игрока", 
  minutes="Минут бана(0 - перманент)", 
  reason="Причина бана")
@discord.app_commands.autocomplete(target=auto.ban_online)
@discord.app_commands.autocomplete(minutes=auto.ban_minutes)
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_ban(interaction: discord.Interaction, target: str, minutes: int, reason: str=""):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_CS_BAN, {
    Param.Interaction: interaction,
    "target": target,
    "minutes": minutes,
    "reason": reason
  })

# -- /ban_offline
@bot.tree.command(name="ban_offline", description="Банит игрока, который был на сервере ранее")
@discord.app_commands.describe(
  target="steam_id игрока", 
  minutes="Минут бана(0 - перманент)", 
  reason="Причина бана")
@discord.app_commands.autocomplete(target=auto.ban_offline)
@discord.app_commands.autocomplete(minutes=auto.ban_minutes)
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_offline_ban(interaction: discord.Interaction, target: str, minutes: int, reason: str=""):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_CS_BAN_OFFLINE, {
    Param.Interaction: interaction,
    "target": target,
    "minutes": minutes,
    "reason": reason
  })

# -- /unban
@bot.tree.command(name="unban", description="Разбанивает игрока")
@discord.app_commands.describe(target="steam_id игрока")
@discord.app_commands.autocomplete(target=auto.unban)
@commands.has_permissions(manage_messages=True)  # Проверка прав пользователя
async def cmd_unban(interaction: discord.Interaction, target: str):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_CS_UNBAN, {
    Param.Interaction: interaction,
    "target": target,
  })

# -- /sync_maps
@bot.tree.command(name="sync_maps", 
                  description="Синхронизирует список карт между MySQL, redis и сервером(MySQL главный)")
@commands.has_permissions(manage_messages=True)  
async def cmd_sync_maps(interaction: discord.Interaction):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_CS_SYNC_MAPS, {
    Param.Interaction: interaction,
  })

# -- /sync_maps_to_db
@bot.tree.command(name="sync_maps_to_db", description="Инициирует синхронизацию списка карт с CS сервера в базу данных.")
@commands.has_permissions(manage_messages=True)
async def cmd_sync_maps_to_db(interaction: discord.Interaction):
  await interaction.response.defer(thinking=True, ephemeral=True)
  try:
    # Send the RCON command to the CS server
    await observer.notify(Event.BC_CS_RCON, {
        Param.Interaction: interaction, # Pass interaction for potential RCON handler follow-up
        "command": "ultrahc_cs_upload_maps_to_db"
        # Note: The BC_CS_RCON event handler might send its own followup message.
        # This command provides a specific confirmation that this particular action was initiated.
    })
    # Send a confirmation message to the user
    await interaction.followup.send("Команда синхронизации карт с сервера в БД отправлена. Проверьте консоль сервера для деталей.", ephemeral=True)
  except Exception as e:
    logger.error(f"Error in cmd_sync_maps_to_db: {e}", exc_info=True)
    # Try to send an error message if the followup hasn't been used yet by RCON handler
    if not interaction.response.is_done():
        await interaction.followup.send("Произошла ошибка при отправке команды синхронизации.", ephemeral=True)
    else: # if RCON handler already responded (possibly with an error, or success)
        logger.info("cmd_sync_maps_to_db: Interaction already responded to by RCON handler, error not sent to user via this command's followup.")


# -- /map_change
@bot.tree.command(name="map_change", description="Меняет карту")
@discord.app_commands.describe(map="Название карты")
@discord.app_commands.autocomplete(map=auto.maps_active)
@commands.has_permissions(manage_messages=True)
async def cmd_map_change(interaction: discord.Interaction, map: str):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_CS_MAP_CHANGE, {
    Param.Interaction: interaction,
    "map": map
  })

# -- /map_add
@bot.tree.command(name="map_add", description="Добавляет карту в БД")
@discord.app_commands.describe(map_name="Название карты", 
                               activated="Активна ли карта(в маппуле)", 
                               min_players="Минимум игроков", 
                               max_players="Максимум игроков", 
                               priority="Приоритет")
@commands.has_permissions(manage_messages=True) 
async def cmd_map_add(interaction: discord.Interaction, map_name: str, activated: int=1, min_players: int=0, max_players: int=32, priority: int=100):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_DB_MAP_ADD, {
    Param.Interaction: interaction,
    "map_name": map_name,
    "activated": activated,
    "min_players": min_players,
    "max_players": max_players,
    "priority": priority
  })

# -- /map_delete
@bot.tree.command(name="map_delete", description="Удаляет карту из БД")
@discord.app_commands.describe(map_name="Название карты")
@discord.app_commands.autocomplete(map_name=auto.maps_all)
@commands.has_permissions(manage_messages=True)
async def cmd_map_delete(interaction: discord.Interaction, map_name: str):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_DB_MAP_DELETE, {
    Param.Interaction: interaction,
    "map_name": map_name
  })

# -- /map_update
@bot.tree.command(name="map_update", description="Обновляет карту новыми данными")
@discord.app_commands.describe(map_name="Название карты", 
                               activated="Активна ли карта(в маппуле)", 
                               min_players="Минимум игроков", 
                               max_players="Максимум игроков", 
                               priority="Приоритет")
@discord.app_commands.autocomplete(map_name=auto.maps_all)
@commands.has_permissions(manage_messages=True)
async def cmd_map_update(interaction: discord.Interaction, map_name: str, activated: int=None, min_players: int=None, max_players: int=None, priority: int=None):
  await interaction.response.defer(thinking=True, ephemeral=True)

  await observer.notify(Event.BC_DB_MAP_UPDATE, {
    Param.Interaction: interaction,
    "map_name": map_name,
    "activated": activated,
    "min_players": min_players,
    "max_players": max_players,
    "priority": priority
  })

# -- /list_server_maps
@bot.tree.command(name="list_server_maps", description="Выводит список карт с сервера из базы данных и их статус активации.")
@commands.has_permissions(manage_messages=True) # Or other appropriate permissions
async def cmd_list_server_maps(interaction: discord.Interaction):
  await interaction.response.defer(thinking=True, ephemeral=True)

  try:
    # map_list_data is expected to be List[Tuple[str, int]] or None
    # Example: [('de_dust2', 1), ('cs_office', 0)]
    map_list_data = await observer.nsroute.call_route("/get_map_list")

    if not map_list_data: # Handles None or empty list
      await interaction.followup.send("Список карт пуст или не удалось его загрузить.", ephemeral=True)
      return

    response_lines = ["**Список карт сервера:**"]
    for map_entry in map_list_data:
      if isinstance(map_entry, (list, tuple)) and len(map_entry) >= 2:
        map_name = str(map_entry[0]) # Ensure map_name is a string
        try:
            activated = int(map_entry[1]) # Ensure activated is an int
            status_str = "Активна" if activated == 1 else "Неактивна"
            response_lines.append(f"- {map_name}: {status_str}")
        except (ValueError, TypeError):
            logger.warning(f"cmd_list_server_maps: Invalid activation status for map '{map_name}': {map_entry[1]}")
            response_lines.append(f"- {map_name}: Статус неизвестен (ошибка данных)")
      else:
        logger.warning(f"cmd_list_server_maps: Unexpected map entry format: {map_entry}")
        # Optionally, add a placeholder for malformed entries if desired
        # response_lines.append(f"- Некорректные данные для карты: {str(map_entry)[:50]}")


    if len(response_lines) <= 1: # If only header is present (or map_list_data was effectively empty)
        await interaction.followup.send("Список карт содержит некорректные данные или пуст после обработки.", ephemeral=True)
        return
        
    final_response = "\n".join(response_lines)
    
    # Discord message length limit is 2000 characters.
    # If the message is too long, truncate it and add a note.
    if len(final_response) > 1980: # Using a buffer
        truncated_response = final_response[:1900] # Truncate to allow space for the note
        last_newline = truncated_response.rfind('\n') # Try to end on a full line
        if last_newline != -1:
            truncated_response = truncated_response[:last_newline]
        
        await interaction.followup.send(truncated_response + "\n\n**Примечание: Список был урезан, так как он слишком длинный.**", ephemeral=True)
        logger.warning("cmd_list_server_maps: Map list was too long and has been truncated.")
    else:
        await interaction.followup.send(final_response, ephemeral=True)

  except Exception as e:
    logger.error(f"Error in cmd_list_server_maps: {e}", exc_info=True)
    await interaction.followup.send("Произошла ошибка при получении списка карт.", ephemeral=True)

# !SECTION
