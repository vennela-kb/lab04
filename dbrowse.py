from disklib.Disk import Disk
import struct

class DiskBrowser:
    def __init__(self, disk_image):
        self.disk = Disk(disk_image, 512)  # Initialize with block size 512
        self.current_directory = "/"  # Start at root
        self.filesystem = {}  # In-memory representation of filesystem
        self.load_filesystem()

    def load_filesystem(self):
        """Load filesystem metadata from disk image."""
        try:
            # Read the first block which contains filesystem metadata
            metadata = self.disk.readBlock(0)
            
            # Initialize root directory
            self.filesystem = {
                "/": {"type": "dir", "children": {}}
            }
            
            # Read FAT table (usually starts from block 1)
            fat_block = 1
            while True:
                try:
                    block = self.disk.readBlock(fat_block)
                    if not block:  # Empty block, stop reading
                        break
                        
                    # Parse each entry in the FAT table
                    offset = 0
                    while offset < len(block):
                        # Extract filename (11 bytes for 8.3 format)
                        filename = block[offset:offset+11].strip(b'\x00').decode('utf-8', errors='ignore')
                        if not filename:  # Empty filename, break
                            break
                            
                        # Extract attributes (1 byte)
                        attributes = block[offset+11]
                        
                        # Extract first cluster number (2 bytes)
                        first_cluster = struct.unpack('>H', block[offset+26:offset+28])[0]
                        
                        # Extract file size (4 bytes)
                        file_size = struct.unpack('>I', block[offset+28:offset+32])[0]
                        
                        # Clean up filename (remove special characters)
                        filename = ''.join(c for c in filename if c.isalnum() or c in ' ._-')
                        filename = filename.strip()
                        
                        # Add to filesystem structure
                        if attributes & 0x10:  # Directory attribute
                            # Remove trailing slash if present
                            filename = filename.rstrip('/')
                            if filename and filename not in ['.', '..']:
                                self.filesystem[f"/{filename}"] = {
                                    "type": "dir",
                                    "children": {},
                                    "cluster": first_cluster
                                }
                                self.filesystem["/"]["children"][filename] = self.filesystem[f"/{filename}"]
                        else:  # Regular file
                            if filename and filename not in ['.', '..']:
                                self.filesystem[f"/{filename}"] = {
                                    "type": "file",
                                    "cluster": first_cluster,
                                    "size": file_size
                                }
                                self.filesystem["/"]["children"][filename] = self.filesystem[f"/{filename}"]
                        
                        offset += 32  # Move to next entry (32 bytes per entry)
                        
                    fat_block += 1
                except Exception as e:
                    print(f"⚠️ Warning reading block {fat_block}: {e}")
                    break
            
            print(f"💾 Disk image loaded successfully. Found {len(self.filesystem['/']['children'])} items.")
        except Exception as e:
            print(f"❌ Error loading disk image: {e}")

    def list_files(self, path=None):
        """List files in the current directory."""
        if path is None:
            path = self.current_directory
            
        try:
            current_dir = self.get_directory(path)
            if current_dir is None:
                print(f"❌ Directory '{path}' not found")
                return
                
            print(f"\n📂 Contents of {path}:")
            for name, info in current_dir["children"].items():
                if info["type"] == "dir":
                    print(f"📁 {name}/")
                else:
                    print(f"📄 {name}")
        except Exception as e:
            print(f"❌ Error listing files: {e}")

    def get_directory(self, path):
        """Get directory information from path."""
        if path not in self.filesystem:
            return None
        return self.filesystem[path]

    def change_directory(self, new_directory):
        """Change current working directory."""
        if new_directory == "..":
            # Move up one directory
            if self.current_directory != "/":
                self.current_directory = "/".join(self.current_directory.split("/")[:-1])
                if not self.current_directory:
                    self.current_directory = "/"
        else:
            # Move to new directory
            new_path = "/".join([self.current_directory, new_directory])
            if self.get_directory(new_path):
                self.current_directory = new_path
            else:
                print(f"❌ Directory '{new_directory}' not found.")

    def read_file(self, filename):
        """Read a file from the disk image."""
        file_path = "/".join([self.current_directory, filename])
        
        try:
            file_info = self.filesystem.get(file_path)
            if not file_info or file_info["type"] != "file":
                print(f"❌ File '{filename}' not found.")
                return
                
            # Read file contents using cluster chain
            cluster = file_info["cluster"]
            size = file_info["size"]
            content = b""
            
            while size > 0:
                # Read the block containing this cluster
                block = self.disk.readBlock(cluster)
                if not block:
                    break
                    
                # Add to content
                content += block[:min(size, 512)]
                size -= 512
                
                # Get next cluster from FAT table
                cluster = self.read_fat_entry(cluster)
                if cluster == 0xFFFF:  # End of chain
                    break
            
            print(f"\n📄 Content of {filename}:")
            print(content.decode('utf-8', errors='ignore'))
        except Exception as e:
            print(f"❌ Error reading file: {e}")

    def read_fat_entry(self, cluster):
        """Read the next cluster number from FAT table."""
        try:
            # FAT table is usually in block 1
            fat_block = 1
            fat_entry = cluster * 2  # Each entry is 2 bytes
            
            # Calculate block and offset
            block_offset = fat_entry // 512
            entry_offset = (fat_entry % 512) * 2
            
            # Read the FAT entry
            fat_block_data = self.disk.readBlock(fat_block + block_offset)
            next_cluster = struct.unpack('>H', fat_block_data[entry_offset:entry_offset+2])[0]
            
            return next_cluster
        except Exception as e:
            print(f"❌ Error reading FAT entry: {e}")
            return 0xFFFF

    def show_current_directory(self):
        """Display the current working directory."""
        print(f"\n📍 Current Directory: {self.current_directory}")

    def show_help(self):
        """Display available commands."""
        print("\n📜 Available Commands:")
        print("  dir          → List files in current directory")
        print("  pwd          → Show current directory")
        print("  read <file>  → Read a file")
        print("  cd <dir>     → Change directory")
        print("  help         → Show available commands")
        print("  exit         → Exit the browser")

    def show_statistics(self):
        """Show disk usage statistics."""
        self.disk.printStats()

# Initialize the disk browser
disk_browser = DiskBrowser("disk.img")

# Interactive Command Loop
print("Welcome to DBrowse - A dFAT Filesystem Browser")
print("Type 'help' for available commands")

while True:
    command = input("\ndbrowse> ").strip().lower()
    
    if command == "exit":
        print("👋 Exiting DBrowse.")
        disk_browser.show_statistics()  # Show disk usage stats on exit
        break
    elif command == "dir":
        disk_browser.list_files()
    elif command == "pwd":
        disk_browser.show_current_directory()
    elif command.startswith("cd "):
        # Extract directory name (remove trailing slash if present)
        new_dir = command[3:].strip().rstrip("/")
        disk_browser.change_directory(new_dir)
    elif command.startswith("read "):
        filename = command[5:].strip()
        disk_browser.read_file(filename)
    elif command == "help":
        disk_browser.show_help()
    else:
        print("❌ Unknown command. Use 'help' to see available commands.")
