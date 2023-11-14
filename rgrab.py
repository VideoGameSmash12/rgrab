# - rgrab v1.7 -
# Written by videogamesm12

print("                    _    ")
print("  _ _ __ _ _ _ __ _| |__ ")
print(" | '_/ _` | '_/ _` | '_ \\")
print(" |_| \__, |_| \__,_|_.__/")
print("     |___/ ")
print(" ========================")
#---------------------------------
print(" * Setting up dependencies...")
#--
from dataclasses import dataclass
import pathlib
import requests
import re
import os
import aria2p
import json
import argparse
from concurrent.futures import ThreadPoolExecutor
#---------------------------------
print(" * Reading command-line arguments (if any)...")
#--
parser = argparse.ArgumentParser(description = "Scrape Roblox's setup servers for client versions.")
parser.add_argument("-d", "--domain", default = "https://setup.rbxcdn.com/", help = "Sets the domain that the script will grab versions from. Unless you're scraping something from LouBu, there is no need to set this.")
parser.add_argument("-c", "--channel", default = None, help = "Sets the channel that the script will grab versions from.")
parser.add_argument("-mn", "--manual", action = 'store_true', default = False, help = "Attempts to query additional endpoints other than DeployHistory to find versions.")
parser.add_argument("-dhf", "--deploy_history_file", action = 'store', default = None, help = "If specified, reads the file with the same name as the DeployHistory instead of trying to get the latest one. Useful for getting clients from channels with previously wiped deploy histories.")
parser.add_argument("-m", "--mac", action = 'store_true', default = False, help = "Scrape versions in a way that properly grabs Mac clients.")
parser.add_argument("-nd", "--no_deploy_history", action = 'store_true', default = False, help = "Disables scraping from DeployHistory.txt.")
parser.add_argument("-di", "--dont_ignore_versions_after_parsed", action = 'store_true', default = False, help = "Don't ignore versions found during the parsing process in future sessions.")
parser.add_argument("-ai", "--aria2c_ip", action = 'store', default = "127.0.0.1", help = "The IP address of the aria2c daemon to connect to.")
parser.add_argument("-ap", "--aria2c_port", action = 'store', default = 6800, help = "The port of the aria2c daemon to connect to.")
args = parser.parse_args()
#--
domain = args.domain
channel = args.channel
mac = args.mac
ignoreVersions = not args.dont_ignore_versions_after_parsed
useDeployHistory = not args.no_deploy_history
daemonSettings = {
	"ip": args.aria2c_ip,
	"port": args.aria2c_port
}
manual = args.manual
deployHistoryFile = args.deploy_history_file
#--
print(" * Applying command-line options (if any)...")
outputFolder = ""
if channel:
	domain = f"{domain}channel/{channel}/"
	outputFolder = f"{channel}/"
if mac:
	domain = f"{domain}mac/"
	outputFolder = f"{outputFolder}mac/"
#--
print(" * Setting up internal variables...")
#--
pattern = re.compile("^New (WindowsPlayer|Studio|Studio64|Client) (version-[A-Fa-f0-9]{16}) at ([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4} [0-9]{1,2}:[0-9]{2}:[0-9]{2} (AM|PM))(, file ver(s)?ion: [0-9], [0-9]{1,}, 0, [0-9]{1,})?(, git hash: ([A-z0-9]{1,} ))?...(Done!)?")
filePattern = re.compile("^([A-z0-9-]{1,}\.[A-z0-9]{1,})")
session = requests.Session()
#--
aria2 = aria2p.API(
	aria2p.Client(
		host = f"http://{daemonSettings['ip']}",
		port = daemonSettings['port']
	)
)
#--
versions = []
ignore = []
#---------------------------------
print(" * Setting up thread pool...")
#--
executor = ThreadPoolExecutor(10)
#---------------------------------
print(" * Setting up internal classes...")
#--
@dataclass
class Version:
	fullstring: str
	type: str
	id: str
	deployDate: str
	manifest: str = None
	
	def verifyAvailability(self):
		if not mac:
			return self.getManifest()
		else:
			statusCode = session.get(f"{domain}{self.id}-Roblox{'Studio' if 'Studio' in self.type else ''}.dmg").status_code	
			return statusCode == 200
	
	def getManifest(self):
		meta = session.get(f"{domain}{self.id}-rbxPkgManifest.txt")
		
		if meta.status_code != 200:
			print(f" - Meta grabbing for {self.id} (deployed at {self.deployDate}) failed")
			return None
		else:
			print(f" * Successfully grabbed meta for {self.id}, deployed at {self.deployDate}")
			self.manifest = meta.text
			return self.manifest
	
	def queueForDownload(self):
		if not self.verifyAvailability():
			print(f" - Existence validation for {self.id} (deployed at {self.deployDate}) failed")
			return
	
		# Roblox stores Mac clients very differently compared to Windows clients.
		# - Windows clients are split up into separate zip files depending on the type of data being stored.
		# - Mac clients are stored in one big zip file that is simply downloaded by the installer all in one go.
		if not mac:
			print(f" * Sending manifests for version {self.id} to queue")
			aria2.add(f"{domain}{self.id}-rbxPkgManifest.txt", options = {"out": f"{outputFolder}{self.id}/{self.id}-rbxPkgManifest.txt"})
			aria2.add(f"{domain}{self.id}-rbxManifest.txt", options = {"out": f"{outputFolder}{self.id}/{self.id}-rbxManifest.txt"})
			
			print(f" * Sending files for version {self.id} to queue")
			for line in self.manifest.split('\n'):
				match = filePattern.search(line)					
				# This is a file, download it
				if match:
					print(f" * Sending file {match.group(1)} for version {self.id} to queue")
					aria2.add(f"{domain}{self.id}-{match.group(1)}", options = {"out": f"{outputFolder}{self.id}/{self.id}-{match.group(1)}"})
		else:
			print(f" * Sending files for version {self.id} to queue")
			if "Studio" in self.type:
				# Thank you to BRAVONATCHO for letting me know about this file
				aria2.add(f"{domain}{self.id}-RobloxStudioApp.zip", options = {"out": f"{outputFolder}{self.id}/{self.id}-RobloxStudioApp.zip"})
				aria2.add(f"{domain}{self.id}-RobloxStudio.zip", options = {"out": f"{outputFolder}{self.id}/{self.id}-RobloxStudio.zip"})
				aria2.add(f"{domain}{self.id}-RobloxStudio.dmg", options = {"out": f"{outputFolder}{self.id}/{self.id}-RobloxStudio.dmg"})
			else:
				aria2.add(f"{domain}{self.id}-Roblox.dmg", options = {"out": f"{outputFolder}{self.id}/{self.id}-Roblox.dmg"})
				aria2.add(f"{domain}{self.id}-RobloxPlayer.zip", options = {"out": f"{outputFolder}{self.id}/{self.id}-RobloxPlayer.zip"})
#---------------------------------
print(" * Setting up internal methods...")
#--
def queueIfPresent(version):
	try:
		version.queueForDownload()
	except Exception as ex:
		print("FUCK", ex)
#--
def findVersions(domain):
	print(" STAGE 1 - FINDING VERSIONS")
	print(" ==========================")
	#--
	if useDeployHistory:
		# If the file has been specified and it exists, we'll use it as our DeployHistory.txt instead of getting the latest version
		# This is useful in case you want to get clients from channels with previously wiped DeployHistory.txt files
		if deployHistoryFile and os.path.exists(deployHistoryFile):
			print(" * Reading manually specified file as DeployHistory.txt...")
			history = open(deployHistoryFile, "r").readlines()
		else:
			print(f" * Grabbing {domain}DeployHistory.txt from online...")
			history = session.get(f"{domain}DeployHistory.txt").text.split('\n')
		
		print(f" * Parsing...")
		for line in history:
			match = pattern.search(line)
			
			# This is a valid version entry, send it if it isn't blacklisted
			if match and match.group(2) not in ignore:
				version = Version(line, match.group(1), match.group(2), match.group(3))
				versions.append(version)
				
				if ignoreVersions:
					ignore.append(match.group(2))
	
	# TODO: Improve this later
	if manual:
		print(f" * Grabbing the latest version of the game by checking endpoints...")
		
		if mac:
			studioVersion = session.get(f"{domain}versionStudio").text
			if "version-" in studioVersion and studioVersion not in ignore:
				version = Version(studioVersion, "Studio", studioVersion, "Unspecified")
				versions.append(version)
				
				if ignoreVersions:
					ignore.append(studioVersion)
			
			playerVersion = session.get(f"{domain}version").text
			if "version-" in playerVersion and playerVersion not in ignore:
				version = Version(playerVersion, "Client", playerVersion, "Unspecified")
				versions.append(version)
				
				if ignoreVersions:
					ignore.append(playerVersion)
			
		else:
			studio64Version = session.get(f"{domain}versionQTStudio").text
			if "version-" in studio64Version and studio64Version not in ignore:
				version = Version(studio64Version, "Studio64", studio64Version, "Unspecified")
				versions.append(version)
				
				if ignoreVersions:
					ignore.append(studio64Version)
			
			playerVersion = session.get(f"{domain}version").text
			if "version-" in playerVersion and playerVersion not in ignore:
				version = Version(playerVersion, "WindowsPlayer", playerVersion, "Unspecified")
				versions.append(version)
				
				if ignoreVersions:
					ignore.append(playerVersion)
	
	if ignoreVersions:
		saveIgnore()
	
	print(f" * Parsing complete.")
	print(f"")
#--
def queueVersions():
	print(" STAGE 2 - THE MEAT")
	print(" ================================")
	print(" * Sending all versions to the thread pool to be queued...")
	executor.map(queueIfPresent, versions)
	print(" * Done!")
#--
def loadIgnore():
	print(" * Loading version blacklist...")
	try:
		with open("ignore.json", "r") as ignoreList:
			ignore.extend(json.loads(ignoreList.read()))
	except Exception as ex:
		print(" - Failed to load blacklist!")
		print(" - Details:", ex)

def saveIgnore():
	print(" * Saving new version blacklist...")
	try:
		with open("ignore.json", "w") as newList:
			json.dump(ignore, newList)
		print(" * Blacklist saved.")
	except Exception as ex:
		print(" - Failed to save blacklist!")
		print(" - Details:", ex)
#--
if os.path.exists("ignore.json"):
	loadIgnore()
#---------------------------------
print(" * Done!")
print("")
#---------------------------------
findVersions(domain)
queueVersions()
