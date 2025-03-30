#ifndef DFAT_DATA_STRUCTURES_H
#define DFAT_DATA_STRUCTURES_H

#include <string>
#include <vector>
#include "disklib/Disk.h"

// Block size is 512 bytes
#define BLOCK_SIZE 512

// Define enums for FAT and Directory Entry types
enum fat_entry_type {
    DISK_LABEL = 0x0000,
    FAT_BLOCK = 0x0001,
    IN_USE = 0xfefe,
    UNALLOCATED = 0xffff,
};

enum dir_entry_type {
    UNUSED_ENTRY = 0x0000,
    DIR_ENTRY = 0x0002,
    FILE_CHUNK = 0x0003,
};

// Directory Listing structure
struct dir_listing {
    unsigned short type;   // Directory entry type
    unsigned short block;  // Block where file/directory is stored
    unsigned int metadata; // File size or metadata
    char name[24];         // Name of the file or directory
};

// Disk Label structure
struct disk_label {
    char label[BLOCK_SIZE]; // Disk label (max 512 bytes)
};

// FAT Table structure
struct fat {
    unsigned short table[BLOCK_SIZE / 2]; // Array of FAT entries
};

// Directory Entry structure
struct dir_entry {
    struct dir_listing list[BLOCK_SIZE / sizeof(dir_listing)]; // Directory listings
};

// File Chunk structure
struct file_chunk {
    char data[BLOCK_SIZE]; // File data block (max 512 bytes)
};

// Union for different block types
union block {
    struct disk_label disk_label;  // Disk label block
    struct fat fat;                // FAT block
    struct dir_entry dir_entry;    // Directory entry block
    struct file_chunk file_chunk;  // File chunk block
};

// dFAT File System Class
class dFAT_FileSystem {
public:
    fat fat_table;           // FAT table (stores block allocation info)
    dir_entry root_directory;  // Root directory
    disk_label disk_label;      // Disk label
    std::string current_path;   // Current directory path

    dFAT_FileSystem();  // Constructor

    bool loadFileSystem(Disk& disk);  // Load file system from disk
    std::string getDiskLabel();  // Get the disk label
    void listDirectory();  // List the current directory contents
    void changeDirectory(const std::string& dir);  // Change current directory
    std::string getCurrentPath();  // Get the current directory path
    void readFile(const std::string& file);  // Read a file
};

#endif // DFAT_DATA_STRUCTURES_H
