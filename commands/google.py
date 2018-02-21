"""
Commands that utilize Google APIs, and their related functions.
"""

import discord
from discord.ext import commands
import googlemaps
import os

from helpers import text_manipulation as text


class GoogleMaps:

    def __init__(self, bot):

        self._bot = bot
        self._maps = googlemaps.Client(key=os.environ["GOOGLE_MAPS_KEY"])

    def get_distance_time(self, start, end, mode):
        """
        Given start and end location, and the mode of travel, return distance and time to travel in a string.
        :param start: Str
        :param end: Str
        :param mode: Str
        :return: Str
        """
        result_dict = self._maps.distance_matrix(origins=start, destinations=end, units="metric", mode=mode)
        origin, destination = result_dict["origin_addresses"][0], result_dict["destination_addresses"][0]
        try:
            dis = result_dict["rows"][0]["elements"][0]["distance"]["text"]
            time = result_dict["rows"][0]["elements"][0]["duration"]["text"]
        except KeyError:
            reply = "No results from Google."
        else:
            reply = "From {o} to {d}\n{dis}\n{time}".format(o=origin, d=destination, dis=dis, time=time)
        return reply

    @commands.command(pass_context=True)
    async def distance(self, context, start, end, *args):
        reply = self.get_distance_time(start, end, "driving")
        await self._bot.send_message(context.message.channel, text.codeblock(reply))

    @commands.command(pass_context=True)
    async def makeit(self, context, *args):
        """
        Joke command. Doesn't work very well because Google's data isn't precise.
        """

        possible = "No! You can't make it in 10 minutes."

        string = " ".join(args)
        if " to " in string:
            start, end = string.split(" to ")
        else:
            start, end = string.split(" ")

        dis_and_time = self.get_distance_time(start, end, "walking").split("\n")[1:]
        if "min" in dis_and_time[1] and int(dis_and_time[1].split(" ")[-2]) <= 10:
            possible = "Yes! You can make it in 10 minutes."

        reply = possible + "\n" + ", ".join(dis_and_time)
        await self._bot.send_message(context.message.channel, text.codeblock(reply))

    @commands.command(pass_context=True)
    async def nearby(self, context, query, *args):
        """
        Given a one-word query (e.g. DepartmentStores) and a location, return POIs near that location.
        Ignores explicitly closed POIs.
        """

        location = " ".join(args)

        longlat = self._maps.geocode(location)[0]["geometry"]["location"]
        readable_location = self._maps.geocode(location)[0]["formatted_address"]
        result_dict = self._maps.places(query=query, location=longlat)

        embeded_object = discord.Embed(title="Near {address}".format(address=readable_location), color=0x00ff00)
        num_places = 10

        for place in result_dict["results"]:
            num_places -= 1
            if "opening_hours" in place and place["opening_hours"]["open_now"] is False:
                pass
                # ignore everything that is certainly closed
            else:
                name = place["name"]
                address = place["formatted_address"].split(", ")[0]  # ignore the city, postal code, etc
                if "rating" in place:
                    rating = place["rating"]
                    entry = "{address}, Rating: {rating}/5".format(address=address, rating=rating)
                else:
                    entry = address
                embeded_object.add_field(name=name, value=entry, inline=False)
            if num_places == 0:
                break

        await self._bot.send_message(context.message.channel, embed=embeded_object)
