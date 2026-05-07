# mikubot
A basic discord music bot made using the discord-py module. 
This project was mainly made to learn some python basics and practice version control.

Uses yt-dlp and ffmpeg to stream music directly from youtube, so no file download necessary!
Commands are stored in discord-py cogs, allowing for hot swapping.

Command list:

join - join's the user's current voice channel

leave - disconnects the bot from its current voice channel

play - plays a song from url or searches youtube for the provided query

pause - pauses the currently playing song

resume - resumes paused playback

stop - stops playback

now-playing - shows information about current playback

play-next - plays the next song in play queue manually

queue - shows what songs are currently in play queue

remove-from-queue - removes the selected song from the play queue

repeat - enables looping for the current song

avatar - displays the selected user's avatar

jimboards - shows the top 10 most fire emoji reacted messages

Dev Commands:

reload-cog - reloads the specified command cog for testing

