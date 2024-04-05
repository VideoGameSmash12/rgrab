# - rgrab v2.0 -
# Written by videogamesm12

print("                    _    ")
print("  _ _ __ _ _ _ __ _| |__ ")
print(" | '_/ _` | '_/ _` | '_ \\")
print(" |_| \__, |_| \__,_|_.__/")
print("     |___/ ")
print(" ========================")
#---------------------------------
print(" (*) Setting up dependencies...")
#--
from commons import *
from finders import *
import aria2p
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
#---------------------------------
print(" (*) Reading command-line arguments (if any)...")
#--
parser = argparse.ArgumentParser(description = "Scrape Roblox's setup servers for client versions.")
parser.add_argument("-d", "--domain", default = "https://setup.rbxcdn.com/", help = "Sets the domain that the script will grab versions from. Unless you're scraping something from LouBu, there is no need to set this.")
parser.add_argument("-c", "--channel", default = None, help = "Sets the channel that the script will grab versions from.")
parser.add_argument("-dp", "--deployhistory", action = 'store_true', default = False, help = "Use an endpoint provided by Roblox as reference to build a list of all known clients.")
parser.add_argument("-dpf", "--deployhistory_file", default = None, help = "If set, use a file instead of an endpoint as reference to build a list of all known clients.")
parser.add_argument("-l", "--latest", action = 'store_true', default = False, help = "Use an API provided by Roblox to find the latest clients.")
parser.add_argument("-lg", "--legacy", action = 'store_true', default = False, help = "Use a legacy API provided by Roblox to find the latest clients. Sometimes useful for grabbing hidden clients from private setup channels.")
parser.add_argument("-lu", "--luobu", action = 'store_true', default = False, help = "Use an API provided by Roblox to find the latest LuoBu clients, which are normally hidden from DeployHistory.txt")
#--
parser.add_argument("-m", "--mac", action = 'store_true', default = False, help = "Get Mac clients instead which are downloaded differently.")
parser.add_argument("-ma", "--arm64", action = 'store_true', default = False, help = "When getting Mac clients, download clients compiled for the arm64 CPU architecture.")
#--
parser.add_argument("-i", "--ignore", action = 'store_true', default = False, help = "Ignore clients retrieved by this session in the sessions that follow.")
#--
parser.add_argument("-ai", "--aria2_ip", default = "127.0.0.1", help = "The IP address of the aria2c daemon to connect to.")
parser.add_argument("-ap", "--aria2_port", default = 6800, help = "The port of the aria2c daemon to connect to.")
args = parser.parse_args()

finders = []
versions = []
executor = ThreadPoolExecutor(10)
ignore = []

def handleArgs(parsed: argparse.Namespace):
	#-- ENFORCEMENT -- #
	# Enforce the requirement of at least one finder.
	if not parsed.latest and not parsed.deployhistory and not parsed.latest and not parsed.legacy:
		print(" (X) You didn't specify what to use to find clients. Specify at least one of the following:  --deployhistory, --latest, --luobu, --legacy")
		return None
	
	if not parsed.mac and parsed.arm64:
		print(" (X) As of this version's release, no arm64-based clients for Windows exist and grabbing them isn't supported. When these do eventually exist, please create an issue on GitHub at https://www.github.com/VideoGameSmash12/rgrab")
		return None

	#-- FINDERS -- #
	if parsed.deployhistory:
		finders.append(DeployFinder())
	
	if parsed.latest:
		finders.append(LatestFinder())
	
	if parsed.legacy:
		finders.append(LegacyFinder())
	
	if parsed.luobu:
		finders.append(LuobuFinder())
	
	global settings
	settings = Settings(parsed.mac, parsed.arm64, parsed.channel, parsed.domain, parsed.deployhistory_file, parsed.ignore, parsed.aria2_ip, parsed.aria2_port)
	
	global aria2
	aria2 = aria2p.API(
		aria2p.Client(
			host = f"http://{settings.aria2_ip}",
			port = settings.aria2_port
		)
	)
	
	return 1337

def queueIfPresent(version: Version):
	try:
		version.queueForDownload(settings, aria2)
	except Exception as ex:
		print(f" (!) Failed to queue version {version.id} -", ex)
		
def loadBlacklist():
	print(" (*) Loading version blacklist...")
	try:
		with open("ignore.json", "r") as ignoreList:
			ignore.extend(json.loads(ignoreList.read()))
		print(" (*) Blacklist loaded.")
	except Exception as ex:
		print(f" (!) Failed to load version blacklist -", ex)
		
def saveBlacklist():
	print(" (*) Saving version blacklist...")
	try:	
		with open("ignore.json", "w") as newList:
			json.dump(ignore, newList)
		print(" (*) Blacklist saved.")
	except Exception as ex:
		print(f" (!) Failed to save version blacklist -", ex)

if handleArgs(args):
	# Load the blacklist if enabled
	if settings.ignore and os.path.exists("ignore.json"):
		loadBlacklist()

	# Get every version we can find
	for finder in finders:
		versions = versions + finder.findVersions(settings, ignore)

	# Save the blacklist if enabled
	if settings.ignore:
		saveBlacklist()

	# Queue everything
	executor.map(queueIfPresent, versions)

	if settings.ignore:
		with open("ignore.json", "r") as ignoreList:
			ignore.extend(json.loads(ignoreList.read()))
