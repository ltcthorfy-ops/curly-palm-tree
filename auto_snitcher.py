"""
AUTO SNITCHER - COMPLETE FIXED VERSION (450+ LINES)
Runs 24/7 - No browser needed
Full implementation with NopeCHA captcha solving
Longer waits for captcha solving
"""

import discord
import asyncio
import json
import requests
import base64
import time
import random
import re
import sys
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ============================================================
# CONFIGURATION CLASS
# ============================================================

class ConfigManager:
    """Handles loading and saving configuration"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Config file not found: {self.config_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in config file: {self.config_file}")
            sys.exit(1)
    
    def save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def get_token(self, index: int = 0) -> str:
        """Get token by index"""
        return self.config['tokens'][index]['token']
    
    def get_server_id(self) -> str:
        """Get first monitored server ID"""
        return list(self.config['monitored_servers'].keys())[0]
    
    def get_server_config(self, server_id: str) -> Dict:
        """Get server configuration"""
        return self.config['monitored_servers'][server_id]
    
    def get_nopecha_key(self) -> Optional[str]:
        """Get NopeCHA API key"""
        return self.config.get('nopecha_api_key')
    
    def get_general_settings(self) -> Dict:
        """Get general settings"""
        return self.config.get('general_settings', {})
    
    def get_processed_members(self, server_id: str) -> List[str]:
        """Get processed members list"""
        return self.config['monitored_servers'][server_id].get('processed_members', [])
    
    def add_processed_member(self, server_id: str, member_id: str) -> None:
        """Add member to processed list"""
        if 'processed_members' not in self.config['monitored_servers'][server_id]:
            self.config['monitored_servers'][server_id]['processed_members'] = []
        if member_id not in self.config['monitored_servers'][server_id]['processed_members']:
            self.config['monitored_servers'][server_id]['processed_members'].append(member_id)
            self.save_config()
    
    def get_invite_link(self, server_id: str) -> Optional[str]:
        """Get invite link for server"""
        return self.config['monitored_servers'][server_id].get('invite_link')
    
    def get_message(self, server_id: str) -> str:
        """Get DM message for server"""
        return self.config['monitored_servers'][server_id].get('message', 'Welcome!')

# ============================================================
# NOPECHA SOLVER CLASS WITH LONGER WAITS
# ============================================================

class NopeCHASolver:
    """NopeCHA API Solver - Auto solves captchas with longer waits"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.nopecha.com/solve"
        self.timeout = 180  # Increased to 3 minutes
        self.max_retries = 5  # Increased retries
    
    def solve_hcaptcha(self, sitekey: str, page_url: str = "https://discord.com/channels/@me") -> Optional[str]:
        """
        Solve hCaptcha using NopeCHA API with longer waits
        """
        for attempt in range(self.max_retries):
            try:
                print(f"   📤 NopeCHA attempt {attempt + 1}/{self.max_retries}")
                print(f"   📍 Sitekey: {sitekey[:20]}...")
                print(f"   ⏳ This may take 30-90 seconds...")
                
                payload = {
                    "type": "hcaptcha",
                    "sitekey": sitekey,
                    "url": page_url,
                    "api_key": self.api_key
                }
                
                response = requests.post(
                    self.base_url, 
                    json=payload, 
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'solution' in result:
                        solution = result['solution']
                        print(f"   ✅ NopeCHA solved: {solution[:30]}...")
                        return solution
                    elif 'error' in result:
                        print(f"   ❌ NopeCHA error: {result['error']}")
                        if attempt < self.max_retries - 1:
                            wait_time = 20
                            print(f"   ⏳ Waiting {wait_time} seconds before retry...")
                            time.sleep(wait_time)
                        continue
                elif response.status_code == 520:
                    print(f"   ⚠️ Rate limited (520)! Waiting 45 seconds...")
                    time.sleep(45)
                    continue
                elif response.status_code == 429:
                    print(f"   ⚠️ Rate limited (429)! Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                else:
                    print(f"   ❌ HTTP error: {response.status_code}")
                    if attempt < self.max_retries - 1:
                        wait_time = 15
                        print(f"   ⏳ Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"   ⏳ Timeout - waiting longer...")
                time.sleep(30)
                continue
            except Exception as e:
                print(f"   ❌ NopeCHA error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(15)
                continue
        
        print(f"   ❌ Failed to solve captcha after {self.max_retries} attempts")
        return None
    
    def solve_recaptcha(self, sitekey: str, page_url: str = "https://discord.com/channels/@me") -> Optional[str]:
        """Solve reCaptcha using NopeCHA"""
        try:
            payload = {
                "type": "recaptcha",
                "sitekey": sitekey,
                "url": page_url,
                "api_key": self.api_key
            }
            
            response = requests.post(self.base_url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if 'solution' in result:
                    return result['solution']
            return None
        except Exception as e:
            print(f"❌ NopeCHA reCaptcha error: {e}")
            return None
    
    def solve_image_captcha(self, image_base64: str) -> Optional[str]:
        """Solve image captcha using NopeCHA"""
        try:
            payload = {
                "type": "image",
                "image": image_base64,
                "api_key": self.api_key
            }
            
            response = requests.post(self.base_url, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if 'solution' in result:
                    return result['solution']
            return None
        except Exception as e:
            print(f"❌ NopeCHA image error: {e}")
            return None

# ============================================================
# DISCORD API HELPER CLASS
# ============================================================

class DiscordAPI:
    """Discord API helper for direct API calls"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://discord.com/api/v9"
        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def join_server(self, invite_code: str, captcha_key: Optional[str] = None) -> Tuple[bool, Dict]:
        """Join a server using invite code"""
        try:
            url = f"{self.base_url}/invites/{invite_code}"
            payload = {}
            
            if captcha_key:
                payload['captcha_key'] = captcha_key
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 400:
                data = response.json()
                if 'captcha_key' in data or 'captcha_sitekey' in data:
                    return False, {'captcha_required': True, 'data': data}
                return False, data
            else:
                return False, {'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def create_dm_channel(self, recipient_id: str) -> Tuple[bool, Dict]:
        """Create a DM channel with a user"""
        try:
            url = f"{self.base_url}/users/@me/channels"
            payload = {"recipient_id": recipient_id}
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 201:
                return True, response.json()
            else:
                return False, response.json()
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def send_message(self, channel_id: str, content: str, captcha_key: Optional[str] = None) -> Tuple[bool, Dict]:
        """Send a message to a channel"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/messages"
            payload = {"content": content}
            
            if captcha_key:
                payload['captcha_key'] = captcha_key
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                return False, response.json()
                
        except Exception as e:
            return False, {'error': str(e)}
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Get user information"""
        try:
            url = f"{self.base_url}/users/{user_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    def get_guild_info(self, guild_id: str) -> Optional[Dict]:
        """Get guild information"""
        try:
            url = f"{self.base_url}/guilds/{guild_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

# ============================================================
# TOKEN MANAGER CLASS
# ============================================================

class TokenManager:
    """Manages multiple Discord tokens with failover"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.tokens = config.get('tokens', [])
        self.token_status = {}
        self.active_tokens = []
        self.current_index = 0
        self.init_tokens()
    
    def init_tokens(self) -> None:
        """Initialize all tokens"""
        for i, token_data in enumerate(self.tokens):
            token = token_data['token']
            self.token_status[token] = {
                'index': i,
                'active': True,
                'locked': False,
                'limited': False,
                'dm_count': 0,
                'last_used': None,
                'name': token_data.get('name', f'Token {i+1}')
            }
            self.active_tokens.append(token)
        
        print(f'✅ Loaded {len(self.tokens)} tokens')
        for i, token_data in enumerate(self.tokens):
            print(f'  Token {i+1}: {token_data.get("name", f"Token {i+1}")}')
    
    def get_next_token(self) -> Optional[str]:
        """Get the next available token (round-robin)"""
        if not self.active_tokens:
            return None
        
        for _ in range(len(self.active_tokens)):
            token = self.active_tokens[self.current_index % len(self.active_tokens)]
            self.current_index += 1
            
            status = self.token_status[token]
            if status['active'] and not status['locked'] and not status['limited']:
                daily_limit = self.config['general_settings'].get('max_daily_dms_per_token', 50)
                if status['dm_count'] >= daily_limit:
                    continue
                return token
        
        return None
    
    def mark_token_used(self, token: str) -> None:
        """Mark token as used"""
        if token in self.token_status:
            self.token_status[token]['dm_count'] += 1
            self.token_status[token]['last_used'] = datetime.utcnow().isoformat()
    
    def mark_token_locked(self, token: str) -> None:
        """Mark token as locked/banned"""
        if token in self.token_status:
            self.token_status[token]['locked'] = True
            self.token_status[token]['active'] = False
            if token in self.active_tokens:
                self.active_tokens.remove(token)
            print(f'🔒 Token locked: {self.token_status[token]["name"]}')
    
    def mark_token_limited(self, token: str) -> None:
        """Mark token as rate limited"""
        if token in self.token_status:
            self.token_status[token]['limited'] = True
            print(f'⏳ Token limited: {self.token_status[token]["name"]}')
            threading.Timer(300, self.unlimit_token, args=[token]).start()
    
    def unlimit_token(self, token: str) -> None:
        """Unlimit a token after cooldown"""
        if token in self.token_status:
            self.token_status[token]['limited'] = False
            print(f'🔄 Token un-limited: {self.token_status[token]["name"]}')
    
    def get_status_report(self) -> str:
        """Get status report of all tokens"""
        report = []
        for token_data in self.tokens:
            token = token_data['token']
            status = self.token_status.get(token, {})
            report.append({
                'name': token_data.get('name', 'Unknown'),
                'active': status.get('active', False),
                'locked': status.get('locked', False),
                'limited': status.get('limited', False),
                'dm_count': status.get('dm_count', 0)
            })
        return json.dumps(report, indent=2)

# ============================================================
# MAIN AUTO SNITCHER CLASS
# ============================================================

class AutoSnitcher:
    """Main Auto Snitcher class"""
    
    def __init__(self, config_file: str = 'config.json'):
        # Load configuration
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.config
        
        # Initialize token manager
        self.token_manager = TokenManager(self.config)
        
        # Get server info
        self.server_id = self.config_manager.get_server_id()
        self.server_config = self.config_manager.get_server_config(self.server_id)
        self.message = self.config_manager.get_message(self.server_id)
        self.invite_link = self.config_manager.get_invite_link(self.server_id)
        
        # Initialize NopeCHA
        nopecha_key = self.config_manager.get_nopecha_key()
        self.nopecha = NopeCHASolver(nopecha_key) if nopecha_key else None
        
        # Discord client
        self.client = None
        self.processed_members = []
        self.running = True
        self.dm_count = 0
        
        # Print startup info
        self.print_startup_info()
    
    def print_startup_info(self) -> None:
        """Print startup information"""
        print("=" * 60)
        print("🤖 AUTO SNITCHER - FIXED VERSION")
        print("=" * 60)
        print(f"📡 Server ID: {self.server_id}")
        print(f"🔐 NopeCHA: {'ENABLED' if self.nopecha else 'DISABLED'}")
        print(f"📊 Tokens: {len(self.token_manager.tokens)}")
        print(f"⏳ Captcha timeout: 180 seconds")
        print("=" * 60)
    
    def save_processed(self) -> None:
        """Save processed members to config"""
        self.server_config['processed_members'] = self.processed_members
        self.config_manager.save_config()
    
    def is_member_processed(self, member_id: str) -> bool:
        """Check if member has been processed"""
        return member_id in self.processed_members
    
    def mark_member_processed(self, member_id: str) -> None:
        """Mark member as processed"""
        if member_id not in self.processed_members:
            self.processed_members.append(member_id)
            self.save_processed()
    
    async def send_dm(self, member, token: str) -> bool:
        """Send DM to a member using a token"""
        try:
            await member.send(self.message)
            self.dm_count += 1
            self.token_manager.mark_token_used(token)
            print(f"✅ DM sent to {member.name} (Total: {self.dm_count})")
            return True
            
        except discord.Forbidden:
            print(f"🚫 DMs disabled for {member.name}")
            return False
            
        except discord.HTTPException as e:
            error_str = str(e).lower()
            
            if "captcha" in error_str or "400" in error_str:
                print(f"🔐 Captcha required for {member.name}")
                
                if self.nopecha:
                    print(f"⏳ Waiting up to 180 seconds for captcha...")
                    solved = await self.solve_captcha_for_member(member, token)
                    if solved:
                        return True
                return False
            else:
                print(f"❌ HTTP error: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending DM: {e}")
            return False
    
    async def solve_captcha_for_member(self, member, token: str) -> bool:
        """Solve captcha for a member using NopeCHA with longer waits"""
        try:
            print(f"🔐 Solving captcha for {member.name}...")
            print(f"⏳ This may take 30-90 seconds. Please wait...")
            
            # Discord DM captcha sitekey
            sitekey = "a9b5fb07-92ff-493f-86fe-352a2803b3df"
            
            # Solve with NopeCHA
            solution = await asyncio.get_running_loop().run_in_executor(
                None,
                self.nopecha.solve_hcaptcha,
                sitekey
            )
            
            if not solution:
                print(f"❌ NopeCHA failed to solve captcha")
                return False
            
            print(f"✅ Captcha solved! Waiting 5 seconds before sending DM...")
            await asyncio.sleep(5)
            
            # Use API directly with captcha token
            api = DiscordAPI(token)
            
            # Create DM channel
            success, data = api.create_dm_channel(str(member.id))
            if not success:
                print(f"❌ Failed to create DM: {data}")
                return False
            
            channel_id = data['id']
            
            # Send message with captcha key
            success, data = api.send_message(channel_id, self.message, solution)
            
            if success:
                print(f"✅ DM sent to {member.name} with captcha!")
                self.dm_count += 1
                return True
            else:
                print(f"❌ Failed to send with captcha: {data}")
                return False
                
        except Exception as e:
            print(f"❌ Captcha solve error: {e}")
            return False
    
    async def process_member(self, member, token: str) -> None:
        """Process a single member"""
        member_id = str(member.id)
        
        # Skip if already processed
        if self.is_member_processed(member_id):
            return
        
        # Skip bots
        if member.bot:
            print(f"🤖 Skipping bot: {member.name}")
            return
        
        # Skip self
        if member.id == self.client.user.id:
            print(f"⏭️ Skipping self")
            self.mark_member_processed(member_id)
            return
        
        print(f"👤 Processing: {member.name} ({member_id})")
        
        # Send DM
        success = await self.send_dm(member, token)
        
        # Mark as processed regardless
        self.mark_member_processed(member_id)
        
        if success:
            print(f"✅ Done: {member.name}")
        else:
            print(f"❌ Failed: {member.name}")
        
        await asyncio.sleep(3)
    
    async def scan_server(self, token: str) -> None:
        """Scan server for new members"""
        guild = self.client.get_guild(int(self.server_id))
        if not guild:
            print(f"❌ Not in server! Join manually first.")
            return
        
        print(f"📡 Scanning: {guild.name} ({len(guild.members)} members)")
        
        # Load processed members
        self.processed_members = self.config_manager.get_processed_members(self.server_id)
        
        for member in guild.members:
            member_id = str(member.id)
            
            if self.is_member_processed(member_id):
                continue
            
            if member.bot:
                continue
            
            if member.id == self.client.user.id:
                continue
            
            if member.joined_at:
                time_diff = datetime.utcnow() - member.joined_at.replace(tzinfo=None)
                if time_diff.total_seconds() < 300:  # Last 5 minutes
                    await self.process_member(member, token)
                    await asyncio.sleep(5)  # Longer delay between members
    
    async def monitor_loop(self) -> None:
        """Main monitoring loop"""
        print("🔄 Starting monitoring loop...")
        print("💡 Checking for new members every 30 seconds")
        print("⏳ Captcha will wait up to 180 seconds to solve")
        print("=" * 60)
        
        while self.running:
            try:
                # Get next token
                token = self.token_manager.get_next_token()
                if not token:
                    print("⚠️ No available tokens! Waiting 60 seconds...")
                    await asyncio.sleep(60)
                    continue
                
                # Scan server
                await self.scan_server(token)
                
                # Wait before next scan
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"⚠️ Error in monitor loop: {e}")
                await asyncio.sleep(60)
    
    def run(self) -> None:
        """Run the bot"""
        # For discord.py-self, no intents needed
        self.client = discord.Client()
        
        @self.client.event
        async def on_ready():
            print("=" * 60)
            print(f"✅ LOGGED IN: {self.client.user.name}")
            print(f"📱 User ID: {self.client.user.id}")
            print("=" * 60)
            
            # Check if in server
            guild = self.client.get_guild(int(self.server_id))
            if guild:
                print(f"✅ In server: {guild.name}")
            else:
                print(f"❌ NOT in server!")
                if self.invite_link:
                    print(f"🔗 Join manually: {self.invite_link}")
                print("=" * 60)
                return
            
            # Start monitoring
            await self.monitor_loop()
        
        @self.client.event
        async def on_member_join(member):
            if str(member.guild.id) == self.server_id:
                print(f"🔔 NEW MEMBER: {member.name}")
                token = self.token_manager.get_next_token()
                if token:
                    await self.process_member(member, token)
        
        @self.client.event
        async def on_error(event, *args, **kwargs):
            print(f"❌ Error event: {event}")
        
        print("🚀 Starting Discord client...")
        
        try:
            # Get first token
            token = self.token_manager.get_next_token()
            if not token:
                print("❌ No valid tokens found!")
                return
            
            self.client.run(token)
            
        except discord.LoginFailure:
            print("❌ Invalid token!")
        except Exception as e:
            print(f"❌ Fatal error: {e}")

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    try:
        snitcher = AutoSnitcher('config.json')
        snitcher.run()
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⚠️ Bot stopped by user")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Fatal error: {e}")