from dataclasses import dataclass
import requests
import aria2p
import re

session = requests.Session()
domain = "https://setup.rbxcdn.com/"
settings = None
aria2 = None

@dataclass
class Settings:
	mac: bool
	mac_arm64: bool
	channel: str
	domain: str
	deploy_file: str
	ignore: bool
	aria2_ip: str
	aria2_port: int	

@dataclass
class Version:
	fullstring: str
	type: str
	id: str
	deployDate: str
	manifest: str = None
	arm64: bool = False
	filePattern = re.compile("^([A-z0-9-]{1,}\.[A-z0-9]{1,})")
	
	def verifyAvailability(self, settings: Settings):
		if not settings.mac:
			return self.getManifest(settings)
		else:
			statusCode = session.get(f'{domain}{f"channel/{settings.channel}/" if settings.channel else ""}mac/{f"arm64/" if settings.mac_arm64 else ""}{self.id}-Roblox{"Studio" if "Studio" in self.type else ""}.dmg').status_code
			return statusCode == 200
	
	def getManifest(self, settings: Settings):
		meta = session.get(f'{domain}{f"channel/{settings.channel}/" if settings.channel else ""}{self.id}-rbxPkgManifest.txt')
		
		if meta.status_code != 200:
			print(f" (!) Meta grabbing for {self.id} (deployed at {self.deployDate}) failed")
			return None
		else:
			print(f" (*) Successfully grabbed meta for {self.id}, deployed at {self.deployDate}")
			self.manifest = meta.text
			return self.manifest
	
	def queueForDownload(self, settings: Settings, aria2: aria2p.API):
		outputFolder = f'{f"{settings.channel}/" if settings.channel else ""}{"mac/" if settings.mac else ""}{"arm64/" if self.arm64 else ""}'
		if not self.verifyAvailability(settings):
			print(f" (!) Existence validation for {self.id} (deployed at {self.deployDate}) failed")
			return
	
		# Roblox stores Mac clients very differently compared to Windows clients.
		# - Windows clients are split up into separate zip files depending on the type of data being stored.
		# - Mac clients are stored in one big zip file that is simply downloaded by the installer all in one go.
		if not settings.mac:
			print(f" (*) Sending manifests for version {self.id} to queue")
			aria2.add(f"{domain}{f'channel/{settings.channel}/' if settings.channel else ''}{self.id}-rbxPkgManifest.txt", options = {"out": f"{outputFolder}{self.id}/{self.id}-rbxPkgManifest.txt"})
			aria2.add(f"{domain}{f'channel/{settings.channel}/' if settings.channel else ''}{self.id}-rbxManifest.txt", options = {"out": f"{outputFolder}{self.id}/{self.id}-rbxManifest.txt"})
			
			print(f" (*) Sending files for version {self.id} to queue")
			for line in self.manifest.split('\n'):
				match = self.filePattern.search(line)					
				# This is a file, download it
				if match:
					print(f" (*) Sending file {match.group(1)} for version {self.id} to queue")
					aria2.add(f"{domain}{self.id}-{match.group(1)}", options = {"out": f"{outputFolder}{self.id}/{self.id}-{match.group(1)}"})
		else:
			print(f" (*) Sending files for version {self.id} to queue")
			if "Studio" in self.type:
				# Thank you to BRAVONATCHO for letting me know about this file
				aria2.add(f"{domain}{f'channel/{settings.channel}/' if settings.channel else ''}mac/{f'arm64/' if self.arm64 else ''}{self.id}-RobloxStudioApp.zip", options = {"out": f"{outputFolder}{self.id}/{self.id}-RobloxStudioApp.zip"})
				aria2.add(f"{domain}{f'channel/{settings.channel}/' if settings.channel else ''}mac/{f'arm64/' if self.arm64 else ''}{self.id}-RobloxStudio.zip", options = {"out": f"{outputFolder}{self.id}/{self.id}-RobloxStudio.zip"})
				aria2.add(f"{domain}{f'channel/{settings.channel}/' if settings.channel else ''}mac/{f'arm64/' if self.arm64 else ''}{self.id}-RobloxStudio.dmg", options = {"out": f"{outputFolder}{self.id}/{self.id}-RobloxStudio.dmg"})
			else:
				aria2.add(f"{domain}{f'channel/{settings.channel}/' if settings.channel else ''}mac/{f'arm64/' if self.arm64 else ''}{self.id}-Roblox.dmg", options = {"out": f"{outputFolder}{self.id}/{self.id}-Roblox.dmg"})
				aria2.add(f"{domain}{f'channel/{settings.channel}/' if settings.channel else ''}mac/{f'arm64/' if self.arm64 else ''}{self.id}-RobloxPlayer.zip", options = {"out": f"{outputFolder}{self.id}/{self.id}-RobloxPlayer.zip"})
