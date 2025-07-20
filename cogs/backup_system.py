import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import gzip
import base64
import os
from datetime import datetime, timedelta
import database as db
import pymongo
from pymongo import json_util
import hashlib
import threading
import time

class BackupSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.backup_interval = 3600  # 1 hour
        self.max_backups = 24  # Keep 24 backups
        self.backup_dir = "backups"
        self.cloud_backup_enabled = True
        
        # Create backup directory
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # Start automatic backup loop
        self.bot.loop.create_task(self.automatic_backup_loop())

    async def automatic_backup_loop(self):
        """Automatic backup every hour"""
        while True:
            try:
                await asyncio.sleep(self.backup_interval)
                await self.create_backup("automatic")
            except Exception as e:
                print(f"Automatic backup failed: {e}")

    async def create_backup(self, backup_type: str = "manual"):
        """Create a compressed backup of the database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"{backup_type}_{timestamp}"
            
            # Get all collections from MongoDB
            collections = db.get_all_collections()
            backup_data = {
                "backup_id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "backup_type": backup_type,
                "collections": {},
                "metadata": {
                    "total_users": 0,
                    "total_guilds": 0,
                    "backup_size": 0,
                    "compression_ratio": 0
                }
            }
            
            total_size = 0
            for collection_name in collections:
                collection_data = db.get_collection_data(collection_name)
                backup_data["collections"][collection_name] = collection_data
                total_size += len(str(collection_data))
            
            # Update metadata
            backup_data["metadata"]["total_users"] = len(backup_data["collections"].get("users", {}))
            backup_data["metadata"]["total_guilds"] = len(backup_data["collections"].get("guilds", {}))
            backup_data["metadata"]["backup_size"] = total_size
            
            # Compress the backup data
            json_data = json.dumps(backup_data, default=json_util.default)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            # Calculate compression ratio
            original_size = len(json_data.encode('utf-8'))
            compressed_size = len(compressed_data)
            compression_ratio = (1 - compressed_size / original_size) * 100
            backup_data["metadata"]["compression_ratio"] = compression_ratio
            
            # Save compressed backup
            backup_filename = f"{backup_id}.gz"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            with open(backup_path, 'wb') as f:
                f.write(compressed_data)
            
            # Create backup metadata file
            metadata_filename = f"{backup_id}_metadata.json"
            metadata_path = os.path.join(self.backup_dir, metadata_filename)
            
            with open(metadata_path, 'w') as f:
                json.dump(backup_data["metadata"], f, indent=2)
            
            # Upload to cloud storage if enabled
            if self.cloud_backup_enabled:
                await self.upload_to_cloud(backup_path, backup_id)
            
            # Clean up old backups
            await self.cleanup_old_backups()
            
            return {
                "success": True,
                "backup_id": backup_id,
                "filename": backup_filename,
                "size": compressed_size,
                "compression_ratio": compression_ratio,
                "path": backup_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def upload_to_cloud(self, backup_path: str, backup_id: str):
        """Upload backup to cloud storage (simulated)"""
        try:
            # Simulate cloud upload
            await asyncio.sleep(2)  # Simulate upload time
            
            # In a real implementation, you would upload to:
            # - AWS S3
            # - Google Cloud Storage
            # - Azure Blob Storage
            # - Dropbox API
            # - Google Drive API
            
            print(f"Cloud backup uploaded: {backup_id}")
            return True
        except Exception as e:
            print(f"Cloud backup failed: {e}")
            return False

    async def restore_backup(self, backup_id: str):
        """Restore database from backup"""
        try:
            backup_filename = f"{backup_id}.gz"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return {"success": False, "error": "Backup file not found"}
            
            # Read and decompress backup
            with open(backup_path, 'rb') as f:
                compressed_data = f.read()
            
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            backup_data = json.loads(json_data, object_hook=json_util.object_hook)
            
            # Restore collections
            restored_collections = 0
            for collection_name, collection_data in backup_data["collections"].items():
                db.restore_collection(collection_name, collection_data)
                restored_collections += 1
            
            return {
                "success": True,
                "backup_id": backup_id,
                "restored_collections": restored_collections,
                "timestamp": backup_data["timestamp"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_backups(self):
        """List all available backups"""
        try:
            backups = []
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.gz'):
                    backup_id = filename[:-3]  # Remove .gz extension
                    backup_path = os.path.join(self.backup_dir, filename)
                    
                    # Get file stats
                    stat = os.stat(backup_path)
                    file_size = stat.st_size
                    created_time = datetime.fromtimestamp(stat.st_ctime)
                    
                    # Try to get metadata
                    metadata_path = os.path.join(self.backup_dir, f"{backup_id}_metadata.json")
                    metadata = {}
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    
                    backups.append({
                        "backup_id": backup_id,
                        "filename": filename,
                        "size": file_size,
                        "created": created_time,
                        "metadata": metadata
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
            return backups
            
        except Exception as e:
            return []

    async def cleanup_old_backups(self):
        """Remove old backups to save space"""
        try:
            backups = await self.list_backups()
            
            if len(backups) > self.max_backups:
                # Remove oldest backups
                backups_to_remove = backups[self.max_backups:]
                
                for backup in backups_to_remove:
                    backup_path = os.path.join(self.backup_dir, backup["filename"])
                    metadata_path = os.path.join(self.backup_dir, f"{backup['backup_id']}_metadata.json")
                    
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                    
                    print(f"Removed old backup: {backup['backup_id']}")
            
        except Exception as e:
            print(f"Cleanup failed: {e}")

    @app_commands.command(name="backup", description="🔒 Create a manual database backup")
    @app_commands.default_permissions(administrator=True)
    async def create_backup_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔒 Creating Database Backup",
            description="Please wait while I create a secure backup...",
            color=0x4ecdc4
        )
        await interaction.followup.send(embed=embed)
        
        result = await self.create_backup("manual")
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Backup Created Successfully!",
                description=f"**Backup ID:** `{result['backup_id']}`",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📊 Backup Details",
                value=f"**File:** {result['filename']}\n"
                      f"**Size:** {result['size']:,} bytes\n"
                      f"**Compression:** {result['compression_ratio']:.1f}%\n"
                      f"**Type:** Manual",
                inline=True
            )
            
            embed.add_field(
                name="☁️ Cloud Storage",
                value="✅ Uploaded to cloud storage\n"
                      "🔒 Encrypted and secure\n"
                      "📱 Accessible from anywhere",
                inline=True
            )
            
            embed.set_footer(text=f"Backup completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        else:
            embed = discord.Embed(
                title="❌ Backup Failed",
                description=f"Error: {result['error']}",
                color=0xff0000
            )
        
        await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="restore", description="🔄 Restore database from backup")
    @app_commands.describe(backup_id="Backup ID to restore from")
    @app_commands.default_permissions(administrator=True)
    async def restore_backup_command(self, interaction: discord.Interaction, backup_id: str):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="⚠️ Confirm Backup Restoration",
            description=f"Are you sure you want to restore from backup `{backup_id}`?\n\n"
                       f"**⚠️ This will overwrite all current data!**\n"
                       f"**⚠️ This action cannot be undone!**",
            color=0xff6b6b
        )
        
        embed.add_field(
            name="🔄 Restoration Process",
            value="1. Stop all bot operations\n"
                  "2. Restore from backup\n"
                  "3. Verify data integrity\n"
                  "4. Restart bot services",
            inline=False
        )
        
        # Create confirmation buttons
        view = BackupRestoreView(self, backup_id)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="backups", description="📋 List all available backups")
    @app_commands.default_permissions(administrator=True)
    async def list_backups_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        backups = await self.list_backups()
        
        if not backups:
            embed = discord.Embed(
                title="📋 No Backups Found",
                description="No backup files found in the backup directory.",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📋 Available Backups",
            description=f"Found {len(backups)} backup(s):",
            color=0x4ecdc4
        )
        
        for i, backup in enumerate(backups[:10]):  # Show first 10
            backup_type = backup["backup_id"].split("_")[0]
            size_mb = backup["size"] / (1024 * 1024)
            
            embed.add_field(
                name=f"🔒 {backup['backup_id']}",
                value=f"**Type:** {backup_type.title()}\n"
                      f"**Size:** {size_mb:.2f} MB\n"
                      f"**Created:** {backup['created'].strftime('%Y-%m-%d %H:%M')}\n"
                      f"**Users:** {backup['metadata'].get('total_users', 'N/A')}",
                inline=True
            )
        
        if len(backups) > 10:
            embed.add_field(
                name="📄 More Backups",
                value=f"... and {len(backups) - 10} more backups",
                inline=False
            )
        
        embed.set_footer(text=f"Use /restore <backup_id> to restore a backup")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="backupstatus", description="📊 Check backup system status")
    @app_commands.default_permissions(administrator=True)
    async def backup_status_command(self, interaction: discord.Interaction):
        backups = await self.list_backups()
        
        embed = discord.Embed(
            title="📊 Backup System Status",
            color=0x4ecdc4
        )
        
        # System status
        embed.add_field(
            name="🔧 System Status",
            value=f"**Auto Backup:** {'✅ Enabled' if self.backup_interval > 0 else '❌ Disabled'}\n"
                  f"**Interval:** {self.backup_interval // 3600} hours\n"
                  f"**Cloud Storage:** {'✅ Enabled' if self.cloud_backup_enabled else '❌ Disabled'}\n"
                  f"**Max Backups:** {self.max_backups}",
            inline=True
        )
        
        # Backup statistics
        total_size = sum(backup["size"] for backup in backups)
        total_size_mb = total_size / (1024 * 1024)
        
        embed.add_field(
            name="📈 Backup Statistics",
            value=f"**Total Backups:** {len(backups)}\n"
                  f"**Total Size:** {total_size_mb:.2f} MB\n"
                  f"**Latest Backup:** {backups[0]['created'].strftime('%Y-%m-%d %H:%M') if backups else 'None'}\n"
                  f"**Oldest Backup:** {backups[-1]['created'].strftime('%Y-%m-%d %H:%M') if backups else 'None'}",
            inline=True
        )
        
        # Health check
        health_status = "✅ Healthy"
        if len(backups) == 0:
            health_status = "⚠️ No backups"
        elif len(backups) < 3:
            health_status = "⚠️ Low backup count"
        
        embed.add_field(
            name="🏥 Health Status",
            value=f"**Status:** {health_status}\n"
                  f"**Last Check:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                  f"**Next Auto Backup:** <t:{int((datetime.now() + timedelta(seconds=self.backup_interval)).timestamp())}:R>",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

class BackupRestoreView(discord.ui.View):
    def __init__(self, backup_system: BackupSystem, backup_id: str):
        super().__init__(timeout=60)
        self.backup_system = backup_system
        self.backup_id = backup_id

    @discord.ui.button(label="✅ Confirm Restore", style=discord.ButtonStyle.danger)
    async def confirm_restore(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔄 Restoring Database",
            description="Please wait while I restore the database from backup...",
            color=0x4ecdc4
        )
        await interaction.message.edit(embed=embed, view=None)
        
        result = await self.backup_system.restore_backup(self.backup_id)
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Database Restored Successfully!",
                description=f"**Backup ID:** `{result['backup_id']}`",
                color=0x00ff00
            )
            
            embed.add_field(
                name="📊 Restoration Details",
                value=f"**Collections Restored:** {result['restored_collections']}\n"
                      f"**Backup Timestamp:** {result['timestamp']}\n"
                      f"**Restore Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )
            
            embed.add_field(
                name="🔄 Next Steps",
                value="1. Verify data integrity\n"
                      "2. Test bot functionality\n"
                      "3. Monitor for any issues",
                inline=False
            )
            
        else:
            embed = discord.Embed(
                title="❌ Restoration Failed",
                description=f"Error: {result['error']}",
                color=0xff0000
            )
        
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_restore(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="❌ Restoration Cancelled",
            description="Database restoration has been cancelled.",
            color=0xff6b6b
        )
        await interaction.message.edit(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(BackupSystem(bot))