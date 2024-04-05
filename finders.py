import json
import re
import requests
import os
from commons import *

class Finder:
	def findVersions(self, settings: Settings, ignore: list) -> list:
		""" Returns a list of version hashes to send to the database. """
		pass

class LatestFinder(Finder):
	endpoint = None

	def __init__(self, endpoint: str = "https://clientsettings.roblox.com/v2/client-version/"):
		self.endpoint = endpoint

	def findVersions(self, settings: Settings, ignore: list) -> list:
		print(f" (*) Grabbing the latest known client...")
		versions = []
		
		if settings.mac_arm64:
			print(" (!) Skipping grabbing the latest version as arm64 is enabled and there isn't a known way to grab arm64 clients with this method at this moment in time.")
			return []

		# Mac clients
		if settings.mac:
			macPlayerResponse = json.loads(session.get(f'{self.endpoint}MacPlayer{f"/channel/{settings.channel}" if settings.channel else ""}').text)
			macStudioResponse = json.loads(session.get(f'{self.endpoint}MacStudio{f"/channel/{settings.channel}" if settings.channel else ""}').text)
			
			# Did an error occur while trying to grab the clients?
			if "errors" in macPlayerResponse or "errors" in macStudioResponse:
				print(f' (!) Unable to grab latest version from the default endpoint: {macPlayerResponse["errors"][0]["message"]}')
				return []
			else:
				macPlayerVersion = macPlayerResponse["clientVersionUpload"]
				macStudioVersion = macStudioResponse["clientVersionUpload"]
				
				# Studio
				if macStudioVersion not in ignore:
					version = Version(macStudioVersion, "Studio", macStudioVersion, "Unspecified")
					versions.append(version)
					
					if settings.ignore:
						ignore.append(macStudioVersion)
				
				# Client
				if macPlayerVersion not in ignore:
					version = Version(macPlayerVersion, "Client", macPlayerVersion, "Unspecified")
					versions.append(version)
					
					if settings.ignore:
						ignore.append(macPlayerVersion)
		# Windows clients
		else:
			winPlayerResponse = json.loads(session.get(f'{self.endpoint}WindowsPlayer{f"/channel/{settings.channel}" if settings.channel else ""}').text)
			winStudioLegacyResponse = json.loads(session.get(f'{self.endpoint}WindowsStudio{f"/channel/{settings.channel}" if settings.channel else ""}').text) # Legacy, not updated anymore but still included anyways
			winStudio64Response = json.loads(session.get(f'{self.endpoint}WindowsStudio64{f"/channel/{settings.channel}" if settings.channel else ""}').text)
			
			# Did an error occur while trying to grab the clients?
			if "errors" in winPlayerResponse or "errors" in winStudioLegacyResponse or "errors" in winStudio64Response:
				print(f' (!) Unable to grab latest version from the default endpoint: {winPlayerResponse["errors"][0]["message"]}')
				return []
			else:
				winPlayerVersion = winPlayerResponse["clientVersionUpload"]
				winStudioLegacyVersion = winStudioLegacyResponse["clientVersionUpload"]
				winStudio64Version = winStudio64Response["clientVersionUpload"]

				# WindowsPlayer
				if winPlayerVersion not in ignore:
					version = Version(winPlayerVersion, "WindowsPlayer", winPlayerVersion, "Unspecified")
					versions.append(version)
					
					if settings.ignore:
						ignore.append(winPlayerVersion)
				
				# Studio (legacy)
				if winStudioLegacyVersion not in ignore:
					version = Version(winStudioLegacyVersion, "Studio", winStudioLegacyVersion, "Unspecified")
					versions.append(version)
					
					if settings.ignore:
						ignore.append(winStudioLegacyVersion)
				
				# Studio64
				if winStudio64Version not in ignore:
					version = Version(winStudio64Version, "Studio64", winStudio64Version, "Unspecified")
					versions.append(version)
					
					if settings.ignore:
						ignore.append(winStudio64Version)
						
		return versions	

class LegacyFinder(LatestFinder):
	def __init__(self, endpoint: str = "https://setup.rbxcdn.com/"):
		self.endpoint = endpoint

	def findVersions(self, settings: Settings, ignore: list) -> list:
		print(f" * Grabbing clients from fallback endpoints (may not be up to date)...")
		versions = []
		
		if settings.mac:
			studioVersion = session.get(f'{self.endpoint}{f"channel/{settings.channel}/" if settings.channel else ""}mac/versionStudio').text
			if "version-" in studioVersion and studioVersion not in ignore:
				version = Version(studioVersion, "Studio", studioVersion, "Unspecified")
				versions.append(version)
				
				if settings.ignore:
					ignore.append(studioVersion)
			
			playerVersion = session.get(f'{self.endpoint}{f"channel/{settings.channel}/" if settings.channel else ""}mac/version').text
			if "version-" in playerVersion and playerVersion not in ignore:
				version = Version(playerVersion, "Client", playerVersion, "Unspecified")
				versions.append(version)
				
				if settings.ignore:
					ignore.append(playerVersion)
		else:
			studio64Version = session.get(f'{self.endpoint}{f"channel/{settings.channel}/" if settings.channel else ""}versionQTStudio').text
			if "version-" in studio64Version and studio64Version not in ignore:
				version = Version(studio64Version, "Studio64", studio64Version, "Unspecified")
				versions.append(version)
				
				if settings.ignore:
					ignore.append(studio64Version)
			
			playerVersion = session.get(f'{self.endpoint}{f"channel/{settings.channel}/" if settings.channel else ""}version').text
			if "version-" in playerVersion and playerVersion not in ignore:
				version = Version(playerVersion, "WindowsPlayer", playerVersion, "Unspecified")
				versions.append(version)
				
				if settings.ignore:
					ignore.append(playerVersion)
		
		return versions

class LuobuFinder(LatestFinder):
	def findVersions(self, settings: Settings, ignore: list) -> list:
		print(f" * Grabbing the latest known Luobu client...")
		versions = []

		if settings.mac_arm64:
			print(" (!) Skipping grabbing the latest version as arm64 is enabled and there isn't a known way to grab arm64 clients with this method at this moment in time.")
			return []
	
		# Mac clients
		if settings.mac:
			macStudioLBResponse = json.loads(session.get(f'{self.endpoint}MacStudioCJV{f"/channel/{settings.channel}" if settings.channel else ""}').text)
			
			if "errors" in macStudioLBResponse:
				print(f' (!) Unable to grab latest Luobu version from the endpoint: {macStudioLBResponse["errors"][0]["message"]}')
				return []
			else:
				macStudioLBVersion = macStudioLBResponse["clientVersionUpload"]
				if macStudioLBVersion not in ignore:
					version = Version(macStudioLBVersion, "StudioCJV", macStudioLBVersion, "Unspecified", False)
					versions.append(version)
					
					if settings.ignore:
						ignore.append(macStudioLBVersion)
		# Windows clients
		else:
			winStudio64LBResponse = json.loads(session.get(f'{self.endpoint}WindowsStudio64CJV{f"/channel/{settings.channel}" if settings.channel else ""}').text)
			winStudioLegacyLBResponse = json.loads(session.get(f'{self.endpoint}WindowsStudioCJV{f"/channel/{settings.channel}" if settings.channel else ""}').text)
			
			if "errors" in winStudio64LBResponse:
				print(f' (!) Unable to grab latest Luobu version from the endpoint: {winStudio64LBResponse["errors"][0]["message"]}')
			else:
				winStudio64LBVersion = winStudio64LBResponse["clientVersionUpload"]
				winStudioLegacyLBVersion = winStudioLegacyLBResponse["clientVersionUpload"]

				if winStudio64LBVersion not in ignore:
					version = Version(winStudio64LBVersion, "Studio64CJV", winStudio64LBVersion, "Unspecified")
					versions.append(version)
					
					if settings.ignore:
						ignore.append(winStudio64LBVersion)

				if winStudioLegacyLBVersion not in ignore:
					version = Version(winStudioLegacyLBVersion, "StudioCJV", winStudioLegacyLBVersion, "Unspecified")
					versions.append(version)
					
					if settings.ignore:
						ignore.append(winStudioLegacyLBVersion)
						
		return versions

class DeployFinder(Finder):
	pattern = re.compile("^New (WindowsPlayer|Studio|Studio64|Client) (version-[A-Fa-f0-9]{16}) at ([0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4} [0-9]{1,2}:[0-9]{2}:[0-9]{2} (AM|PM))(, file ver(s)?ion: [0-9], [0-9]{1,}, 0, [0-9]{1,})?(, git hash: ([A-z0-9]{1,} ))?...(Done!)?")
	deployHistoryFile = None
	
	def __init__(self, deployHistoryFile: str = None):
		self.deployHistoryFile = deployHistoryFile
	
	def findVersions(self, settings: Settings, ignore: list) -> list:
		versions = []
	
		# If the file has been specified and it exists, we'll use it as our DeployHistory.txt instead of getting the latest version
		# This is useful in case you want to get clients from channels with previously wiped DeployHistory.txt files
		if settings.deploy_file and os.path.exists(settings.deploy_file):
			print(" (*) Reading manually specified file as DeployHistory.txt...")
			history = open(settings.deploy_file, "r").readlines()
		else:
			print(f' (*) Grabbing {settings.domain}{f"channel/{settings.channel}/" if settings.channel else ""}{f"mac/" if settings.mac else ""}{f"arm64/" if settings.mac_arm64 else ""}DeployHistory.txt from online...')
			history = session.get(f'{settings.domain}{f"channel/{settings.channel}/" if settings.channel else ""}{f"mac/" if settings.mac else ""}{f"arm64/" if settings.mac_arm64 else ""}DeployHistory.txt').text.split('\n')
		
		print(f" (*) Parsing...")
		for line in history:
			match = self.pattern.search(line)
			
			# This is a valid version entry, send it if it isn't blacklisted
			if match and match.group(2) not in ignore:
				version = Version(line, match.group(1), match.group(2), match.group(3), settings.mac_arm64)
				versions.append(version)
				
				if settings.ignore:
					ignore.append(match.group(2))
					
		return versions
