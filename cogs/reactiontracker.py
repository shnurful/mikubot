import asyncio
import sqlite3
from typing import Optional

import discord
from discord.ext import commands


class ReactionTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect("messages.db")
        self.db.row_factory = sqlite3.Row
        self._startup_sync_lock = asyncio.Lock()
        self._startup_sync_done = False
        self._init_db()

    def cog_unload(self):
        self.db.close()

    def _init_db(self):
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS reaction_messages (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                reaction_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                jumped_url TEXT NOT NULL,
                content TEXT DEFAULT ''
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS reaction_tracker_state (
                channel_id INTEGER PRIMARY KEY,
                last_scanned_message_id INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reaction_messages_user_count
            ON reaction_messages (author_id, reaction_count DESC)
            """
        )
        # Add content column if it doesn't exist (for existing databases)
        try:
            self.db.execute("ALTER TABLE reaction_messages ADD COLUMN content TEXT DEFAULT ''")
            self.db.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass

    async def _fetch_message(self, channel_id: int, message_id: int) -> Optional[discord.Message]:
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (discord.Forbidden, discord.HTTPException):
                return None

        try:
            return await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    def _total_reactions(self, message: discord.Message) -> int:
        return sum(r.count for r in message.reactions)

    def _is_fire_reaction(self, reaction) -> bool:
        # Only count fire emojis
        emoji_obj = getattr(reaction, "emoji", None)
        # Unicode emoji are plain strings
        if isinstance(emoji_obj, str):
            return emoji_obj == "🔥" or emoji_obj == ":fire:"

        # For PartialEmoji/Emoji objects, check the name
        name = getattr(emoji_obj, "name", None)
        return name in ("fire", "🔥")

    def _total_reactions(self, message: discord.Message) -> int:
        # Count only fire reactions
        return sum(r.count for r in message.reactions if self._is_fire_reaction(r))

    def _upsert_message(self, message: discord.Message, reaction_count: int):
        if message.guild is None:
            return
        # If there are no fire reactions, remove any existing row and skip inserting.
        if reaction_count <= 0:
            self.db.execute(
                "DELETE FROM reaction_messages WHERE message_id = ?",
                (message.id,),
            )
            self.db.commit()
            return

        self.db.execute(
            """
            INSERT INTO reaction_messages (
                message_id, channel_id, guild_id, author_id, reaction_count, created_at, jumped_url, content
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(message_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                guild_id = excluded.guild_id,
                author_id = excluded.author_id,
                reaction_count = excluded.reaction_count,
                created_at = excluded.created_at,
                jumped_url = excluded.jumped_url,
                content = excluded.content
            """,
            (
                message.id,
                message.channel.id,
                message.guild.id,
                message.author.id,
                reaction_count,
                message.created_at.isoformat(),
                message.jump_url,
                message.content[:2000],  # Truncate to 2000 chars for Discord embed limits
            ),
        )
        self.db.commit()

    def _set_last_scanned_id(self, channel_id: int, message_id: int):
        self.db.execute(
            """
            INSERT INTO reaction_tracker_state (channel_id, last_scanned_message_id)
            VALUES (?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET
                last_scanned_message_id = excluded.last_scanned_message_id
            """,
            (channel_id, message_id),
        )
        self.db.commit()

    def _get_last_scanned_id(self, channel_id: int) -> int:
        row = self.db.execute(
            "SELECT last_scanned_message_id FROM reaction_tracker_state WHERE channel_id = ?",
            (channel_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    async def _sync_channel_history(self, channel: discord.TextChannel):
        print(f"[ReactionTracker] Syncing history for {channel.name} ({channel.id})")
        last_scanned_id = self._get_last_scanned_id(channel.id)
        newest_seen = last_scanned_id

        history_kwargs = {"limit": None, "oldest_first": True}
        if last_scanned_id > 0:
            history_kwargs["after"] = discord.Object(id=last_scanned_id)

        try:
            count = 0
            async for message in channel.history(**history_kwargs):
                if message.author.bot:
                    newest_seen = max(newest_seen, message.id)
                    continue
                
                fire_count = self._total_reactions(message)
                self._upsert_message(message, fire_count)
                newest_seen = max(newest_seen, message.id)
                count += 1

            if newest_seen > 0:
                self._set_last_scanned_id(channel.id, newest_seen)
            print(f"[ReactionTracker] Synced {count} messages from {channel.name}")
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"[ReactionTracker] Error syncing {channel.name}: {e}")
            return

    async def _sync_all_channels(self):
        async with self._startup_sync_lock:
            if self._startup_sync_done:
                return

            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    await self._sync_channel_history(channel)

            self._startup_sync_done = True

    @commands.Cog.listener()
    async def on_ready(self):
        await self._sync_all_channels()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        self._upsert_message(message, self._total_reactions(message))
        last_scanned_id = self._get_last_scanned_id(message.channel.id)
        if message.id > last_scanned_id:
            self._set_last_scanned_id(message.channel.id, message.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        message = await self._fetch_message(payload.channel_id, payload.message_id)
        if message is None or message.author.bot:
            return
        self._upsert_message(message, self._total_reactions(message))

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        message = await self._fetch_message(payload.channel_id, payload.message_id)
        if message is None or message.author.bot:
            return
        self._upsert_message(message, self._total_reactions(message))

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        message = await self._fetch_message(payload.channel_id, payload.message_id)
        if message is None or message.author.bot:
            return
        self._upsert_message(message, self._total_reactions(message))

    @commands.Cog.listener()
    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        message = await self._fetch_message(payload.channel_id, payload.message_id)
        if message is None or message.author.bot:
            return
        self._upsert_message(message, self._total_reactions(message))

    @commands.hybrid_command(
        name="jimboards",
        description="Show top 10 messages with the most :fire: reactions from a specific user",
    )
    async def top_reacted(
        self,
        ctx: commands.Context,
        user: Optional[discord.Member] = None,
    ):
        guild_id = ctx.guild.id if ctx.guild else 0

        if user is None:
            rows = self.db.execute(
                """
                SELECT message_id, reaction_count, jumped_url, content, author_id
                FROM reaction_messages
                WHERE guild_id = ?
                ORDER BY reaction_count DESC, message_id DESC
                LIMIT 10
                """,
                (guild_id,),
            ).fetchall()
            target_label = "Server"
        else:
            rows = self.db.execute(
                """
                SELECT message_id, reaction_count, jumped_url, content, author_id
                FROM reaction_messages
                WHERE author_id = ? AND guild_id = ?
                ORDER BY reaction_count DESC, message_id DESC
                LIMIT 10
                """,
                (user.id, guild_id),
            ).fetchall()
            target_label = user.display_name

        if not rows:
            if user is None:
                await ctx.send("No tracked messages found for this server yet.")
            else:
                await ctx.send(f"No tracked messages found for {user.mention} yet.")
            return

        embed = discord.Embed(
            title=f"{target_label}",
            color=discord.Color.blurple(),
        )

        for idx, row in enumerate(rows, start=1):
            content = row['content'] or "(no content)"
            if len(content) > 100:
                content = content[:97] + "..."
            
            if user is None:
                # show author name if no user arg
                try:
                    author = await self.bot.fetch_user(row['author_id'])
                    author_name = author.display_name
                except discord.NotFound:
                    author_name = f"Unknown User"
                field_name = f"{author_name}\n {content} - {row['reaction_count']} 🔥"
            else:
                field_name = f"{content} - {row['reaction_count']} 🔥"
            
            embed.add_field(
                name=field_name,
                value=f"[Jump to message]({row['jumped_url']})",
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionTracker(bot))
