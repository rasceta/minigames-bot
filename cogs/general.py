import discord
import util
import asyncio

from discord.ext import commands, tasks

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description="Shows the help menu or information for a specific command when specified.",
        usage="help <command>",
        aliases=["h", "commands"],
    )
    async def help(self, ctx, *, command: str = None):
        member = ctx.author
        if command:
            command = self.bot.get_command(command.lower())
            if not command:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"That command does not exist. Use `{ctx.prefix}help` to see all the commands."
                    )
                )
                return
            embed = discord.Embed(
                title=f"Command Help ({command.name})", 
                description=command.description
            )
            embed.add_field(name="Usage", value=f"```{ctx.prefix}{command.usage}```", inline=False)
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Command Help",
            description=f"Type `{ctx.prefix}help <commmand_name>` to see its information"
        )
        embed.add_field(
            name="General", 
            value="`help`, `daily`, `donate`, `lastcount`, `leaderboard`, `purchase`, `shop`, `wallet`, `weekly`", 
            inline=False
        )
        if discord.utils.find(lambda r: r.name == "Game Master", member.roles):
            embed.add_field(
                name="Game Master", 
                value="`addcoins`, `resetcount`, `startcount`, `stopcount`",
                inline=False
        )
        if member.guild_permissions.administrator:
            embed.add_field(name="Admin", value="`send`, `resetdaily`, `resetweekly`", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong!")

def setup(bot):
    bot.add_cog(General(bot))