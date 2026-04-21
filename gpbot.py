import discord
from discord.ext import commands
import json
import os
from datetime import datetime

# basic bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "ghost_pings.json"


# load saved data or make empty
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# save data to file
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


@bot.event
async def on_ready():
    print(f"bot is online as {bot.user}")


# catches ghost pings (mention then delete)
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    # ignore if no mentions
    if not message.mentions:
        return

    data = load_data()
    guild_id = str(message.guild.id)

    if guild_id not in data:
        data[guild_id] = {}

    user_id = str(message.author.id)

    if user_id not in data[guild_id]:
        data[guild_id][user_id] = {
            "count": 0,
            "logs": []
        }

    mentioned_users = [member.name for member in message.mentions]

    # add ghost ping
    data[guild_id][user_id]["count"] += 1
    data[guild_id][user_id]["logs"].append({
        "content": message.content,
        "mentions": mentioned_users,
        "channel": message.channel.name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    save_data(data)

    # message to show who 
    embed = discord.Embed(
        title="ghost pinger ",
        description=f"{message.author.mention} tried to ghost ping",
    )
    embed.add_field(name="who got pinged", value=", ".join(mentioned_users), inline=False)
    embed.add_field(name="deleted message", value=message.content if message.content else "[no text]", inline=False)
    embed.add_field(name="channel", value=message.channel.mention, inline=False)

    await message.channel.send(embed=embed)


# check ghost pings
@bot.command()
async def ghosts(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    guild_id = str(ctx.guild.id)

    count = 0
    if guild_id in data and str(member.id) in data[guild_id]:
        count = data[guild_id][str(member.id)]["count"]

    await ctx.send(f"{member.mention} has {count} ghost ping(s)")


# leaderboard
@bot.command()
async def ghostlb(ctx):
    data = load_data()
    guild_id = str(ctx.guild.id)

    if guild_id not in data or not data[guild_id]:
        await ctx.send("no ghost pings yet")
        return

    leaderboard = sorted(
        data[guild_id].items(),
        key=lambda item: item[1]["count"],
        reverse=True
    )[:10]

    embed = discord.Embed(
        title="ghost ping leaderboard",
        description="top offenders lmao"
    )

    for index, (user_id, info) in enumerate(leaderboard, start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.name if member else "unknown"
        embed.add_field(
            name=f"#{index} - {name}",
            value=f"{info['count']} ghost ping(s)",
            inline=False
        )

    await ctx.send(embed=embed)


# recent logs
@bot.command()
async def ghostlog(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    guild_id = str(ctx.guild.id)

    if guild_id not in data or str(member.id) not in data[guild_id]:
        await ctx.send("no logs found")
        return

    logs = data[guild_id][str(member.id)]["logs"][-5:]

    embed = discord.Embed(
        title=f"recent ghost pings for {member}",
    )

    for i, log in enumerate(logs, start=1):
        embed.add_field(
            name=f"log {i}",
            value=(
                f"time: {log['time']}\n"
                f"channel: {log['channel']}\n"
                f"pinged: {', '.join(log['mentions'])}\n"
                f"msg: {log['content'] if log['content'] else '[no text]'}"
            ),
            inline=False
        )

    await ctx.send(embed=embed)


bot.run("YOUR_BOT_TOKEN")
